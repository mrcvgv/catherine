#!/usr/bin/env python3
"""
Service Account Gmail/Tasks
OAuthService Account
"""

import os
import json
import logging
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_service_account_credentials():
    """Service Account """
    service_account_key = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
    if not service_account_key:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY not found in environment")
    
    # JSON
    credentials_info = json.loads(service_account_key)
    
    # 
    scopes = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/tasks',
        'https://www.googleapis.com/auth/calendar'
    ]
    
    credentials = Credentials.from_service_account_info(
        credentials_info, 
        scopes=scopes
    )
    
    return credentials

def test_gmail_access():
    """Gmail API """
    print("\nTesting Gmail API access with Service Account...")
    
    try:
        credentials = get_service_account_credentials()
        
        # Gmail API service 
        service = build('gmail', 'v1', credentials=credentials)
        
        # 
        try:
            profile = service.users().getProfile(userId='me').execute()
            print(f"Gmail API connected successfully")
            print(f"   Email: {profile.get('emailAddress', 'Unknown')}")
            print(f"   Messages Total: {profile.get('messagesTotal', 0)}")
            print(f"   Threads Total: {profile.get('threadsTotal', 0)}")
            return True
        except Exception as e:
            print(f"Gmail API access failed: {e}")
            if "domain-wide delegation" in str(e).lower():
                print("This requires domain-wide delegation setup")
            return False
            
    except Exception as e:
        print(f" Service Account setup failed: {e}")
        return False

def test_tasks_access():
    """Google Tasks API """
    print("\n Testing Google Tasks API access with Service Account...")
    
    try:
        credentials = get_service_account_credentials()
        
        # Tasks API service 
        service = build('tasks', 'v1', credentials=credentials)
        
        # 
        try:
            tasklists = service.tasklists().list().execute()
            print(f" Google Tasks API connected successfully")
            
            lists = tasklists.get('items', [])
            print(f"   Task Lists found: {len(lists)}")
            
            for tasklist in lists[:3]:  # 3
                print(f"    {tasklist['title']} (ID: {tasklist['id']})")
            
            return True
            
        except Exception as e:
            print(f" Google Tasks API access failed: {e}")
            if "domain-wide delegation" in str(e).lower():
                print(" This requires domain-wide delegation setup")
            return False
            
    except Exception as e:
        print(f" Service Account setup failed: {e}")
        return False

def setup_domain_wide_delegation_guide():
    """Domain-wide delegation"""
    print("\n Domain-wide Delegation Setup Required")
    print("" * 50)
    print("Gmail API requires domain-wide delegation for service accounts.")
    print("\nSteps to enable:")
    print("1. Go to Google Cloud Console")
    print("2. Navigate to IAM & Admin  Service Accounts")
    print("3. Find your service account: catherine@catherine-470022.iam.gserviceaccount.com")
    print("4. Click 'Advanced settings'  'View Google Workspace Admin Console'")
    print("5. Enable domain-wide delegation")
    print("6. Add required scopes:")
    print("   - https://www.googleapis.com/auth/gmail.readonly")
    print("   - https://www.googleapis.com/auth/tasks")
    print("   - https://www.googleapis.com/auth/calendar")

def alternative_oauth_guide():
    """OAuth"""
    print("\n Alternative: OAuth User Authentication")
    print("" * 50)
    print("Instead of Service Account, use OAuth with personal account:")
    print("\n1. Google Cloud Console  APIs & Services  OAuth consent screen")
    print("2. Add test user: catherinecandyconytown@gmail.com")
    print("3. Status should change from 'Testing' to allow your email")
    print("4. Re-run the OAuth token script")
    print("\nOR")
    print("\n1. Publish the OAuth application (requires verification)")
    print("2. This allows any Google user to authenticate")

def main():
    print("Catherine Gmail/Tasks Integration Test")
    print("Using Service Account Authentication\n")
    
    gmail_success = test_gmail_access()
    tasks_success = test_tasks_access()
    
    print(f"\n Results Summary:")
    print(f"   Gmail API: {' Success' if gmail_success else ' Failed'}")
    print(f"   Tasks API: {' Success' if tasks_success else ' Failed'}")
    
    if not gmail_success or not tasks_success:
        print(f"\n Troubleshooting Options:")
        setup_domain_wide_delegation_guide()
        alternative_oauth_guide()
        
        print(f"\n Immediate Solutions:")
        print(f"1. Add test user to OAuth consent screen (easiest)")
        print(f"2. Use existing Calendar API (already working)")
        print(f"3. Implement Gmail/Tasks via MCP server with OAuth")
    else:
        print(f"\n All APIs working! Ready for integration.")

if __name__ == "__main__":
    main()