import asyncio
import logging
from datetime import datetime, timedelta, timezone
from backend.services.neon_db import get_db_connection, log_event
from backend.agents.response_drafter import ResponseDrafter
import uuid
import sys

# event loop policy set in main block below

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimerEngine:
    def __init__(self):
        # We might need a drafter to propose reminders
        self.response_drafter = ResponseDrafter()

    async def run(self):
        logger.info("Starting Timer & Reminder Engine...")
        while True:
            try:
                await self.check_timers()
                await asyncio.sleep(300) # Check every 5 mins
            except Exception as e:
                logger.error(f"Error in Timer loop: {e}")
                await asyncio.sleep(60)

    async def check_timers(self):
        conn = await get_db_connection()
        try:
            async with conn:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        SELECT se.id, se.type, se.decision_maker_id, se.step, dm.name, dm.status as dm_status, 
                               c.status as camp_status, tc.status as comp_status
                        FROM scheduled_emails se
                        JOIN decision_makers dm ON se.decision_maker_id = dm.id
                        JOIN campaigns c ON dm.campaign_id = c.id
                        JOIN target_companies tc ON dm.company_id = tc.id
                        WHERE se.status = 'pending' AND se.scheduled_date <= NOW()
                        FOR UPDATE OF se SKIP LOCKED
                    """)
                    due_tasks = await cur.fetchall()
                    
                    for task in due_tasks:
                        task_id = str(task['id'])
                        dm_status = task['dm_status']
                        camp_status = task['camp_status']
                        comp_status = task['comp_status']
                        
                        # 1. Check Cancellation (DM no longer active)
                        if dm_status != 'ACTIVE':
                            logger.info(f"Cancelling task {task_id} because DM status is {dm_status}")
                            await cur.execute("UPDATE scheduled_emails SET status = 'cancelled' WHERE id = %s", (task_id,))
                            continue

                        # 1b. Check Company Discovery (Short Circuit)
                        if comp_status == 'DISCOVERY':
                             logger.info(f"Cancelling task {task_id} because Company is in DISCOVERY")
                             await cur.execute("UPDATE scheduled_emails SET status = 'cancelled' WHERE id = %s", (task_id,))
                             continue
                            
                        # 2. Check Paused (Campaign not active)
                        if camp_status != 'MONITORING_ACTIVE':
                            # Just skip, leave as pending
                            continue
                            
                        # 3. Fire Timer
                        # Update status first to ensure exactly-once processing (at least once with lock?)
                        # We are in transaction, so fine.
                        await cur.execute("UPDATE scheduled_emails SET status = 'processed' WHERE id = %s", (task_id,))
                        
                        await self.fire_timer(cur, task)

                    await conn.commit()
        finally:
            await conn.close()

    async def fire_timer(self, cursor, task):
        dm_id = str(task['decision_maker_id'])
        timer_type = task['type']
        next_turn = task['step']
        
        logger.info(f"Firing {timer_type} for M {task['name']} ({dm_id})")
        
        # Log event
        await log_event(cursor, 'TIMER_FIRED', dm_id, 'DECISION_MAKER', {
            "timer_type": timer_type,
            "next_turn": next_turn,
            "schedule_id": str(task['id'])
        })
        
        if timer_type == 'TERMINATION_CHECK':
            # Termination logic
            await cursor.execute("UPDATE decision_makers SET status = 'TERMINATED' WHERE id = %s", (dm_id,))
            await log_event(cursor, 'DECISION_MAKER_TERMINATED', dm_id, 'DECISION_MAKER', {"reason": "NO_REPLY_AFTER_REMINDERS"})
            return

        # For Reminders: We need to draft a follow-up
        # This will be handled by the Orchestrator reacting to TIMER_FIRED
        # or we can do it here. The user said Orchestrator is COORDINATOR.
        # I'll let the Orchestrator handle the drafting part to keep TimerEngine dumb.

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    engine = TimerEngine()
    asyncio.run(engine.run())
