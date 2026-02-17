import psycopg
from psycopg.rows import dict_row
from backend.config.settings import settings
import uuid
import json
import logging

print("### NEON_DB.PY LOADED ###")

logger = logging.getLogger(__name__)

async def get_db_connection():
    try:
        conn = await psycopg.AsyncConnection.connect(
            settings.NEON_DB_URL, 
            row_factory=dict_row
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise e

async def create_campaign(name: str, product_description: str) -> str:
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                campaign_id = str(uuid.uuid4())
                await cur.execute(
                    "INSERT INTO campaigns (id, name, product_description, status) VALUES (%s, %s, %s, 'DRAFT') RETURNING id",
                    (campaign_id, name, product_description)
                )
                await log_event(cur, 'CAMPAIGN_CREATED', campaign_id, 'CAMPAIGN', {"name": name})
                return campaign_id
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        return None
    finally:
        await conn.close()

async def update_campaign_basic(campaign_id: str, name: str, product_description: str) -> bool:
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE campaigns SET name = %s, product_description = %s WHERE id = %s",
                    (name, product_description, campaign_id)
                )
                return True
    except Exception as e:
        logger.error(f"Error updating campaign basic: {e}")
        return False
    finally:
        await conn.close()

async def update_campaign_profile(campaign_id: str, profile_data: dict) -> bool:
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """UPDATE campaigns SET 
                    value_proposition = %s, 
                    key_offerings = %s, 
                    target_audience = %s, 
                    strategic_positioning = %s 
                    WHERE id = %s""",
                    (
                        profile_data.get("value_proposition"),
                        profile_data.get("key_offerings", []),
                        profile_data.get("target_audience"),
                        profile_data.get("strategic_positioning"),
                        campaign_id
                    )
                )
                return True
    except Exception as e:
        logger.error(f"Error updating campaign profile: {e}")
        return False
    finally:
        await conn.close()

async def save_target_company(campaign_id: str, company_data: dict) -> str:
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                # Check if already exists for this campaign
                await cur.execute("SELECT id FROM target_companies WHERE campaign_id = %s AND name = %s", (campaign_id, company_data.get("name")))
                existing = await cur.fetchone()
                if existing:
                    return str(existing['id'])

                company_id = str(uuid.uuid4())
                await cur.execute(
                    """INSERT INTO target_companies 
                    (id, campaign_id, name, website, description, relevance_score, recent_news, key_challenges, strategic_priorities) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (
                        company_id, 
                        campaign_id, 
                        company_data.get("name"), 
                        company_data.get("website"), 
                        company_data.get("description"),
                        company_data.get("relevance_score"),
                        company_data.get("recent_news", []),
                        company_data.get("key_challenges", []),
                        company_data.get("strategic_priorities", [])
                    )
                )
                return company_id
    except Exception as e:
        logger.error(f"Error saving company {company_data.get('name')}: {e}")
        return None
    finally:
        await conn.close()

async def save_decision_maker(campaign_id: str, company_id: str, person_data: dict) -> str:
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                # Check duplicate by email
                email = person_data.get("email")
                if email:
                    await cur.execute("SELECT id FROM decision_makers WHERE email = %s AND campaign_id = %s", (email, campaign_id))
                    existing = await cur.fetchone()
                    if existing:
                        return str(existing['id'])

                dm_id = str(uuid.uuid4())
                await cur.execute(
                    """INSERT INTO decision_makers 
                    (id, campaign_id, company_id, name, role, role_category, email, linkedin, status, turn_count) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0) RETURNING id""",
                    (
                        dm_id,
                        campaign_id,
                        company_id,
                        person_data.get("name"),
                        person_data.get("role"),
                        person_data.get("role_category"),
                        email,
                        person_data.get("linkedin"),
                        "new"
                    )
                )
                return dm_id
    except Exception as e:
        logger.error(f"Error saving decision maker {person_data.get('name')}: {e}")
        return None
    finally:
        await conn.close()

async def save_email_draft(decision_maker_id: str, subject: str, body: str, recipient: str = None, sender: str = "System") -> str:
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                # Idempotency check: Don't create duplicate 'initial' drafts for the same DM
                await cur.execute(
                    "SELECT id FROM emails WHERE decision_maker_id = %s AND type = 'initial' AND direction = 'outbound'",
                    (decision_maker_id,)
                )
                existing = await cur.fetchone()
                if existing:
                    # Update existing draft body instead of creating new one
                    await cur.execute(
                        "UPDATE emails SET subject = %s, body = %s, recipient = %s WHERE id = %s",
                        (subject, body, recipient, existing['id'])
                    )
                    return str(existing['id'])

                email_id = str(uuid.uuid4())
                await cur.execute(
                    """INSERT INTO emails 
                    (id, decision_maker_id, subject, body, recipient, sent_at, status, type, sender, direction) 
                    VALUES (%s, %s, %s, %s, %s, NULL, 'PENDING_APPROVAL', 'initial', %s, 'outbound') RETURNING id""",
                    (email_id, decision_maker_id, subject, body, recipient, sender)
                )
                await log_event(cur, 'EMAIL_DRAFTED', email_id, 'EMAIL', {"dm_id": decision_maker_id})
                return email_id
    except Exception as e:
        logger.error(f"Error saving email draft: {e}")
        return None
    finally:
        await conn.close()

async def save_email(decision_maker_id: str, email_data: dict) -> str:
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                email_id = str(uuid.uuid4())
                await cur.execute(
                    """INSERT INTO emails 
                    (id, decision_maker_id, subject, body, sent_at, status, type, sender, direction) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'inbound') RETURNING id""",
                    (
                        email_id, 
                        decision_maker_id, 
                        email_data.get("subject"), 
                        email_data.get("body"), 
                        email_data.get("sent_at"),
                        email_data.get("status", "received"),
                        email_data.get("type", "reply"),
                        email_data.get("sender", "Prospect")
                    )
                )
                return email_id
    except Exception as e:
        logger.error(f"Error saving email: {e}")
        return None
    finally:
        await conn.close()

async def save_scheduled_email(decision_maker_id: str, scheduled_data: dict) -> str:
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                task_id = str(uuid.uuid4())
                await cur.execute(
                    """INSERT INTO scheduled_emails 
                    (id, decision_maker_id, recipient_email, subject, body, scheduled_date, status, type, step) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (
                        task_id, 
                        decision_maker_id, 
                        scheduled_data.get("recipient_email"), 
                        scheduled_data.get("subject"), 
                        scheduled_data.get("body"), 
                        scheduled_data.get("scheduled_date"),
                        "pending",
                        scheduled_data.get("type", "reminder"),
                        scheduled_data.get("step", 1)
                    )
                )
                return task_id
    except Exception as e:
        logger.error(f"Error saving scheduled email: {e}")
        return None
    finally:
        await conn.close()

async def update_campaign_status(campaign_id: str, status: str) -> bool:
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE campaigns SET status = %s WHERE id = %s",
                    (status, campaign_id)
                )
                await log_event(cur, 'CAMPAIGN_STATUS_UPDATED', campaign_id, 'CAMPAIGN', {"status": status})
                return True
    except Exception as e:
        logger.error(f"Error updating campaign status: {e}")
        return False
    finally:
        await conn.close()

async def get_all_campaigns():
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id, name, status, created_at FROM campaigns ORDER BY created_at DESC")
                return await cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching campaigns: {e}")
        return []
    finally:
        await conn.close()

async def get_campaign_details(campaign_id: str):
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                details = {"campaign": None, "companies": [], "decision_makers": [], "emails": [], "scheduled_emails": []}
                
                # 1. Campaign Info
                await cur.execute("SELECT * FROM campaigns WHERE id = %s", (campaign_id,))
                details["campaign"] = await cur.fetchone()
                
                if not details["campaign"]:
                    return None

                # 2. Target Companies
                await cur.execute("SELECT * FROM target_companies WHERE campaign_id = %s", (campaign_id,))
                details["companies"] = await cur.fetchall()
                
                # 3. Decision Makers
                await cur.execute("SELECT * FROM decision_makers WHERE campaign_id = %s", (campaign_id,))
                details["decision_makers"] = await cur.fetchall()
                
                # 4. Emails & Schedules (Need DM IDs)
                dm_ids = [dm['id'] for dm in details["decision_makers"]]
                if dm_ids:
                    # Using = ANY(%s) is more robust in PostgreSQL for passing lists/tuples
                    await cur.execute("SELECT * FROM emails WHERE decision_maker_id = ANY(%s) ORDER BY sent_at DESC", (dm_ids,))
                    details["emails"] = await cur.fetchall()
                    
                    await cur.execute("SELECT * FROM scheduled_emails WHERE decision_maker_id = ANY(%s) ORDER BY scheduled_date ASC", (dm_ids,))
                    details["scheduled_emails"] = await cur.fetchall()
                    
                return details
    except Exception as e:
        logger.error(f"Error fetching campaign details: {e}")
        return None
    finally:
        await conn.close()

async def update_decision_maker_email(dm_id: str, new_email: str) -> bool:
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE decision_makers SET email = %s WHERE id = %s", (new_email, dm_id))
                # Also update recipient_email in scheduled_emails
                await cur.execute("UPDATE scheduled_emails SET recipient_email = %s WHERE decision_maker_id = %s AND status = 'pending'", (new_email, dm_id))
                # CRITICAL: Also update the 'recipient' field in existing 'PENDING_APPROVAL' drafts
                await cur.execute("UPDATE emails SET recipient = %s WHERE decision_maker_id = %s AND status = 'PENDING_APPROVAL'", (new_email, dm_id))
                return True
    except Exception as e:
        logger.error(f"Error updating DM email: {e}")
        return False
    finally:
        await conn.close()

async def update_email_draft(email_id: str, subject: str, body: str, recipient: str = None) -> bool:
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                if recipient:
                    await cur.execute(
                        "UPDATE emails SET subject = %s, body = %s, recipient = %s WHERE id = %s",
                        (subject, body, recipient, email_id)
                    )
                else:
                    await cur.execute(
                        "UPDATE emails SET subject = %s, body = %s WHERE id = %s",
                        (subject, body, email_id)
                    )
                return True
    except Exception as e:
        logger.error(f"Error updating email draft: {e}")
        return False
    finally:
        await conn.close()

async def mark_email_sent(email_id: str) -> bool:
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                # 0. Idempotency Check
                await cur.execute("SELECT status, decision_maker_id FROM emails WHERE id = %s", (email_id,))
                current = await cur.fetchone()
                if not current: return False
                if current['status'] == 'SENT':
                    logger.info(f"Email {email_id} already sent. Skipping.")
                    return True
                
                dm_id = current['decision_maker_id']

                # 0b. Status Validation (Race Condition Fix)
                # Ensure DM and Company are still in a valid state to receive emails.
                await cur.execute("""
                    SELECT dm.status as dm_status, tc.status as co_status 
                    FROM decision_makers dm
                    JOIN target_companies tc ON dm.company_id = tc.id
                    WHERE dm.id = %s
                """, (dm_id,))
                status_res = await cur.fetchone()
                
                if not status_res: return False
                
                dm_status = status_res['dm_status']
                co_status = status_res['co_status']
                
                # If DM is Terminated/Discovery/Blacklisted -> ABORT
                invalid_dm_states = ['TERMINATED', 'DISCOVERY', 'BLACKLISTED', 'blacklisted']
                if dm_status in invalid_dm_states:
                    logger.warning(f"Aborting send for DM {dm_id}: Status is {dm_status}")
                    return False
                    
                # If Company is Discovery -> ABORT (System-wide suppression)
                if co_status == 'DISCOVERY':
                    logger.warning(f"Aborting send for DM {dm_id}: Company is DISCOVERY")
                    return False

                # 1. Update Email status
                await cur.execute(
                    "UPDATE emails SET status = 'SENT', sent_at = NOW(), human_approved = TRUE WHERE id = %s",
                    (email_id,)
                )

                # 2. Update Decision Maker (turn count and last_sent)
                await cur.execute(
                    "UPDATE decision_makers SET turn_count = turn_count + 1, last_outbound_at = NOW(), status = 'ACTIVE' WHERE id = %s RETURNING campaign_id, turn_count, email",
                    (dm_id,)
                )
                dm_res = await cur.fetchone()
                if not dm_res: return False
                campaign_id = dm_res['campaign_id']
                new_turn = dm_res['turn_count']
                dm_email = dm_res['email']

                # 3. Handle Campaign Activation (Hard Rule)
                # If campaign is MONITORING_READY, it becomes MONITORING_ACTIVE upon first sent
                await cur.execute("SELECT status FROM campaigns WHERE id = %s", (campaign_id,))
                camp = await cur.fetchone()
                if camp and camp['status'] == 'MONITORING_READY':
                    await cur.execute("UPDATE campaigns SET status = 'MONITORING_ACTIVE' WHERE id = %s", (campaign_id,))
                    await log_event(cur, 'MONITORING_ACTIVATED', campaign_id, 'CAMPAIGN')
                
                # 4. Schedule Next Reminder (Structural Fix: Explicit Scheduling)
                next_type = None
                if new_turn == 1: next_type = 'REMINDER_1' 
                elif new_turn == 2: next_type = 'REMINDER_2'
                elif new_turn == 3: next_type = 'TERMINATION_CHECK'
                elif new_turn > 10:
                    # Hard Limit Safety Net
                    await cur.execute("UPDATE decision_makers SET status = 'TERMINATED' WHERE id = %s", (dm_id,))
                    await log_event(cur, 'DECISION_MAKER_TERMINATED', str(dm_id), 'DECISION_MAKER', {"reason": "MAX_TURN_LIMIT"})
                
                if next_type:
                    sched_id = str(uuid.uuid4())
                    # Schedule for 2 days later (hard contract)
                    await cur.execute("""
                        INSERT INTO scheduled_emails 
                        (id, decision_maker_id, recipient_email, scheduled_date, status, type, step)
                        VALUES (%s, %s, %s, NOW() + INTERVAL '2 days', 'pending', %s, %s)
                    """, (sched_id, dm_id, dm_email, next_type, new_turn + 1))
                    await log_event(cur, 'TIMER_SCHEDULED', sched_id, 'SCHEDULE', {"type": next_type})

                # 5. Log event
                await log_event(cur, 'EMAIL_SENT', email_id, 'EMAIL', {"dm_id": str(dm_id), "campaign_id": str(campaign_id)})
                
                return True
    except Exception as e:
        logger.error(f"Error marking email as sent: {e}")
        return False
    finally:
        await conn.close()

async def log_event(cursor, event_type: str, entity_id: str, entity_type: str, payload: dict = None):
    """
    Internal helper to log events within an existing transaction cursor.
    """
    try:
        await cursor.execute(
            "INSERT INTO event_log (event_type, entity_id, entity_type, payload) VALUES (%s, %s, %s, %s)",
            (event_type, entity_id, entity_type, json.dumps(payload) if payload else None)
        )
    except Exception as e:
        logger.error(f"Failed to log event {event_type}: {e}")

async def update_company_status(company_id: str, status: str):
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE target_companies SET status = %s WHERE id = %s", (status, company_id))
                await log_event(cur, 'COMPANY_STATUS_UPDATED', company_id, 'COMPANY', {"status": status})
                return True
    except Exception as e:
        logger.error(f"Error updating company status: {e}")
        return False
    finally:
        await conn.close()

async def update_decision_maker_status(dm_id: str, status: str):
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE decision_makers SET status = %s WHERE id = %s", (status, dm_id))
                await log_event(cur, 'DECISION_MAKER_STATUS_UPDATED', dm_id, 'DECISION_MAKER', {"status": status})
                return True
    except Exception as e:
        logger.error(f"Error updating DM status: {e}")
        return False
    finally:
        await conn.close()

async def reject_decision_maker(dm_id: str) -> bool:
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE decision_makers SET status = 'blacklisted' WHERE id = %s", (dm_id,))
                await cur.execute("UPDATE scheduled_emails SET status = 'cancelled' WHERE decision_maker_id = %s AND status = 'pending'", (dm_id,))
                return True
    except Exception as e:
        logger.error(f"Error rejecting DM: {e}")
        return False
    finally:
        await conn.close()

async def delete_campaign(campaign_id: str) -> bool:
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                # 1. Delete emails related to decision makers of this campaign
                await cur.execute(
                    "DELETE FROM emails WHERE decision_maker_id IN (SELECT id FROM decision_makers WHERE campaign_id = %s)",
                    (campaign_id,)
                )
                
                # 2. Delete scheduled emails related to decision makers of this campaign
                await cur.execute(
                    "DELETE FROM scheduled_emails WHERE decision_maker_id IN (SELECT id FROM decision_makers WHERE campaign_id = %s)",
                    (campaign_id,)
                )
                
                # 3. Delete decision makers
                await cur.execute("DELETE FROM decision_makers WHERE campaign_id = %s", (campaign_id,))
                
                # 4. Delete target companies
                await cur.execute("DELETE FROM target_companies WHERE campaign_id = %s", (campaign_id,))
                
                # 5. Finally delete the campaign
                await cur.execute("DELETE FROM campaigns WHERE id = %s", (campaign_id,))
                
                return True
    except Exception as e:
        logger.error(f"Error deleting campaign {campaign_id}: {e}")
        return False
    finally:
        await conn.close()

async def get_event_logs(entity_id: str):
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT * FROM event_log 
                    WHERE entity_id = %s OR (payload->>'dm_id') = %s OR (payload->>'campaign_id') = %s
                    ORDER BY created_at DESC 
                    LIMIT 50
                """, (entity_id, entity_id, entity_id))
                return await cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching event logs: {e}")
        return []
    finally:
        await conn.close()

async def save_sent_discovery_email(dm_id: str, subject: str, body: str, recipient: str):
    conn = await get_db_connection()
    try:
        async with conn:
            async with conn.cursor() as cur:
                email_id = str(uuid.uuid4())
                await cur.execute(
                    """INSERT INTO emails 
                    (id, decision_maker_id, subject, body, recipient, sent_at, status, type, sender, direction) 
                    VALUES (%s, %s, %s, %s, %s, NOW(), 'sent', 'discovery_invite', 'System', 'outbound')""",
                    (email_id, dm_id, subject, body, recipient)
                )
                # Update DM status to indicate discovery is in progress
                await cur.execute("UPDATE decision_makers SET status = 'DISCOVERY_SENT' WHERE id = %s", (dm_id,))
                await log_event(cur, 'DISCOVERY_EMAIL_SENT', dm_id, 'DECISION_MAKER', {"email_id": email_id})
                return True
    except Exception as e:
        logger.error(f"Error saving sent discovery email: {e}")
        return False
    finally:
        await conn.close()
