import time
from backend.graphs.workflow import app_workflow as app
from backend.services.neon_db import create_campaign, get_db_connection
from backend.schemas.campaign import Campaign, CampaignFilters
from backend.services.mail_service import EmailService
from backend.config.settings import settings
import uuid

def run_e2e_test():
    print("=== Starting E2E Collaborative Grand Test ===")
    
    # 1. Initialize State
    # We will let the orchestrator create its own campaign for true E2E
    # campaign_id = create_campaign(name="E2E Prod Readiness", product_description="AI Lead Gen SaaS")
    
    filters = CampaignFilters(
        industries=["Fintech"],
        locations=["London"],
        roles=["Marketing Manager"]
    )
    
    campaign = Campaign(
        name="E2E Prod Readiness v2",
        user_company_name="DigiotAI Solutions",
        product_description="AI Lead Gen SaaS for Fintech",
        target_filters=filters
    )
    
    initial_state = {
        "user_input": "Find people in fintech in London",
        "campaign_data": campaign,
        "campaign_id": None, # Let it be created
        "target_companies": [],
        "decision_makers": [],
        "email_drafts": [],
        "validation_status": "pending",
        "errors": [],
        "current_agent": ""
    }
    
    # 2. Run LangGraph Workflow
    print("\n[Step 1/3] Running Agent Workflow...")
    result = app.invoke(initial_state)
    
    if result["errors"]:
        print(f"Workflow finished with errors: {result['errors']}")
    
    campaign_id = result.get("campaign_id")
    print(f"Workflow completed! Campaign ID: {campaign_id}")
    print(f"Found {len(result['target_companies'])} companies and {len(result['decision_makers'])} people.")
    
    # 3. Simulate Outreach to Target
    print(f"\n[Step 2/3] Injecting Target Prospect: {settings.TARGET_EMAIL}")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get a company_id from search results to link to
    if result["target_companies"]:
        target_company_name = result["target_companies"][0].name
        # Flexible lookup: just get the first company for this campaign if name fails
        cur.execute("SELECT id FROM target_companies WHERE campaign_id = %s LIMIT 1", (campaign_id,))
        row = cur.fetchone()
        if row:
            company_id = row['id']
        else:
            campaign_id = str(uuid.uuid4()) # dummy
            company_id = str(uuid.uuid4())
    else:
        company_id = str(uuid.uuid4())
    
    # Insert the "Target" prospect
    dm_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO decision_makers (id, campaign_id, company_id, name, role, email, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (dm_id, campaign_id, company_id, "Test Prospect", "Manager", settings.TARGET_EMAIL, "new"))
    conn.commit()
    
    # 4. Send Email
    print(f"Sending real email to {settings.TARGET_EMAIL}...")
    success = EmailService.send_email(
        to_email=settings.TARGET_EMAIL,
        subject="Production Readiness Test: Conversation Loop",
        body="Hi, we are checking our systems. Could you please let us know if you are interested in a demo?",
        to_name="Test Prospect"
    )
    
    if success:
        print("Email sent successfully!")
        print(f"\n[Step 3/3] Monitoring for Reply...")
        print("Now run 'python -m tests.simulate_prospect' and then check back here.")
    else:
        print("Failed to send email.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    run_e2e_test()
