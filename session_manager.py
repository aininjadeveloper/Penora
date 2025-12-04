#!/usr/bin/env python3
"""
Session manager for main website integration
"""
from flask import session, request, url_for, redirect
import requests
import logging

class SessionManager:
    """Manage sessions with main website integration"""
    
    def __init__(self, main_website_url):
        self.main_website_url = main_website_url
        
    def sync_from_main_website(self):
        """Sync user session from main website cookies/headers"""
        try:
            # Check for session data from cookies or URL parameters
            session_token = None
            
            # Option 1: Check URL parameter (when redirected from main website)
            if 'session_token' in request.args:
                session_token = request.args.get('session_token')
                
            # Option 2: Check cookies (shared domain or cross-domain setup)
            elif 'main_session' in request.cookies:
                session_token = request.cookies.get('main_session')
                
            # Option 3: Check custom header
            elif request.headers.get('X-Main-Session'):
                session_token = request.headers.get('X-Main-Session')
                
            if session_token:
                # Verify session with main website
                user_data = self.verify_session_with_main_website(session_token)
                if user_data:
                    session['user_data'] = user_data
                    session['main_session_token'] = session_token
                    return user_data
                    
        except Exception as e:
            logging.error(f"Error syncing session: {e}")
            
        return None
    
    def verify_session_with_main_website(self, session_token):
        """Verify session token with main website"""
        try:
            # For now, simulate user data based on session token
            # In production, this would make an API call to your main website
            
            # Mock verification - replace with actual API call
            if session_token and len(session_token) > 10:
                return {
                    'user_id': 'user_123',
                    'username': 'testuser',
                    'email': 'user@example.com',
                    'credits': 50  # This would come from main website
                }
                
        except Exception as e:
            logging.error(f"Error verifying session: {e}")
            
        return None
    
    def get_current_user(self):
        """Get current user from session"""
        return session.get('user_data')
    
    def get_user_credits(self):
        """Get user credits (from main website or session)"""
        user_data = self.get_current_user()
        if user_data:
            # In production, make API call to get real-time credits
            return user_data.get('credits', 0)
        return 0
    
    def clear_session(self):
        """Clear user session"""
        session.pop('user_data', None)
        session.pop('main_session_token', None)

# Global session manager
session_manager = SessionManager("https://c1ba9609-94a3-4895-8d7d-a2f5a0c196c7-00-1q7j60lf4r7la.riker.replit.dev")