import asyncio
import sys
import os
import uuid
import json
import logging

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config.settings import settings
from pydantic import BaseModel, EmailStr
from backend.services.mail_service import EmailService
from backend.graphs.workflow import app_workflow
from backend.schemas.campaign import UserInput, CampaignResponse
from backend.graphs.state import AgentState
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

from backend.services.neon_db import (
    get_all_campaigns, 
    get_campaign_details, 
    update_decision_maker_email, 
    reject_decision_maker,
    update_campaign_status,
    delete_campaign,
    update_email_draft,
    mark_email_sent,
    get_db_connection,
    save_sent_discovery_email,
    create_campaign as db_create_campaign
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Agentic B2B System...")
    logger.info(f"Current Event Loop: {asyncio.get_event_loop().__class__.__name__}")
    logger.info(f"Current Policy: {asyncio.get_event_loop_policy().__class__.__name__}")
    
    # 1. Start Background Workers (Optional Bundle Mode)
    if os.environ.get("BUNDLE_WORKERS") == "true" or os.environ.get("RENDER"):
        from backend.background_workers.email_ingestion import EmailIngestionService
        from backend.background_workers.orchestrator_worker import MonitoringOrchestrator
        from backend.background_workers.timer_engine import TimerEngine
        
        ingestion = EmailIngestionService()
        orchestrator = MonitoringOrchestrator()
        timer = TimerEngine()
        
        # Fire and forget tasks
        asyncio.create_task(ingestion.run())
        asyncio.create_task(orchestrator.run())
        asyncio.create_task(timer.run())
        
        logger.info("Autonomous workers bundled and initialized in background process.")
    
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title="Agentic B2B Outbound Sales Automation System",
    description="API for managing outbound sales campaigns using multi-agent system",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmailRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    body: str # HTML or Text
    recipient_name: str = None

class InitialCampaignRequest(BaseModel):
    name: str

class UpdateEmailRequest(BaseModel):
    subject: str
    body: str
    recipient: str = None

class StatusUpdate(BaseModel):
    status: str

class DiscoverySendRequest(BaseModel):
    subject: str
    body: str

@app.get("/")
async def root():
    return {"message": "Agentic B2B Outbound Sales Automation System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/campaigns/initialize")
async def initialize_campaign(req: InitialCampaignRequest):
    campaign_id = await db_create_campaign(req.name, "")
    if campaign_id:
        return {"campaign_id": campaign_id, "name": req.name}
    else:
        return {"error": "Failed to create campaign"}

@app.patch("/emails/{email_id}")
async def patch_email(email_id: str, req: UpdateEmailRequest):
    success = await update_email_draft(email_id, req.subject, req.body, req.recipient)
    if success:
        return {"status": "success"}
    return {"error": "Failed to update email draft"}

@app.get("/campaigns")
async def list_campaigns():
    campaigns = await get_all_campaigns()
    return {"campaigns": campaigns}

@app.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    details = await get_campaign_details(campaign_id)
    if not details:
        return {"error": "Campaign not found"}
    return details

@app.patch("/campaigns/{campaign_id}/status")
async def update_status(campaign_id: str, req: StatusUpdate):
    success = await update_campaign_status(campaign_id, req.status)
    if success:
        return {"status": "success"}
    return {"error": "Failed to update campaign status"}

@app.get("/events/{entity_id}")
async def fetch_events(entity_id: str):
    from backend.services.neon_db import get_event_logs
    events = await get_event_logs(entity_id)
    return {"events": events}

@app.delete("/campaigns/{campaign_id}")
async def remove_campaign(campaign_id: str):
    success = await delete_campaign(campaign_id)
    if success:
        return {"status": "success"}
    return {"error": "Failed to delete campaign"}

@app.post("/campaigns/{campaign_id}/launch", response_model=CampaignResponse)
async def launch_campaign(campaign_id: str, req: UserInput):
    initial_state = AgentState(
        user_input=req.query,
        campaign_id=campaign_id,
        campaign_data=None,
        target_companies=[],
        decision_makers=[],
        email_drafts=[],
        validation_status="pending",
        errors=[],
        current_agent="start"
    )
    
    result = await app_workflow.ainvoke(initial_state)
    
    # Update Status in DB to trigger Monitoring Phase in UI
    await update_campaign_status(campaign_id, "MONITORING_ACTIVE")
    
    if result["errors"]:
        print(f"Workflow errors: {result['errors']}")
        
    return CampaignResponse(
        campaign_id=result.get("campaign_id", campaign_id),
        status="MONITORING_ACTIVE",
        campaign=result["campaign_data"],
        target_companies=result.get("target_companies", []),
        decision_makers=result.get("decision_makers", []),
        email_draft_ids=[], # Deprecated in favor of emails service
        email_drafts=result.get("email_drafts", []),
        scheduled_emails=result.get("scheduled_emails", [])
    )

@app.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(input_data: UserInput):
    initial_state = AgentState(
        user_input=input_data.query,
        campaign_data=None,
        target_companies=[],
        decision_makers=[],
        email_drafts=[],
        validation_status="pending",
        errors=[],
        current_agent="start"
    )
    
    result = await app_workflow.ainvoke(initial_state)
    
    if result["errors"]:
        print(f"Workflow errors: {result['errors']}")
        
    return CampaignResponse(
        campaign_id=result.get("campaign_id", "failed-to-save"),
        status="planned",
        campaign=result["campaign_data"],
        target_companies=result.get("target_companies", []),
        decision_makers=result.get("decision_makers", []),
        email_drafts=result.get("email_drafts", []),
        scheduled_emails=result.get("scheduled_emails", [])
    )

@app.post("/send-email")
async def send_email_endpoint(email_req: EmailRequest):
    success = await EmailService.send_email(
        to_email=email_req.recipient_email,
        subject=email_req.subject,
        body=email_req.body, # sending as is
        to_name=email_req.recipient_name
    )
    
    if success:
        return {"status": "success", "message": "Email sent successfully"}
    else:
        return {"status": "error", "message": "Failed to send email. Check logs/credentials."}

@app.post("/emails/{email_id}/approve")
async def approve_email(email_id: str):
    from backend.services.neon_db import get_campaign_details_by_email_id
    details = await get_campaign_details_by_email_id(email_id) 
    if not details:
        return {"error": "Email not found"}
    
    email = details['email']
    dm = details['dm']
    
    success = await EmailService.send_email(
        to_email=email['recipient'] or dm['email'],
        subject=email['subject'],
        body=email['body'],
        to_name=dm['name']
    )
    
    if success:
        await mark_email_sent(email_id)
        return {"status": "success"}
    return {"error": "Failed to send email"}

@app.post("/emails/{email_id}/decline")
async def decline_email(email_id: str):
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE emails SET status = 'declined' WHERE id = %s", (email_id,))
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        await conn.close()

@app.post("/campaigns/{campaign_id}/batch-send")
async def batch_send(campaign_id: str):
    details = await get_campaign_details(campaign_id)
    if not details:
        return {"error": "Campaign not found"}
    
    drafts = [e for e in details['emails'] if e['status'] == 'PENDING_APPROVAL']
    sent_count = 0
    
    for email in drafts:
        dm = next((d for d in details['decision_makers'] if d['id'] == email['decision_maker_id']), None)
        if not dm: continue
        
        success = await EmailService.send_email(
            to_email=email['recipient'] or dm['email'],
            subject=email['subject'],
            body=email['body'],
            to_name=dm['name']
        )
        
        if success:
            await mark_email_sent(str(email['id']))
            sent_count += 1
            
    return {"status": "success", "sent": sent_count}

@app.post("/decision-makers/{dm_id}/send-discovery")
async def send_discovery_email(dm_id: str, req: DiscoverySendRequest):
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT name, email FROM decision_makers WHERE id = %s", (dm_id,))
                dm = await cur.fetchone()
                if not dm:
                    return {"error": "Decision maker not found"}
                
                success = await EmailService.send_email(
                    to_email=dm['email'],
                    subject=req.subject,
                    body=req.body,
                    to_name=dm['name']
                )
                
                if success:
                    db_success = await save_sent_discovery_email(dm_id, req.subject, req.body, dm['email'])
                    if db_success:
                        return {"status": "success"}
                    return {"error": "Email sent but failed to update database"}
                return {"error": "Failed to send email"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        await conn.close()

@app.patch("/decision-makers/{dm_id}")
async def patch_dm(dm_id: str, req: dict):
    # For updating DM info like email
    success = await update_decision_maker_email(dm_id, req.get('email'))
    if success:
        return {"status": "success"}
    return {"error": "Failed to update decision maker"}
