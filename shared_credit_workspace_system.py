#!/usr/bin/env python3
"""
Unified Credit and Workspace System for Penora + ImageGene Integration
Provides shared credits, 1MB storage, and merged workspace across both apps
"""

import sqlite3
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)

class UnifiedCreditWorkspaceSystem:
    """Unified system for credits and workspace management across Penora and ImageGene"""
    
    def __init__(self, db_path="unified_system.db"):
        self.db_path = db_path
        self._db_lock = threading.Lock()
        self.MAX_STORAGE_MB = 1  # 1MB storage limit per user across both apps
        self.MAX_STORAGE_BYTES = self.MAX_STORAGE_MB * 1024 * 1024
        self.init_database()
    
    @contextmanager
    def get_db_connection(self):
        """Get database connection with proper locking"""
        conn = None
        try:
            with self._db_lock:
                conn = sqlite3.connect(
                    self.db_path,
                    timeout=10,
                    check_same_thread=False
                )
                conn.execute('PRAGMA foreign_keys=ON')
                conn.execute('PRAGMA journal_mode=WAL')
                yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def init_database(self):
        """Initialize unified database schema"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Unified user table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS unified_users (
                        user_id TEXT PRIMARY KEY,
                        username TEXT NOT NULL,
                        email TEXT NOT NULL,
                        credits INTEGER DEFAULT 50,
                        subscription_status TEXT DEFAULT 'premium',
                        profile_image TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        storage_used_bytes INTEGER DEFAULT 0,
                        storage_limit_bytes INTEGER DEFAULT 1048576
                    )
                """)
                
                # Unified projects table (supports both Penora and ImageGene)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS unified_projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        project_code TEXT UNIQUE NOT NULL,
                        app_source TEXT NOT NULL,  -- 'penora' or 'imagegene'
                        project_type TEXT NOT NULL,  -- 'text', 'image', 'ai_art', etc.
                        title TEXT NOT NULL,
                        content TEXT,
                        metadata TEXT,  -- JSON for app-specific data
                        file_size_bytes INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        is_deleted BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (user_id) REFERENCES unified_users(user_id)
                    )
                """)
                
                # Unified credit transactions
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS unified_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        app_name TEXT NOT NULL,  -- 'penora' or 'imagegene'
                        transaction_type TEXT NOT NULL,  -- 'used', 'purchased', 'bonus'
                        amount INTEGER NOT NULL,
                        description TEXT,
                        project_code TEXT,  -- Link to project if applicable
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES unified_users(user_id)
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_user_id ON unified_projects(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_app_source ON unified_projects(app_source)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON unified_transactions(user_id)")
                
                conn.commit()
                logger.info("✅ Unified database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def create_or_update_user(self, user_id: str, username: str, email: str, 
                             initial_credits: int = 60) -> Dict[str, Any]:
        """Create or update user in unified system"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute("SELECT credits, storage_used_bytes FROM unified_users WHERE user_id = ?", (user_id,))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    # Update existing user
                    cursor.execute("""
                        UPDATE unified_users 
                        SET username = ?, email = ?, updated_at = ?
                        WHERE user_id = ?
                    """, (username, email, datetime.now().isoformat(), user_id))
                    
                    credits, storage_used = existing_user
                else:
                    # Create new user with bonus credits
                    cursor.execute("""
                        INSERT INTO unified_users 
                        (user_id, username, email, credits, storage_used_bytes, storage_limit_bytes)
                        VALUES (?, ?, ?, ?, 0, ?)
                    """, (user_id, username, email, initial_credits, self.MAX_STORAGE_BYTES))
                    
                    # Log bonus credit transaction for new users
                    cursor.execute("""
                        INSERT INTO unified_transactions 
                        (user_id, app_name, transaction_type, amount, description)
                        VALUES (?, 'system', 'bonus', ?, 'Welcome bonus - 10 Ku coins')
                    """, (user_id, 10))
                    
                    credits = initial_credits
                    storage_used = 0
                
                conn.commit()
                
                return {
                    'user_id': user_id,
                    'username': username,
                    'email': email,
                    'credits': credits,
                    'storage_used_mb': round(storage_used / (1024 * 1024), 2),
                    'storage_limit_mb': self.MAX_STORAGE_MB,
                    'storage_available_mb': round((self.MAX_STORAGE_BYTES - storage_used) / (1024 * 1024), 2)
                }
                
        except Exception as e:
            logger.error(f"Error creating/updating user: {e}")
            return None
    
    def get_user_credits(self, user_id: str) -> int:
        """Get user's current credit balance"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT credits FROM unified_users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting user credits: {e}")
            return 0
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get complete user information from unified system"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, username, email, credits, storage_used_bytes, 
                           storage_limit_bytes, subscription_status, created_at, updated_at
                    FROM unified_users WHERE user_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'user_id': result[0],
                        'username': result[1],
                        'email': result[2],
                        'credits': result[3],
                        'storage_used_bytes': result[4],
                        'storage_limit_bytes': result[5],
                        'storage_used_mb': round(result[4] / (1024 * 1024), 2),
                        'storage_limit_mb': round(result[5] / (1024 * 1024), 2),
                        'storage_available_mb': round((result[5] - result[4]) / (1024 * 1024), 2),
                        'subscription_status': result[6],
                        'created_at': result[7],
                        'updated_at': result[8]
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def deduct_credits(self, user_id: str, amount: int, app_name: str, 
                      description: str, project_code: str = None) -> bool:
        """Deduct credits from user account with unified tracking"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get current credits
                cursor.execute("SELECT credits FROM unified_users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                
                if not result or result[0] < amount:
                    return False
                
                current_credits = result[0]
                new_credits = current_credits - amount
                
                # Update credits
                cursor.execute("""
                    UPDATE unified_users 
                    SET credits = ?, updated_at = ?
                    WHERE user_id = ?
                """, (new_credits, datetime.now().isoformat(), user_id))
                
                # Log transaction
                cursor.execute("""
                    INSERT INTO unified_transactions 
                    (user_id, app_name, transaction_type, amount, description, project_code)
                    VALUES (?, ?, 'used', ?, ?, ?)
                """, (user_id, app_name, -amount, description, project_code))
                
                conn.commit()
                logger.info(f"✅ Deducted {amount} credits from {user_id} for {app_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error deducting credits: {e}")
            return False
    
    def add_credits(self, user_id: str, amount: int, transaction_type: str = 'purchased',
                   description: str = "Credit purchase") -> bool:
        """Add credits to user account"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Update credits
                cursor.execute("""
                    UPDATE unified_users 
                    SET credits = credits + ?, updated_at = ?
                    WHERE user_id = ?
                """, (amount, datetime.now().isoformat(), user_id))
                
                # Log transaction
                cursor.execute("""
                    INSERT INTO unified_transactions 
                    (user_id, app_name, transaction_type, amount, description)
                    VALUES (?, 'system', ?, ?, ?)
                """, (user_id, transaction_type, amount, description))
                
                conn.commit()
                logger.info(f"✅ Added {amount} credits to {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding credits: {e}")
            return False
    
    def standardize_all_users_to_50_credits(self) -> Dict[str, Any]:
        """Reset all users in unified system to exactly 50 credits"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get all users
                cursor.execute("SELECT user_id, username, credits FROM unified_users")
                users = cursor.fetchall()
                
                updated_users = []
                for user_id, username, current_credits in users:
                    if current_credits != 50:
                        # Update to 50 credits
                        cursor.execute("""
                            UPDATE unified_users 
                            SET credits = 50, updated_at = ?
                            WHERE user_id = ?
                        """, (datetime.now().isoformat(), user_id))
                        
                        # Log the standardization transaction
                        cursor.execute("""
                            INSERT INTO unified_transactions 
                            (user_id, app_name, transaction_type, amount, description)
                            VALUES (?, 'system', 'adjustment', ?, ?)
                        """, (user_id, 50 - current_credits, f'Credit standardization: {current_credits} → 50'))
                        
                        updated_users.append({
                            'user_id': user_id,
                            'username': username,
                            'old_credits': current_credits,
                            'new_credits': 50
                        })
                
                conn.commit()
                logger.info(f"✅ STANDARDIZED: Updated {len(updated_users)} users to 50 credits")
                
                return {
                    'success': True,
                    'users_updated': len(updated_users),
                    'updated_users': updated_users,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error standardizing credits: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_project(self, user_id: str, app_source: str, project_type: str,
                    title: str, content: str, metadata: Dict = None) -> Dict[str, Any]:
        """Save project to unified workspace"""
        try:
            # Calculate content size
            content_size = len(content.encode('utf-8'))
            
            # Check storage limit
            if not self._check_storage_limit(user_id, content_size):
                return {
                    'success': False,
                    'error': f'Storage limit exceeded. Maximum {self.MAX_STORAGE_MB}MB allowed.'
                }
            
            # Generate unique project code
            project_code = self._generate_project_code()
            
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Save project
                cursor.execute("""
                    INSERT INTO unified_projects 
                    (user_id, project_code, app_source, project_type, title, content, metadata, file_size_bytes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, project_code, app_source, project_type, title, content, 
                     json.dumps(metadata or {}), content_size))
                
                # Update user storage
                cursor.execute("""
                    UPDATE unified_users 
                    SET storage_used_bytes = storage_used_bytes + ?
                    WHERE user_id = ?
                """, (content_size, user_id))
                
                conn.commit()
                
                return {
                    'success': True,
                    'project_code': project_code,
                    'title': title,
                    'size_mb': round(content_size / (1024 * 1024), 2)
                }
                
        except Exception as e:
            logger.error(f"Error saving project: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_projects(self, user_id: str, app_filter: str = None) -> List[Dict[str, Any]]:
        """Get user's projects with optional app filtering"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                if app_filter:
                    query = """
                        SELECT project_code, app_source, project_type, title, content, 
                               metadata, file_size_bytes, created_at, updated_at
                        FROM unified_projects 
                        WHERE user_id = ? AND app_source = ? AND is_deleted = FALSE
                        ORDER BY updated_at DESC
                    """
                    cursor.execute(query, (user_id, app_filter))
                else:
                    query = """
                        SELECT project_code, app_source, project_type, title, content, 
                               metadata, file_size_bytes, created_at, updated_at
                        FROM unified_projects 
                        WHERE user_id = ? AND is_deleted = FALSE
                        ORDER BY updated_at DESC
                    """
                    cursor.execute(query, (user_id,))
                
                projects = []
                for row in cursor.fetchall():
                    code, app_source, project_type, title, content, metadata_json, size, created, updated = row
                    
                    try:
                        metadata = json.loads(metadata_json) if metadata_json else {}
                    except:
                        metadata = {}
                    
                    projects.append({
                        'code': code,
                        'app_source': app_source,
                        'project_type': project_type,
                        'title': title,
                        'content': content,
                        'metadata': metadata,
                        'size_bytes': size,
                        'size_mb': round(size / (1024 * 1024), 2),
                        'created_at': created,
                        'updated_at': updated,
                        'word_count': len(content.split()) if content else 0
                    })
                
                return projects
                
        except Exception as e:
            logger.error(f"Error getting user projects: {e}")
            return []
    
    def get_project_by_code(self, user_id: str, project_code: str) -> Dict[str, Any]:
        """Get specific project by code"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT project_code, app_source, project_type, title, content, 
                           metadata, file_size_bytes, created_at, updated_at
                    FROM unified_projects 
                    WHERE user_id = ? AND project_code = ? AND is_deleted = FALSE
                """, (user_id, project_code))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                code, app_source, project_type, title, content, metadata_json, size, created, updated = row
                
                try:
                    metadata = json.loads(metadata_json) if metadata_json else {}
                except:
                    metadata = {}
                
                return {
                    'code': code,
                    'app_source': app_source,
                    'project_type': project_type,
                    'title': title,
                    'content': content,
                    'metadata': metadata,
                    'size_bytes': size,
                    'size_mb': round(size / (1024 * 1024), 2),
                    'created_at': created,
                    'updated_at': updated,
                    'word_count': len(content.split()) if content else 0
                }
                
        except Exception as e:
            logger.error(f"Error getting project by code: {e}")
            return None
    
    def get_user_transactions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's transaction history across both apps"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT app_name, transaction_type, amount, description, 
                           project_code, created_at
                    FROM unified_transactions 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (user_id, limit))
                
                transactions = []
                for row in cursor.fetchall():
                    app_name, trans_type, amount, desc, project_code, created = row
                    transactions.append({
                        'app_name': app_name,
                        'transaction_type': trans_type,
                        'amount': amount,
                        'description': desc,
                        'project_code': project_code,
                        'created_at': created
                    })
                
                return transactions
                
        except Exception as e:
            logger.error(f"Error getting user transactions: {e}")
            return []
    
    def get_storage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user's storage statistics"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT storage_used_bytes, storage_limit_bytes
                    FROM unified_users 
                    WHERE user_id = ?
                """, (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return {'used_mb': 0, 'limit_mb': self.MAX_STORAGE_MB, 'available_mb': self.MAX_STORAGE_MB}
                
                used_bytes, limit_bytes = result
                used_mb = round(used_bytes / (1024 * 1024), 2)
                limit_mb = round(limit_bytes / (1024 * 1024), 2)
                available_mb = round((limit_bytes - used_bytes) / (1024 * 1024), 2)
                
                return {
                    'used_mb': used_mb,
                    'limit_mb': limit_mb,
                    'available_mb': max(0, available_mb),
                    'usage_percentage': round((used_bytes / limit_bytes) * 100, 1) if limit_bytes > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {'used_mb': 0, 'limit_mb': self.MAX_STORAGE_MB, 'available_mb': self.MAX_STORAGE_MB}
    
    def _check_storage_limit(self, user_id: str, additional_bytes: int) -> bool:
        """Check if user can store additional content"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT storage_used_bytes, storage_limit_bytes
                    FROM unified_users 
                    WHERE user_id = ?
                """, (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return additional_bytes <= self.MAX_STORAGE_BYTES
                
                used_bytes, limit_bytes = result
                return (used_bytes + additional_bytes) <= limit_bytes
                
        except Exception as e:
            logger.error(f"Error checking storage limit: {e}")
            return False
    
    def _generate_project_code(self) -> str:
        """Generate unique 6-character project code"""
        import string
        import random
        
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
            # Check if code already exists
            try:
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM unified_projects WHERE project_code = ?", (code,))
                    if cursor.fetchone()[0] == 0:
                        return code
            except:
                continue
    
    def give_bonus_credits_to_all_users(self, bonus_amount: int = 10) -> Dict[str, Any]:
        """Give bonus credits to all existing users"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get all existing users
                cursor.execute("SELECT user_id, username, credits FROM unified_users")
                users = cursor.fetchall()
                
                updated_count = 0
                for user_id, username, current_credits in users:
                    # Add bonus credits
                    new_credits = current_credits + bonus_amount
                    cursor.execute("""
                        UPDATE unified_users 
                        SET credits = ?, updated_at = ?
                        WHERE user_id = ?
                    """, (new_credits, datetime.now().isoformat(), user_id))
                    
                    # Log bonus transaction
                    cursor.execute("""
                        INSERT INTO unified_transactions 
                        (user_id, app_name, transaction_type, amount, description)
                        VALUES (?, 'system', 'bonus', ?, 'Universal bonus - 10 Ku coins for all users')
                    """, (user_id, bonus_amount))
                    
                    updated_count += 1
                    logger.info(f"✅ Gave {bonus_amount} bonus credits to {username} ({user_id})")
                
                conn.commit()
                
                return {
                    'success': True,
                    'users_updated': updated_count,
                    'bonus_amount': bonus_amount,
                    'total_credits_distributed': updated_count * bonus_amount
                }
                
        except Exception as e:
            logger.error(f"Error giving bonus credits: {e}")
            return {'success': False, 'error': str(e)}

# Global instance
unified_system = UnifiedCreditWorkspaceSystem()