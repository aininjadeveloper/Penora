#!/usr/bin/env python3
"""
Manual test with new OAuth credentials
"""
import requests
from urllib.parse import urlencode

# Your new credentials
NEW_CLIENT_ID = "814950413158-ug0h11ft0j7lqkrbd93n2dac06jsrlsu.apps.googleusercontent.com"
DOMAIN = "e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev"

def test_new_credentials():
    """Test OAuth with the new credentials"""
    redirect_uri = f"https://{DOMAIN}/working_google_login/callback"
    
    params = {
        'client_id': NEW_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': 'openid email profile',
        'response_type': 'code',
        'state': 'test_state_123',
        'access_type': 'offline',
        'prompt': 'select_account'
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    print("=== Testing New OAuth Credentials ===")
    print(f"New Client ID: {NEW_CLIENT_ID}")
    print(f"Redirect URI: {redirect_uri}")
    print(f"Auth URL (first 100 chars): {auth_url[:100]}...")
    
    # Test if Google accepts the new client
    try:
        print("\nTesting OAuth URL accessibility...")
        response = requests.get(auth_url, allow_redirects=False, timeout=15)
        
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ SUCCESS: Google accepts the OAuth request!")
            print("The new client ID is working correctly.")
            location = response.headers.get('Location', 'No location header')
            print(f"Redirects to: {location[:100]}...")
        elif response.status_code == 400:
            print("❌ ERROR: Bad request - check redirect URI configuration")
        elif response.status_code == 403:
            print("❌ ERROR: Access forbidden - client may not be configured correctly")
        else:
            print(f"❌ UNEXPECTED: Status {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print(f"\n📋 COPY THIS REDIRECT URI TO GOOGLE CONSOLE:")
    print(f"{redirect_uri}")

if __name__ == "__main__":
    test_new_credentials()