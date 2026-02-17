import requests
import time
import json
import sys

# Configuration
API_URL = "http://localhost:8000"
CAMPAIGN_QUERY = "I want to sell CRM software to real estate agencies in Austin. Find me 2 targets."

def test_api_health():
    print("Testing API Health...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("API is healthy.")
            return True
        else:
            print(f"API Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"API Connection Failed: {e}")
        return False

def test_create_campaign():
    print(f"\nCreating Campaign with query: '{CAMPAIGN_QUERY}'")
    payload = {"query": CAMPAIGN_QUERY}
    start_time = time.time()
    
    try:
        response = requests.post(f"{API_URL}/campaigns", json=payload)
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            campaign_id = data.get("campaign_id")
            print(f"Campaign Created Successfully in {end_time - start_time:.2f}s")
            print(f"Campaign ID: {campaign_id}")
            
            # Verify Structure
            assert data["campaign"]["name"] is not None
            assert len(data["target_companies"]) > 0
            assert len(data["decision_makers"]) > 0
            assert len(data["email_drafts"]) > 0
            assert len(data["scheduled_emails"]) > 0
            
            print(f" - Found {len(data['target_companies'])} Companies")
            print(f" - Found {len(data['decision_makers'])} Decision Makers")
            print(f" - Generated {len(data['email_drafts'])} Email Drafts")
            print(f" - Scheduled {len(data['scheduled_emails'])} Follow-ups")
            
            return campaign_id
        else:
            print(f"Campaign Creation Failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Request Failed: {e}")
        return None

def test_get_campaign(campaign_id):
    print(f"\nRetrieving Campaign Details for ID: {campaign_id}")
    try:
        response = requests.get(f"{API_URL}/campaigns/{campaign_id}")
        if response.status_code == 200:
            data = response.json()
            print("Campaign Details Retrieved Successfully.")
            
            # Verify Persistence
            assert data["campaign"]["id"] == campaign_id
            assert len(data["companies"]) > 0
            assert len(data["decision_makers"]) > 0
            
            # Verify specific data points
            print(f" - Verified Persistence: {data['campaign']['name']}")
            return True
        else:
            print(f"Get Campaign Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"Request Failed: {e}")
        return False

def test_list_campaigns(campaign_id):
    print("\nListing All Campaigns...")
    try:
        response = requests.get(f"{API_URL}/campaigns")
        if response.status_code == 200:
            data = response.json()
            campaigns = data.get("campaigns", [])
            print(f"Found {len(campaigns)} campaigns.")
            
            # Check if our new campaign is in the list
            found = any(c['id'] == campaign_id for c in campaigns)
            if found:
                print(f"Verified Campaign {campaign_id} is in the list.")
                return True
            else:
                print(f"Error: Campaign {campaign_id} not found in list.")
                return False
        else:
            print(f"List Campaigns Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"Request Failed: {e}")
        return False

if __name__ == "__main__":
    if not test_api_health():
        sys.exit(1)
        
    campaign_id = test_create_campaign()
    if not campaign_id:
        sys.exit(1)
        
    if not test_get_campaign(campaign_id):
        sys.exit(1)
        
    if not test_list_campaigns(campaign_id):
        sys.exit(1)
        
    print("\n*** Backend E2E Test Passed Successfully ***")
