#!/usr/bin/env python3
"""
Token-based authentication manager for sukusuku.ai integration
"""
import jwt
import sqlite3
import logging
import os
from datetime import datetime, timedelta
from flask import request, session, redirect, url_for, g
from functools import wraps

class TokenAuthManager:
    """Manage JWT tokens and session authentication with sukusuku.ai"""
    
    def __init__(self, secret_key, shared_db_path="users.db", main_site_url="https://suku-suku-site-developeraim.replit.app"):
        self.secret_key = secret_key
        self.shared_db_path = shared_db_path
        self.main_site_url = main_site_url
        self.algorithm = "HS256"
        
    def verify_token(self, token):
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get('user_id')
            
            if user_id:
                # Fetch user from shared database
                user_data = self.get_user_from_db(user_id)
                if user_data:
                    return {
                        'user_id': user_data[0],
                        'username': user_data[1],
                        'email': user_data[2],
                        'credits': user_data[3],
                        'created_at': user_data[4]
                    }
                    
        except jwt.ExpiredSignatureError:
            logging.warning("Token expired")
        except jwt.InvalidTokenError as e:
            logging.warning(f"Invalid token: {e}")
        except Exception as e:
            logging.error(f"Token verification error: {e}")
            
        return None
    
    def get_user_from_db(self, user_id):
        """Fetch user data from shared users.db"""
        try:
            conn = sqlite3.connect(self.shared_db_path)
            cursor = conn.cursor()
            
            # Query user from shared database
            cursor.execute("""
                SELECT id, username, email, credits, created_at 
                FROM users 
                WHERE id = ?
            """, (user_id,))
            
            user_data = cursor.fetchone()
            conn.close()
            
            return user_data
            
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return None
        except Exception as e:
            logging.error(f"Error fetching user: {e}")
            return None
    
    def get_user_credits(self, user_id):
        """Get real-time credits from shared database"""
        try:
            conn = sqlite3.connect(self.shared_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 0
            
        except Exception as e:
            logging.error(f"Error fetching credits: {e}")
            return 0
    
    def update_user_credits(self, user_id, new_credits, transaction_note=""):
        """Update credits in shared database"""
        try:
            conn = sqlite3.connect(self.shared_db_path)
            cursor = conn.cursor()
            
            # Update credits
            cursor.execute("""
                UPDATE users 
                SET credits = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (new_credits, user_id))
            
            # Log transaction if table exists
            try:
                cursor.execute("""
                    INSERT INTO transactions (user_id, amount, type, note, created_at)
                    VALUES (?, ?, 'deduction', ?, CURRENT_TIMESTAMP)
                """, (user_id, new_credits, transaction_note))
            except sqlite3.Error:
                # Transactions table might not exist, that's okay
                pass
                
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logging.error(f"Error updating credits: {e}")
            return False
    
    def check_authentication(self):
        """Check for valid authentication token from various sources"""
        token = None
        
        # 1. Check URL parameter (primary method from sukusuku.ai)
        if 'auth_token' in request.args:
            token = request.args.get('auth_token')
            
        # 2. Check Authorization header
        elif request.headers.get('Authorization'):
            auth_header = request.headers.get('Authorization')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
        # 3. Check cookies
        elif 'auth_token' in request.cookies:
            token = request.cookies.get('auth_token')
            
        # 4. Check session (if already stored)
        elif 'auth_token' in session:
            token = session['auth_token']
        
        if token:
            user_data = self.verify_token(token)
            if user_data:
                # Store in session for subsequent requests
                session['auth_token'] = token
                session['user_data'] = user_data
                return user_data
                
        return None
    
    def get_current_user(self):
        """Get current authenticated user"""
        # Check for fresh token first (priority for new logins)
        user_data = self.check_authentication()
        if user_data:
            return user_data
            
        # Then try session data
        if 'user_data' in session:
            user_data = session['user_data']
            # Refresh credits from database
            user_data['credits'] = self.get_user_credits(user_data['user_id'])
            return user_data
            
        return None
    
    def clear_session(self):
        """Clear authentication session"""
        session.pop('auth_token', None)
        session.pop('user_data', None)
    
    def get_login_url(self, return_url=None):
        """Get login URL with return path"""
        if return_url:
            return f"{self.main_site_url}/login?redirect={return_url}"
        return f"{self.main_site_url}/login"

# Global auth manager instance
auth_manager = TokenAuthManager(
    secret_key=os.environ.get('JWT_SECRET_KEY', 'fallback-secret-key'),
    shared_db_path="users.db",
    main_site_url="https://suku-suku-site-developeraim.replit.app"
)

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_data = auth_manager.get_current_user()
        if not user_data:
            # Redirect to sukusuku.ai login
            return_url = request.url
            login_url = auth_manager.get_login_url(return_url)
            return redirect(login_url)
        
        # Store user in Flask's g for easy access
        g.user = user_data
        return f(*args, **kwargs)
    return decorated_function

def check_auth_before_request():
    """Flask before_request handler to check authentication on every request"""
    # Skip auth check for static files and login endpoints
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['auth.login', 'auth.callback']
    ):
        return
    
    # Check authentication and store in g.user  
    user_data = auth_manager.get_current_user()
    g.user = user_data
    
    # Store user data in session for persistence across requests
    if user_data:
        session['user_data'] = user_data
        session['authenticated'] = True
        session.permanent = True