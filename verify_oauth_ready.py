#!/usr/bin/env python3
"""
Verify OAuth is ready for testing
"""
import os
import requests
from urllib.parse import urlencode

def verify_oauth_setup():
    """Complete verification of OAuth setup"""
    print("=== OAuth Readiness Check ===")
    
    # Check environment
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    domain = os.environ.get("REPLIT_DEV_DOMAIN")
    
    print(f"Domain: {domain}")
    print(f"Client ID: {'✓' if client_id else '✗'} {client_id[:30] + '...' if client_id else 'Missing'}")
    print(f"Client Secret: {'✓' if client_secret else '✗'} {'Present' if client_secret else 'Missing'}")
    
    # Expected new credentials
    expected_client_id = "814950413158-ug0h11ft0j7lqkrbd93n2dac06jsrlsu.apps.googleusercontent.com"
    
    if client_id == expected_client_id:
        print("✅ New OAuth credentials detected!")
        
        # Test OAuth URL
        redirect_uri = f"https://{domain}/working_google_login/callback"
        
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': 'openid email profile',
            'response_type': 'code',
            'state': 'test_state',
            'access_type': 'offline',
            'prompt': 'select_account'
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        
        try:
            response = requests.get(auth_url, allow_redirects=False, timeout=10)
            if response.status_code in [200, 302]:
                print("✅ OAuth URL test: SUCCESS")
                print("✅ Google accepts the authentication request")
                print("✅ Ready for testing!")
                print(f"\n🎯 Test the Google login at: /auth/login")
                return True
            else:
                print(f"❌ OAuth URL test failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ OAuth URL test error: {e}")
            return False
    else:
        print("⏳ Waiting for new OAuth credentials to be updated...")
        print(f"Expected: {expected_client_id}")
        print(f"Current:  {client_id or 'None'}")
        return False

if __name__ == "__main__":
    verify_oauth_setup()