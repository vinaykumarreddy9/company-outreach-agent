import asyncio
import sys
import uuid
import logging
import aiosmtplib
from email.mime.text import MIMEText
from backend.config.settings import settings
from backend.services.neon_db import get_db_connection
from backend.background_workers.email_ingestion import EmailIngestionService
import psycopg

# Windows Fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IngestionTest")

async def test_end_to_end_ingestion():
    logger.info("Starting End-to-End Email Ingestion Test...")
    
    # 1. SETUP MOCK CAMPAIGN & DM
    # The DM's email MUST be the target email we send FROM.
    from_email = settings.TARGET_EMAIL
    from_password = settings.TARGET_PASSWORD # Using target's credentials to send TO our main user
    
    campaign_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    dm_id = str(uuid.uuid4())
    
    conn = await psycopg.AsyncConnection.connect(settings.NEON_DB_URL)
    async with conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO campaigns (id, name, status) 
                VALUES (%s, 'Ingestion Test', 'MONITORING_ACTIVE')
            """, (campaign_id,))
            
            await cur.execute("""
                INSERT INTO target_companies (id, campaign_id, name, status) 
                VALUES (%s, %s, 'Ingestion Corp', 'ACTIVE')
            """, (company_id, campaign_id))
            
            await cur.execute("""
                INSERT INTO decision_makers (id, campaign_id, company_id, name, email, status) 
                VALUES (%s, %s, %s, 'Target Sender', %s, 'ACTIVE')
            """, (dm_id, campaign_id, company_id, from_email))
            await conn.commit()

    try:
        # 2. SEND TEST EMAIL (Simulating prospect reply)
        unique_id = str(uuid.uuid4())
        logger.info(f"Sending test email from {from_email} to {settings.EMAIL_USER} (ID: {unique_id})...")
        msg = MIMEText(f"This is a test reply for Phase-2 Ingestion. ID: {unique_id}")
        msg['Subject'] = f"Phase-2 Test {unique_id}"
        msg['From'] = from_email
        msg['To'] = settings.EMAIL_USER

        await aiosmtplib.send(
            msg,
            hostname=settings.EMAIL_HOST,
            port=int(settings.EMAIL_PORT),
            start_tls=True,
            username=from_email,
            password=from_password
        )
        logger.info("Test email sent. Waiting 30s for delivery...")
        await asyncio.sleep(30)

        # 3. POLL INBOX
        ingestor = EmailIngestionService()
        logger.info(f"Polling inbox for reply with subject: Phase-2 Test {unique_id}...")
        await ingestor.poll_inbox(f'SUBJECT "Phase-2 Test {unique_id}"')
        
        # 4. VERIFY DB
        async with await psycopg.AsyncConnection.connect(settings.NEON_DB_URL) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT count(*) FROM emails 
                    WHERE decision_maker_id = %s AND direction = 'inbound'
                """, (dm_id,))
                count = (await cur.fetchone())[0]
                logger.info(f"Inbound emails found for DM: {count}")
                
                assert count > 0, "No inbound email was ingested for the decision maker"

    finally:
        # 5. CLEANUP
        logger.info("Cleaning up...")
        async with await psycopg.AsyncConnection.connect(settings.NEON_DB_URL) as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM emails WHERE decision_maker_id = %s", (dm_id,))
                await cur.execute("DELETE FROM decision_makers WHERE campaign_id = %s", (campaign_id,))
                await cur.execute("DELETE FROM target_companies WHERE campaign_id = %s", (campaign_id,))
                await cur.execute("DELETE FROM campaigns WHERE id = %s", (campaign_id,))
                await conn.commit()

    logger.info("End-to-End Ingestion Test PASSED!")

if __name__ == "__main__":
    asyncio.run(test_end_to_end_ingestion())
