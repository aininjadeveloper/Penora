#!/usr/bin/env python3
"""
Integration with main website authentication and credit system
"""
import requests
import os
from flask import session, request, redirect
from functools import wraps

# Main website base URL
MAIN_WEBSITE_URL = "https://c1ba9609-94a3-4895-8d7d-a2f5a0c196c7-00-1q7j60lf4r7la.riker.replit.dev"

class WebsiteIntegration:
    """Handle integration with main website"""
    
    def __init__(self):
        self.base_url = MAIN_WEBSITE_URL
        
    def verify_user_session(self, session_token=None):
        """Verify user session with main website"""
        try:
            if not session_token:
                session_token = session.get('website_session_token')
                
            if not session_token:
                return None
                
            response = requests.get(
                f"{self.base_url}/api/verify-session",
                headers={'Authorization': f'Bearer {session_token}'},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"Error verifying session: {e}")
            return None
    
    def get_user_credits(self, user_id):
        """Get user credits from main website"""
        try:
            response = requests.get(
                f"{self.base_url}/api/user/{user_id}/credits",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('credits', 0)
            return 0
            
        except Exception as e:
            print(f"Error getting user credits: {e}")
            return 0
    
    def deduct_credits(self, user_id, amount, description="AI text generation"):
        """Deduct credits from user account on main website"""
        try:
            response = requests.post(
                f"{self.base_url}/api/user/{user_id}/deduct-credits",
                json={
                    'amount': amount,
                    'description': description
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"Error deducting credits: {e}")
            return None
    
    def add_credits(self, user_id, amount, description="Credit purchase"):
        """Add credits to user account on main website"""
        try:
            response = requests.post(
                f"{self.base_url}/api/user/{user_id}/add-credits",
                json={
                    'amount': amount,
                    'description': description
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"Error adding credits: {e}")
            return None

# Global integration instance
website_integration = WebsiteIntegration()

def require_website_auth(f):
    """Decorator to require authentication from main website"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for session token from main website
        session_token = request.headers.get('Authorization')
        if not session_token:
            session_token = request.cookies.get('session_token')
        if not session_token:
            session_token = session.get('website_session_token')
            
        user_data = website_integration.verify_user_session(session_token)
        if not user_data:
            # Redirect to main website login
            return redirect(f"{MAIN_WEBSITE_URL}/login?redirect={request.url}")
            
        # Store user data in session
        session['user_data'] = user_data
        session['website_session_token'] = session_token
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_website_user():
    """Get current user data from website session"""
    return session.get('user_data')

def sync_user_with_website():
    """Sync user session with main website"""
    # Check if user is coming from main website with session token
    session_token = request.args.get('session_token')
    if session_token:
        user_data = website_integration.verify_user_session(session_token)
        if user_data:
            session['user_data'] = user_data
            session['website_session_token'] = session_token
            return True
    return False