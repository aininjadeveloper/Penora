#!/usr/bin/env python3
"""
Quick test script to verify new Google OAuth credentials
"""
import os

def test_new_oauth():
    print("=== Testing New Google OAuth Credentials ===")
    
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    domain = os.environ.get("REPLIT_DEV_DOMAIN")
    
    print(f"Domain: {domain}")
    print(f"Client ID: {'✓ Present' if client_id else '✗ Missing'}")
    print(f"Client Secret: {'✓ Present' if client_secret else '✗ Missing'}")
    
    if client_id:
        print(f"Client ID preview: {client_id[:30]}...")
    
    redirect_uri = f"https://{domain}/working_google_login/callback"
    print(f"Required redirect URI: {redirect_uri}")
    
    if client_id and client_secret:
        print("\n✅ OAuth credentials are configured!")
        print("You can now test Google login at: /auth/login")
    else:
        print("\n❌ OAuth credentials missing.")
        print("Add GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET to Replit Secrets")

if __name__ == "__main__":
    test_new_oauth()