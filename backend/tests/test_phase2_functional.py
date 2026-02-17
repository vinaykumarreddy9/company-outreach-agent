import asyncio
import sys
import uuid
import json
import logging
from datetime import datetime, timedelta, timezone
import psycopg
from backend.config.settings import settings
from backend.services.neon_db import get_db_connection, mark_email_sent, log_event
from backend.background_workers.orchestrator_worker import MonitoringOrchestrator
from backend.background_workers.timer_engine import TimerEngine

# Windows Fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Phase2Test")

async def run_tests():
    logger.info("Starting Phase-2 Functional Testing...")
    
    # Setup test entities
    campaign_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    dm_id = str(uuid.uuid4())
    
    conn = await psycopg.AsyncConnection.connect(settings.NEON_DB_URL)
    async with conn:
        async with conn.cursor() as cur:
            # 1. CLEANUP PREVIOUS TESTS (Optional but good)
            await cur.execute("DELETE FROM event_log WHERE entity_id IN (%s, %s, %s)", (campaign_id, company_id, dm_id))
            
            # 2. CREATE MOCK CAMPAIGN (DRAFT)
            logger.info("--- Testing Activation Rule ---")
            await cur.execute("""
                INSERT INTO campaigns (id, name, status) 
                VALUES (%s, 'Test Phase 2', 'MONITORING_READY')
            """, (campaign_id,))
            
            await cur.execute("""
                INSERT INTO target_companies (id, campaign_id, name, status) 
                VALUES (%s, %s, 'Test Corp', 'ACTIVE')
            """, (company_id, campaign_id))
            
            await cur.execute("""
                INSERT INTO decision_makers (id, campaign_id, company_id, name, email, status, turn_count) 
                VALUES (%s, %s, %s, 'Test DM', 'test@example.com', 'ACTIVE', 0)
            """, (dm_id, campaign_id, company_id))
            
            # 3. TEST: FIRST EMAIL SENT -> CAMPAIGN BECOMES MONITORING_ACTIVE
            email_id = str(uuid.uuid4())
            await cur.execute("""
                INSERT INTO emails (id, decision_maker_id, status, direction, type) 
                VALUES (%s, %s, 'PENDING_APPROVAL', 'outbound', 'initial')
            """, (email_id, dm_id))
            await conn.commit()
            
            logger.info("Marking first email as sent...")
            await mark_email_sent(email_id)
            
            await cur.execute("SELECT status FROM campaigns WHERE id = %s", (campaign_id,))
            camp = await cur.fetchone()
            logger.info(f"Campaign Status after first send: {camp[0]}")
            assert camp[0] == 'MONITORING_ACTIVE', "Campaign should be MONITORING_ACTIVE after first send"

            # 4. TEST: 11 MESSAGE LIMIT -> TERMINATION
            logger.info("--- Testing 11 Outbound Limit ---")
            # Simulate DM having 10 turns and sending the 11th now
            await cur.execute("UPDATE decision_makers SET turn_count = 10 WHERE id = %s", (dm_id,))
            email_id_11 = str(uuid.uuid4())
            await cur.execute("""
                INSERT INTO emails (id, decision_maker_id, status, direction, type) 
                VALUES (%s, %s, 'PENDING_APPROVAL', 'outbound', 'reminder')
            """, (email_id_11, dm_id))
            await conn.commit()
            
            await mark_email_sent(email_id_11)
            
            # Run Timer Engine check
            timer_engine = TimerEngine()
            await timer_engine.check_timers()
            
            await cur.execute("SELECT status FROM decision_makers WHERE id = %s", (dm_id,))
            dm_status = await cur.fetchone()
            logger.info(f"DM Status after 11 turns: {dm_status[0]}")
            assert dm_status[0] == 'TERMINATED', "DM should be TERMINATED after 11 turns"

            # 5. TEST: POSITIVE INTENT -> DISCOVERY FLOW
            logger.info("--- Testing Positive Intent Discovery ---")
            # Reset DM to Active for this test
            dm_2_id = str(uuid.uuid4())
            await cur.execute("""
                INSERT INTO decision_makers (id, campaign_id, company_id, name, email, status) 
                VALUES (%s, %s, %s, 'Positive Lead', 'lead@example.com', 'ACTIVE')
            """, (dm_2_id, campaign_id, company_id))
            
            # Mock an Inbound Email Received
            inbound_id = str(uuid.uuid4())
            await cur.execute("""
                INSERT INTO emails (id, decision_maker_id, sender, body, status, direction) 
                VALUES (%s, %s, 'lead@example.com', 'Yes, I am interested in a demo next week!', 'RECEIVED', 'inbound')
            """, (inbound_id, dm_2_id))
            
            await log_event(cur, 'EMAIL_RECEIVED', inbound_id, 'EMAIL', {"dm_id": dm_2_id})
            await conn.commit()
            
            # Run Orchestrator - Pass 1: Handle EMAIL_RECEIVED -> Emit INTENT_CLASSIFIED
            orch = MonitoringOrchestrator()
            await orch.process_events()
            
            # Run Orchestrator - Pass 2: Handle INTENT_CLASSIFIED -> DISCOVERY
            await orch.process_events()
            
            # Check DM Status
            await cur.execute("SELECT status FROM decision_makers WHERE id = %s", (dm_2_id,))
            dm_status_new = await cur.fetchone()
            logger.info(f"New DM Status after positive reply: {dm_status_new[0]}")
            
            # Check Company Status (Rule 7: One DM Discovery -> All Company Monitoring Stops)
            await cur.execute("SELECT status FROM target_companies WHERE id = %s", (company_id,))
            co_status = await cur.fetchone()
            logger.info(f"Company Status after one DM Discovery: {co_status[0]}")
            
            assert dm_status_new[0] == 'DISCOVERY', "DM should be in DISCOVERY after positive intent"
            assert co_status[0] == 'DISCOVERY', "Company should be in DISCOVERY after one DM Discovery"

            # Cleanup
            logger.info("Cleaning up test data...")
            await cur.execute("DELETE FROM event_log WHERE entity_id IN (%s, %s, %s, %s, %s, %s)", 
                            (campaign_id, company_id, dm_id, email_id, email_id_11, inbound_id))
            await cur.execute("DELETE FROM emails WHERE decision_maker_id IN (%s, %s)", (dm_id, dm_2_id))
            await cur.execute("DELETE FROM decision_makers WHERE campaign_id = %s", (campaign_id,))
            await cur.execute("DELETE FROM target_companies WHERE campaign_id = %s", (campaign_id,))
            await cur.execute("DELETE FROM campaigns WHERE id = %s", (campaign_id,))
            await conn.commit()

    logger.info("All Phase-2 Functional Tests PASSED!")

if __name__ == "__main__":
    asyncio.run(run_tests())
