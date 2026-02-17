import asyncio
import logging
import aioimaplib
from email import message_from_bytes
from backend.config.settings import settings
from backend.services.neon_db import get_db_connection, log_event
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailIngestionService:
    def __init__(self):
        self.host = settings.IMAP_HOST
        self.user = settings.EMAIL_USER
        self.password = settings.EMAIL_PASSWORD

    async def run(self):
        logger.info("Starting Email Ingestion Service...")
        while True:
            try:
                # 1. Find active monitoring campaigns
                conn = await get_db_connection()
                async with conn:
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT id FROM campaigns WHERE status = 'MONITORING_ACTIVE'")
                        active_campaigns = await cur.fetchall()
                
                if not active_campaigns:
                    logger.debug("No active monitoring campaigns. Sleeping...")
                    await asyncio.sleep(60)
                    continue

                # 2. Check Inbox
                await self.poll_inbox()
                
                await asyncio.sleep(30) # Poll every 30s
            except Exception as e:
                logger.error(f"Error in Ingestion Service loop: {e}")
                await asyncio.sleep(60)

    async def poll_inbox(self, search_criterion: str = "UNSEEN"):
        logger.info(f"Connecting to IMAP {self.host} via Sync-to-Thread...")
        emails_to_process = await asyncio.to_thread(self._poll_inbox_sync, search_criterion)
        
        for email_data in emails_to_process:
            clean_email, subject, body, message_id = email_data
            await self.process_inbound_email(clean_email, subject, body, message_id)

    def _poll_inbox_sync(self, search_criterion):
        import imaplib
        from email import message_from_bytes
        
        results = []
        mail = None
        try:
            mail = imaplib.IMAP4_SSL(self.host, 993)
            mail.login(self.user, self.password)
            mail.select("INBOX")
            
            status, data = mail.search(None, search_criterion)
            if status != "OK" or not data[0]:
                return []

            msg_ids = data[0].split()
            for num in msg_ids:
                status, data = mail.fetch(num, "(RFC822)")
                if status != "OK": continue
                
                raw_email = data[0][1]
                msg = message_from_bytes(raw_email)
                
                sender = msg.get("From", "")
                subject = msg.get("Subject", "")
                message_id = msg.get("Message-ID", "")
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                body = part.get_payload(decode=True).decode()
                                break
                            except: pass
                else:
                    try:
                        body = msg.get_payload(decode=True).decode()
                    except: pass

                clean_email = sender.split('<')[-1].split('>')[0].strip()
                results.append((clean_email, subject, body, message_id))
                
        except Exception as e:
            logger.error(f"Sync IMAP Error: {e}")
        finally:
            if mail:
                try:
                    mail.logout()
                except:
                    pass
        return results

    async def process_inbound_email(self, email_addr: str, subject: str, body: str, message_id: str = None):
        conn = await get_db_connection()
        try:
            async with conn:
                async with conn.cursor() as cur:
                    # Match DM across ANY active monitoring campaign
                    await cur.execute("""
                        SELECT dm.id, dm.campaign_id 
                        FROM decision_makers dm
                        JOIN campaigns c ON dm.campaign_id = c.id
                        JOIN target_companies tc ON dm.company_id = tc.id
                        WHERE dm.email = %s AND c.status = 'MONITORING_ACTIVE'
                        AND tc.status = 'ACTIVE'
                    """, (email_addr,))
                    dm = await cur.fetchone()
                    
                    if not dm:
                        logger.info(f"Received email from unknown sender {email_addr}. Ignoring.")
                        return

                    # Check for duplicate ingestion (Production Grade: Message-ID)
                    if message_id:
                        await cur.execute("SELECT id FROM emails WHERE message_id = %s", (message_id,))
                        if await cur.fetchone():
                            logger.info(f"Skipping duplicate message_id: {message_id}")
                            return
                    else:
                        # Fallback to primitive
                        await cur.execute("SELECT id FROM emails WHERE decision_maker_id = %s AND body = %s", (dm['id'], body))
                        if await cur.fetchone():
                            return

                    # Persist
                    email_id = str(uuid.uuid4())
                    await cur.execute("""
                        INSERT INTO emails (id, decision_maker_id, sender, recipient, subject, body, status, direction, type, message_id)
                        VALUES (%s, %s, %s, %s, %s, %s, 'RECEIVED', 'inbound', 'reply', %s)
                        RETURNING id
                    """, (email_id, dm['id'], email_addr, self.user, subject, body, message_id))
                    print(f"DEBUG: Ingested email {email_id}", flush=True)
                    
                    # Emit Event
                    await log_event(cur, 'EMAIL_RECEIVED', email_id, 'EMAIL', {"dm_id": str(dm['id'])})
                    logger.info(f"Ingested new email from {email_addr} (DM: {dm['id']})")
        finally:
            await conn.close()

if __name__ == "__main__":
    service = EmailIngestionService()
    asyncio.run(service.run())
