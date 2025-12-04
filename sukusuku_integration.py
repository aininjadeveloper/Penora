#!/usr/bin/env python3
"""
High-Performance Sukusuku Integration - Optimized for Production Speed
"""

import sqlite3
import logging
import requests
from datetime import datetime
from flask import session, request, current_app
import os
import threading
from contextlib import contextmanager
import time
import hashlib

logger = logging.getLogger(__name__)

class FastSukusukuIntegration:
    def __init__(self, app_name="penora", main_site_url="https://sukusuku.ai"):
        self.app_name = app_name
        self.main_site_url = main_site_url
        self.shared_db_path = 'users.db'
        self._db_lock = threading.Lock()
        # Cache for frequently accessed users
        self._user_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self.init_database()
    
    @contextmanager
    def get_db_connection(self):
        """Optimized database connection with minimal overhead"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.shared_db_path, 
                timeout=10,  # Reduced timeout
                check_same_thread=False,
                isolation_level=None  # autocommit mode for speed
            )
            # Optimized SQLite settings for performance
            conn.execute('PRAGMA journal_mode=MEMORY')  # Fastest mode
            conn.execute('PRAGMA synchronous=OFF')  # Maximum speed
            conn.execute('PRAGMA cache_size=10000')  # Larger cache
            conn.execute('PRAGMA temp_store=memory')
            conn.execute('PRAGMA locking_mode=NORMAL')
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            # Don't raise, return None to allow fallback
            return None
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

    def init_database(self):
        """Initialize database with optimized schema"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        username TEXT NOT NULL,
                        email TEXT NOT NULL,
                        credits INTEGER DEFAULT 100,
                        subscription_status TEXT DEFAULT 'premium',
                        profile_image TEXT,
                        bio TEXT,
                        website TEXT,
                        social_links TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        last_login TEXT
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workspace_projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        project_title TEXT NOT NULL,
                        generation_text TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        code TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS credit_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        amount INTEGER NOT NULL,
                        transaction_type TEXT NOT NULL,
                        description TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_id ON users (id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user ON credit_transactions (user_id)")
                
                conn.commit()
            
            logger.info("Optimized database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def get_user_from_cache(self, user_id):
        """Get user from cache if still valid"""
        if user_id in self._user_cache:
            cached_user, timestamp = self._user_cache[user_id]
            if time.time() - timestamp < self._cache_ttl:
                return cached_user
        return None
    
    def cache_user(self, user_id, user_data):
        """Cache user data for performance"""
        self._user_cache[user_id] = (user_data, time.time())
    
    def deduct_credits(self, user_id, amount, description="Credit usage"):
        """High-performance credit deduction"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT credits FROM users WHERE id = ?", (str(user_id),))
                result = cursor.fetchone()
                
                if not result:
                    return False
                
                current_credits = result[0] if result[0] is not None else 100
                if current_credits < amount:
                    return False
                
                new_credits = max(0, current_credits - amount)
                cursor.execute("UPDATE users SET credits = ?, updated_at = ? WHERE id = ?", 
                             (new_credits, datetime.now().isoformat(), str(user_id)))
                
                # Log transaction
                cursor.execute("""
                    INSERT INTO credit_transactions (user_id, amount, transaction_type, description, app_name)
                    VALUES (?, ?, ?, ?, ?)
                """, (str(user_id), -amount, 'Used', description, 'penora'))
                
                # Clear cache for this user
                if user_id in self._user_cache:
                    del self._user_cache[user_id]
                
                return True
                
        except Exception as e:
            logger.error(f"Credit deduction error: {e}")
            return False
    
    def add_credits(self, user_id, amount, description="Credit purchase"):
        """Add credits to user account and create transaction record"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT credits FROM users WHERE id = ?", (str(user_id),))
                result = cursor.fetchone()
                
                if result:
                    # User exists, update credits
                    current_credits = result[0] if result[0] is not None else 0
                    new_credits = current_credits + amount
                    cursor.execute("UPDATE users SET credits = ?, updated_at = ? WHERE id = ?", 
                                 (new_credits, datetime.now().isoformat(), str(user_id)))
                else:
                    # User doesn't exist, create with initial credits
                    cursor.execute("""
                        INSERT INTO users (id, username, email, credits)
                        VALUES (?, ?, ?, ?)
                    """, (str(user_id), f"User_{user_id}", f"user_{user_id}@sukusuku.ai", amount))
                
                # Log transaction
                cursor.execute("""
                    INSERT INTO credit_transactions (user_id, amount, transaction_type, description, app_name)
                    VALUES (?, ?, ?, ?, ?)
                """, (str(user_id), amount, 'Purchase', description, 'penora'))
                
                # Clear cache for this user
                if user_id in self._user_cache:
                    del self._user_cache[user_id]
                
                logger.info(f"Added {amount} credits to user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Add credits error: {e}")
            return False

# Global instance
fast_sukusuku_integration = FastSukusukuIntegration()

def get_user_data():
    """Ultra-fast user authentication with caching and optimizations"""
    try:
        # STEP 0: Check for JWT SSO token first (highest priority)
        jwt_token = request.args.get('jwt_token')
        
        # STEP 1: Check URL parameters for sukusuku.ai integration
        user_id_param = request.args.get('user_id')
        email_param = request.args.get('email')
        first_name_param = request.args.get('first_name')
        last_name_param = request.args.get('last_name')
        dev_email_param = request.args.get('dev_email')
        
        # JWT SSO PATH: Handle JWT tokens from main website SSO
        if jwt_token and user_id_param:
            # For now, trust the JWT from main website and create/load user
            logger.info(f"🔐 SSO: Processing JWT token for user {user_id_param}")
            sso_user_id = f"sso_{user_id_param}"
            sso_email = email_param or f"sso_user_{user_id_param}@sukusuku.ai"
            sso_username = first_name_param or f"SSO_User_{user_id_param}"
            
            logger.info(f"🔍 SSO DEBUG: Params received - ID: {user_id_param}, Email: {email_param}, Name: {first_name_param}")

            # Check cache first
            cached_user = fast_sukusuku_integration.get_user_from_cache(sso_user_id)
            if cached_user:
                session['user_data'] = cached_user
                logger.info(f"✅ SSO: Cached user loaded - {cached_user['username']}")
                return cached_user
            
            with fast_sukusuku_integration.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, email, credits FROM users WHERE id = ? LIMIT 1", (sso_user_id,))
                existing_sso_user = cursor.fetchone()
                
                if existing_sso_user:
                    user_data = {
                        'user_id': existing_sso_user[0],
                        'username': existing_sso_user[1],
                        'email': existing_sso_user[2],
                        'credits': existing_sso_user[3],
                        'subscription_status': 'premium',
                        'profile_image': None,
                        'bio': f'{existing_sso_user[1]} - SSO from sukusuku.ai',
                        'website': 'https://sukusuku.ai',
                        'authenticated': True,
                        'original_credits': 300,  # Premium SSO users get more
                        'credits_used': 300 - existing_sso_user[3]
                    }
                    logger.info(f"✅ SSO: Existing user loaded - {existing_sso_user[1]}")
                else:
                    # Create new SSO user with proper error handling
                    try:
                        # Use timestamps as strings to avoid datatype issues
                        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute("""
                            INSERT INTO users (id, username, email, credits, subscription_status, bio, website, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (sso_user_id, sso_username, sso_email, 50, 'premium', f'{sso_username} - SSO from sukusuku.ai', 'https://sukusuku.ai', current_time, current_time))
                        logger.info(f"✅ SSO: Database insert successful for {sso_username}")
                    except Exception as db_error:
                        logger.error(f"SSO database error: {db_error}")
                        # Try simpler insert without timestamps
                        cursor.execute("""
                            INSERT INTO users (id, username, email, credits, subscription_status)
                            VALUES (?, ?, ?, ?, ?)
                        """, (sso_user_id, sso_username, sso_email, 50, 'premium'))
                    
                    user_data = {
                        'user_id': sso_user_id,
                        'username': sso_username,
                        'email': sso_email,
                        'credits': 50,
                        'subscription_status': 'premium',
                        'profile_image': None,
                        'bio': f'{sso_username} - SSO from sukusuku.ai',
                        'website': 'https://sukusuku.ai',
                        'authenticated': True,
                        'original_credits': 300,
                        'credits_used': 0
                    }
                    logger.info(f"✅ SSO: New user created - {sso_username} with 300 credits")
                
                # Cache and store
                fast_sukusuku_integration.cache_user(sso_user_id, user_data)
                session['user_data'] = user_data
                session['user_id'] = sso_user_id
                session.permanent = True
                return user_data

        # FAST PATH: Check session first (most common case)
        if 'user_data' in session and not any([jwt_token, user_id_param, email_param, dev_email_param]):
            stored_user = session['user_data']
            # Quick cache check
            cached_user = fast_sukusuku_integration.get_user_from_cache(stored_user['user_id'])
            if cached_user:
                return cached_user
            
            # Refresh credits from database (optimized query)
            try:
                with fast_sukusuku_integration.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT credits FROM users WHERE id = ? LIMIT 1", (stored_user['user_id'],))
                    result = cursor.fetchone()
                    if result:
                        stored_user['credits'] = result[0]
                        stored_user['credits_used'] = stored_user.get('original_credits', 250) - result[0]
                        fast_sukusuku_integration.cache_user(stored_user['user_id'], stored_user)
                
                return stored_user
            except:
                # If database is slow, return cached data
                return stored_user
        
        # STEP 2: Handle sukusuku.ai URL parameters
        if user_id_param and email_param and first_name_param and last_name_param:
            isolated_user_id = f"suku_{user_id_param}"
            username = f"{first_name_param}_{last_name_param}".replace(' ', '_')
            email = email_param
            
            # Check cache first
            cached_user = fast_sukusuku_integration.get_user_from_cache(isolated_user_id)
            if cached_user:
                session['user_data'] = cached_user
                return cached_user
            
            with fast_sukusuku_integration.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, email, credits FROM users WHERE id = ? LIMIT 1", (isolated_user_id,))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    user_data = {
                        'user_id': existing_user[0],
                        'username': existing_user[1],
                        'email': existing_user[2],
                        'credits': existing_user[3],
                        'subscription_status': 'premium',
                        'profile_image': None,
                        'bio': f'{existing_user[1]} - isolated from sukusuku.ai',
                        'website': 'https://sukusuku.ai',
                        'authenticated': True,
                        'original_credits': 250,
                        'credits_used': 250 - existing_user[3]
                    }
                else:
                    # Create new user quickly
                    cursor.execute("""
                        INSERT INTO users (id, username, email, credits, subscription_status, bio, website, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (isolated_user_id, username, email, 250, 'premium', f'{username} - isolated from sukusuku.ai', 'https://sukusuku.ai', datetime.now().isoformat(), datetime.now().isoformat()))
                    
                    user_data = {
                        'user_id': isolated_user_id,
                        'username': username,
                        'email': email,
                        'credits': 250,
                        'subscription_status': 'premium',
                        'profile_image': None,
                        'bio': f'{username} - isolated from sukusuku.ai',
                        'website': 'https://sukusuku.ai',
                        'authenticated': True,
                        'original_credits': 250,
                        'credits_used': 0
                    }
                
                # Cache and store
                fast_sukusuku_integration.cache_user(isolated_user_id, user_data)
                session['user_data'] = user_data
                session['user_id'] = isolated_user_id
                session.permanent = True
                return user_data
        
        # STEP 3: Developer access
        elif dev_email_param:
            dev_user_id = f"dev_{hashlib.md5(dev_email_param.encode()).hexdigest()[:8]}"
            dev_username = f"Developer_{dev_user_id[-4:]}"
            
            # Check cache
            cached_user = fast_sukusuku_integration.get_user_from_cache(dev_user_id)
            if cached_user:
                session['user_data'] = cached_user
                return cached_user
            
            with fast_sukusuku_integration.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, email, credits FROM users WHERE id = ? LIMIT 1", (dev_user_id,))
                existing_dev = cursor.fetchone()
                
                if existing_dev:
                    user_data = {
                        'user_id': existing_dev[0],
                        'username': existing_dev[1],
                        'email': existing_dev[2],
                        'credits': existing_dev[3],
                        'subscription_status': 'premium',
                        'profile_image': None,
                        'bio': f'{existing_dev[1]} - developer access',
                        'website': 'https://sukusuku.ai',
                        'authenticated': True,
                        'original_credits': 500,
                        'credits_used': 500 - existing_dev[3]
                    }
                else:
                    cursor.execute("""
                        INSERT INTO users (id, username, email, credits, subscription_status, bio, website, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (dev_user_id, dev_username, dev_email_param, 500, 'premium', f'{dev_username} - developer access', 'https://sukusuku.ai', datetime.now().isoformat(), datetime.now().isoformat()))
                    
                    user_data = {
                        'user_id': dev_user_id,
                        'username': dev_username,
                        'email': dev_email_param,
                        'credits': 500,
                        'subscription_status': 'premium',
                        'profile_image': None,
                        'bio': f'{dev_username} - developer access',
                        'website': 'https://sukusuku.ai',
                        'authenticated': True,
                        'original_credits': 500,
                        'credits_used': 0
                    }
                
                fast_sukusuku_integration.cache_user(dev_user_id, user_data)
                session['user_data'] = user_data
                session['user_id'] = dev_user_id
                session.permanent = True
                return user_data
        
        # STEP 4: Check session for existing authentication (no fallback to random users)
        if 'user_data' in session and session.get('authenticated'):
            cached_user = session.get('user_data')
            logger.info(f"✅ Using session user: {cached_user.get('username', 'Unknown')}")
            return cached_user
        
        # No authentication found - return None to indicate user needs to login
        logger.warning("⚠️ No authentication found - user should login from sukusuku.ai")
        return None
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        
        # PRIORITY: Check for SSO parameters first
        if request.args.get('jwt_token') and request.args.get('user_id'):
            logger.info("🚨 SSO: Database failed, using session-only SSO authentication")
            try:
                original_user_id = request.args.get('user_id')
                sso_user_id = int(original_user_id) if original_user_id.isdigit() else hash(original_user_id) % 2147483647
                first_name = request.args.get('first_name', 'SSO')
                last_name = request.args.get('last_name', 'User')
                sso_username = f"{first_name} {last_name}".strip()
                sso_email = request.args.get('email', 'sso@sukusuku.ai')
                
                # Create complete SSO user data
                user_data = {
                    'user_id': sso_user_id,
                    'username': sso_username,
                    'email': sso_email,
                    'credits': 50,
                    'subscription_status': 'premium',
                    'profile_image': None,
                    'bio': f'{sso_username} - SSO from sukusuku.ai',
                    'website': 'https://sukusuku.ai',
                    'authenticated': True,
                    'original_credits': 50,
                    'credits_used': 0
                }
                
                # Force session to use SSO user - keep user_id as string to avoid integer conversion
                session.clear()  # Clear any existing session data
                user_data['user_id'] = str(original_user_id)  # Keep as string to avoid SQLite INTEGER issues
                session['user_data'] = user_data
                session['user_id'] = str(original_user_id)
                session['sso_user'] = True
                session.permanent = True
                
                logger.info(f"✅ SSO Session-Only Authentication: {sso_username} ({sso_email}) with 50 credits")
                return user_data
            except Exception as sso_error:
                logger.error(f"SSO fallback error: {sso_error}")
        
        # Final fallback
        return {
            'user_id': 'error_fallback',
            'username': 'System_User',
            'email': 'system@penora.local',
            'credits': 1,
            'subscription_status': 'free',
            'authenticated': True,
            'original_credits': 1,
            'credits_used': 0
        }

# Compatibility functions
def get_current_sukusuku_user():
    return get_user_data()

def require_sukusuku_auth(func):
    return func

def deduct_credits(user_id, amount, description="Credit usage"):
    return fast_sukusuku_integration.deduct_credits(user_id, amount, description)

def init_shared_database():
    """Compatibility wrapper for app.py"""
    return fast_sukusuku_integration.init_database()

# Make the optimized integration available as sukusuku_integration for backward compatibility
sukusuku_integration = fast_sukusuku_integration

# Add missing methods for compatibility
sukusuku_integration.init_shared_database = init_shared_database
sukusuku_integration.get_db_connection = fast_sukusuku_integration.get_db_connection