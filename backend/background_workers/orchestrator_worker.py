import asyncio
import logging
import json
from backend.services.neon_db import get_db_connection, log_event
from backend.agents.intent_analyzer import IntentAnalyzer
from backend.agents.response_drafter import ResponseDrafter
import uuid
import sys

# Windows Selector Loop Fix
# This block is moved to the main execution block below.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitoringOrchestrator:
    def __init__(self):
        self.intent_analyzer = IntentAnalyzer()
        self.response_drafter = ResponseDrafter()

    async def run(self):
        logger.info("Starting Monitoring Orchestrator Worker...")
        while True:
            try:
                await self.process_events()
                await asyncio.sleep(10) # Process events every 10s
            except Exception as e:
                logger.error(f"Error in Orchestrator loop: {e}")
                await asyncio.sleep(30)

    async def process_events(self):
        conn = await get_db_connection()
        try:
            async with conn:
                async with conn.cursor() as cur:
                    # 1. Fetch events with Concurrency Control
                    await cur.execute("""
                        SELECT * FROM event_log 
                        WHERE processed = FALSE 
                          AND (next_retry_at IS NULL OR next_retry_at <= NOW())
                          AND retry_count < 5
                        ORDER BY created_at ASC 
                        LIMIT 10
                        FOR UPDATE SKIP LOCKED
                    """)
                    events = await cur.fetchall()
                    
                    if not events: return

                    for event in events:
                        event_id = event['id']
                        try:
                            # 2. Individual Event Transaction (Atomicity)
                            async with conn.transaction():
                                await self.handle_event(cur, event)
                                await cur.execute("UPDATE event_log SET processed = TRUE WHERE id = %s", (event_id,))
                            logger.info(f"Successfully processed event {event_id}")
                        except Exception as e:
                            logger.error(f"Failure processing event {event_id}: {e}")
                            # 3. Error Handling & Potential Backoff (Component 10)
                            retries = (event.get('retry_count') or 0) + 1
                            backoff_map = {1: 1, 2: 5, 3: 30, 4: 120, 5: 600}
                            delay = backoff_map.get(retries, 1440) # Default 1 day if somehow beyond 5
                            
                            await cur.execute("""
                                UPDATE event_log SET 
                                retry_count = %s, 
                                last_error = %s,
                                next_retry_at = NOW() + INTERVAL '%s minutes'
                                WHERE id = %s
                            """, (retries, str(e), delay, event_id))
                    
                    await conn.commit()
        except Exception as e:
            logger.error(f"Critical error in process_events: {e}")
        finally:
            await conn.close()

    async def handle_event(self, cursor, event):
        event_type = event['event_type']
        entity_id = str(event['entity_id'])
        logger.info(f"Handling event: {event_type} for {entity_id}")

        if event_type == 'EMAIL_RECEIVED':
            await self.handle_email_received(cursor, entity_id)
        elif event_type == 'INTENT_CLASSIFIED':
            await self.handle_intent_classified(cursor, entity_id)
        elif event_type == 'TIMER_FIRED':
            await self.handle_timer_fired(cursor, entity_id, event['payload'])

    async def handle_email_received(self, cursor, email_id):
        # 1. Get email body
        await cursor.execute("SELECT body, decision_maker_id FROM emails WHERE id = %s", (email_id,))
        email = await cursor.fetchone()
        if not email:
             logger.warning(f"Orphan event detected: Email {email_id} no longer exists. Marking event as processed.")
             return # Return normally so it gets marked as processed

        # 2. Analyze Intent
        analysis = await self.intent_analyzer.analyze(email['body'])
        
        # 3. Update Email with intent
        await cursor.execute("""
            UPDATE emails SET 
            intent = %s, 
            intent_confidence = %s 
            WHERE id = %s
        """, (analysis['intent'], analysis['confidence'], email_id))
        
        # 4. Emit INTENT_CLASSIFIED
        await log_event(cursor, 'INTENT_CLASSIFIED', email_id, 'EMAIL', {
            "intent": analysis['intent'],
            "dm_id": str(email['decision_maker_id'])
        })

    async def handle_intent_classified(self, cursor, email_id):
        # 1. Get context
        await cursor.execute("""
            SELECT e.*, dm.campaign_id 
            FROM emails e
            JOIN decision_makers dm ON e.decision_maker_id = dm.id
            WHERE e.id = %s
        """, (email_id,))
        email = await cursor.fetchone()
        if not email:
            logger.warning(f"Orphan event detected: Context for Email {email_id} missing. Skipping.")
            return
        
        intent = email['intent']
        dm_id = str(email['decision_maker_id'])
        
        if intent == 'NEGATIVE':
            # Termination logic (Component 8)
            await cursor.execute("UPDATE decision_makers SET status = 'TERMINATED' WHERE id = %s", (dm_id,))
            await cursor.execute("UPDATE scheduled_emails SET status = 'cancelled' WHERE decision_maker_id = %s AND status = 'pending'", (dm_id,))
            await log_event(cursor, 'DECISION_MAKER_TERMINATED', dm_id, 'DECISION_MAKER', {"reason": "NEGATIVE_INTENT"})
            return

        if intent == 'POSITIVE':
            # Discovery logic (Component 7)
            await cursor.execute("UPDATE decision_makers SET status = 'DISCOVERY' WHERE id = %s", (dm_id,))
            await cursor.execute("UPDATE scheduled_emails SET status = 'cancelled' WHERE decision_maker_id = %s AND status = 'pending'", (dm_id,))
            await log_event(cursor, 'DECISION_MAKER_DISCOVERY', dm_id, 'DECISION_MAKER', {"email_id": email_id})
            
            # TRIGGER COMPANY DISCOVERY (Rule: If ONE reached Discovery -> STOP monitoring company)
            await cursor.execute("SELECT company_id FROM decision_makers WHERE id = %s", (dm_id,))
            dm_info = await cursor.fetchone()
            if dm_info:
                co_id = str(dm_info['company_id'])
                # 1. Update Company Status
                await cursor.execute("UPDATE target_companies SET status = 'DISCOVERY' WHERE id = %s", (co_id,))
                
                # 2. TERMINATE COLLEAGUES (Cascade Termination)
                # Find all other DMs at this company who aren't already terminated/discovery
                await cursor.execute("""
                    UPDATE decision_makers 
                    SET status = 'TERMINATED' 
                    WHERE company_id = %s AND id != %s AND status NOT IN ('DISCOVERY', 'BLACKLISTED')
                """, (co_id, dm_id))
                
                # 3. CLEAN UP THEIR QUEUES
                # Cancel scheduled emails for other DMs in this company
                await cursor.execute("""
                    UPDATE scheduled_emails 
                    SET status = 'cancelled' 
                    WHERE decision_maker_id IN (SELECT id FROM decision_makers WHERE company_id = %s AND id != %s)
                    AND status = 'pending'
                """, (co_id, dm_id))
                
                # Revoke pending approval drafts for other DMs in this company
                await cursor.execute("""
                    UPDATE emails 
                    SET status = 'DECLINED' 
                    WHERE decision_maker_id IN (SELECT id FROM decision_makers WHERE company_id = %s AND id != %s)
                    AND status = 'PENDING_APPROVAL'
                """, (co_id, dm_id))

                await log_event(cursor, 'COMPANY_DISCOVERY_CASCADE', co_id, 'COMPANY', {"trigger_dm_id": dm_id})
            return

        if intent == 'NEUTRAL':
            # 2. Find original pitch for context
            # We want the last OUTBOUND PITCH or REPLY that initiated this.
            await cursor.execute("""
                SELECT * FROM emails 
                WHERE decision_maker_id = %s AND direction = 'outbound' 
                AND type IN ('pitch', 'reply', 'reminder_1', 'reminder_2')
                ORDER BY created_at DESC LIMIT 1
            """, (dm_id,))
            original = await cursor.fetchone()
            if not original:
                logger.warning(f"No original pitch found for DM {dm_id}")
                return

            # 3. Draft Response
            draft = await self.response_drafter.draft_response(
                {"intent": intent, "reasoning": "Neutral sentiment detected"},
                original,
                email['body']
            )
            
            if draft:
                # 4. Consolidate Draft to DB (PENDING_APPROVAL)
                draft_id = str(uuid.uuid4())
                await cursor.execute("""
                    INSERT INTO emails (id, decision_maker_id, subject, body, status, direction, type)
                    VALUES (%s, %s, %s, %s, 'PENDING_APPROVAL', 'outbound', 'reply')
                """, (draft_id, dm_id, draft['subject'], draft['body']))
                
                await log_event(cursor, 'RESPONSE_DRAFTED', draft_id, 'EMAIL', {"parent_email_id": email_id})

    async def handle_timer_fired(self, cursor, dm_id, payload):
        timer_type = payload.get('timer_type')
        logger.info(f"Handling TIMER_FIRED {timer_type} for DM {dm_id}")
        
        # 1. Get original pitch (context)
        await cursor.execute("""
            SELECT * FROM emails 
            WHERE decision_maker_id = %s AND direction = 'outbound' 
            ORDER BY created_at DESC LIMIT 1
        """, (dm_id,))
        original = await cursor.fetchone()
        if not original and timer_type != 'TERMINATION_CHECK':
            logger.warning(f"Orphan event detected: DM {dm_id} has no outreach history for timer {timer_type}. Skipping.")
            return
        
        # 2. Draft Reminder
        draft = await self.response_drafter.draft_reminder(timer_type, original or {})
        
        if draft:
            # 3. Save as Draft
            draft_id = str(uuid.uuid4())
            await cursor.execute("""
                INSERT INTO emails (id, decision_maker_id, subject, body, status, direction, type)
                VALUES (%s, %s, %s, %s, 'PENDING_APPROVAL', 'outbound', %s)
            """, (draft_id, dm_id, draft['subject'], draft['body'], timer_type.lower()))
            
            await log_event(cursor, 'REMINDER_DRAFTED', draft_id, 'EMAIL', {"timer_type": timer_type})

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    worker = MonitoringOrchestrator()
    asyncio.run(worker.run())
