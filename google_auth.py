# Use this Flask blueprint for Google authentication. Do not use flask-dance.

import json
import os

import requests
from app import db
from flask import Blueprint, redirect, request, url_for
from flask_login import login_required, login_user, logout_user
from models import User
from oauthlib.oauth2 import WebApplicationClient

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Make sure to use this redirect URL. It has to match the one in the whitelist
DEV_REDIRECT_URL = f'https://{os.environ.get("REPLIT_DEV_DOMAIN")}/google_login/callback'

print(f"Google OAuth Configuration:")
print(f"Client ID exists: {'Yes' if GOOGLE_CLIENT_ID else 'No'}")
print(f"Client Secret exists: {'Yes' if GOOGLE_CLIENT_SECRET else 'No'}")
print(f"Redirect URL: {DEV_REDIRECT_URL}")

# Check if credentials are properly configured
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    print("ERROR: Google OAuth credentials not found!")
    print("Please set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in Replit Secrets")
else:
    print(f"Google OAuth configured. Redirect URI must be: {DEV_REDIRECT_URL}")

# Initialize OAuth client only if credentials exist
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    client = WebApplicationClient(GOOGLE_CLIENT_ID)
else:
    client = None

google_auth = Blueprint("google_auth", __name__)


@google_auth.route("/google_login")
def login():
    if not client or not GOOGLE_CLIENT_ID:
        from flask import flash
        flash('Google OAuth not configured properly', 'danger')
        return redirect(url_for('auth.login'))
    
    try:
        print(f"Initiating Google OAuth with Client ID: {GOOGLE_CLIENT_ID[:20]}...")
        
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use exact redirect URI that should be configured in Google Console
        redirect_uri = DEV_REDIRECT_URL
        
        print(f"Authorization endpoint: {authorization_endpoint}")
        print(f"Using redirect URI: {redirect_uri}")
        
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"],
            state="penora_oauth_state"
        )
        
        print(f"Generated OAuth URL: {request_uri}")
        return redirect(request_uri)
        
    except Exception as e:
        print(f"Error initiating Google login: {str(e)}")
        from flask import flash
        flash(f'Error initiating Google login: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))


@google_auth.route("/google_login/callback")
def callback():
    try:
        # Check for error parameter first
        error = request.args.get("error")
        if error:
            print(f"Google OAuth error: {error}")
            print(f"Error description: {request.args.get('error_description', 'No description')}")
            from flask import flash
            flash(f'Google authentication failed: {error}', 'danger')
            return redirect(url_for('auth.login'))
        
        code = request.args.get("code")
        if not code:
            print("No authorization code received from Google")
            from flask import flash
            flash('No authorization code received from Google', 'danger')
            return redirect(url_for('auth.login'))
            
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]

        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=DEV_REDIRECT_URL,
            code=code,
        )
        
        print(f"Token request URL: {token_url}")
        print(f"Redirect URL used: {request.base_url.replace('http://', 'https://')}")
        
        # Ensure credentials are not None before making request
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            print("ERROR: Missing Google OAuth credentials")
            from flask import flash
            flash('Google OAuth credentials not configured', 'danger')
            return redirect(url_for('auth.login'))
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        print(f"Token response status: {token_response.status_code}")
        print(f"Token response: {token_response.text}")
        
        if token_response.status_code != 200:
            print(f"Token request failed with status {token_response.status_code}")
            from flask import flash
            flash('Failed to get access token from Google', 'danger')
            return redirect(url_for('auth.login'))

        client.parse_request_body_response(json.dumps(token_response.json()))

        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        userinfo = userinfo_response.json()
        if userinfo.get("email_verified"):
            users_email = userinfo["email"]
            users_name = userinfo["given_name"]
        else:
            return "User email not available or not verified by Google.", 400

        user = User.query.filter_by(email=users_email).first()
        if not user:
            user = User()
            user.username = users_name
            user.email = users_email  
            user.credits = 10  # Give new users 10 free credits
            db.session.add(user)
            db.session.commit()

        login_user(user)

        return redirect(url_for("index"))
    except Exception as e:
        return f"Error processing Google login: {str(e)}", 500


@google_auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
