import httpx
import logging
from backend.config.settings import settings
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

async def get_work_email(name: str, domain: str) -> Optional[str]:
    """
    Search for a person's work email using Apollo.io API.
    Uses 'match' logic to be as precise as possible and save credits.
    """
    if not settings.APOLLO_API_KEY:
        logger.warning("APOLLO_API_KEY not set. Skipping enrichment.")
        return None

    url = "https://api.apollo.io/v1/people/match"
    
    # Split name into first and last
    parts = name.split(" ")
    first_name = parts[0]
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    headers = {
        "X-Api-Key": settings.APOLLO_API_KEY,
        "Content-Type": "application/json",
        "Cache-Control": "no-cache"
    }

    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "domain": domain
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                person = data.get("person", {})
                
                # Check for verified email
                email = person.get("email")
                if email:
                    status = person.get("email_status")
                    if status in ["verified", "likely_to_be_deliverable"]:
                        return email
                    else:
                        logger.info(f"Apollo found unverified email for {name}: {email} (Status: {status})")
                        return None
                else:
                    logger.info(f"Apollo found person but no email for {name}.")
                return None
            else:
                logger.error(f"Apollo API error ({response.status_code}): {response.text}")
                return None
    except Exception as e:
        logger.error(f"Error calling Apollo API: {e}")
        return None
