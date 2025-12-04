#!/usr/bin/env python3
"""
Shared database manager for real-time credit synchronization
"""
import sqlite3
import logging
import os
from datetime import datetime

class SharedDBManager:
    """Manage shared users.db for real-time credit sync"""
    
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize shared database if it doesn't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    credits INTEGER DEFAULT 10,
                    google_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create transactions table for credit history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    type TEXT NOT NULL, -- 'purchase', 'deduction', 'bonus'
                    note TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Create generations table for Penora usage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    prompt TEXT NOT NULL,
                    content TEXT NOT NULL,
                    generation_type TEXT NOT NULL, -- 'single', 'story'
                    credits_used INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            conn.commit()
            conn.close()
            
            logging.info("Shared database initialized successfully")
            
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
    
    def create_test_user(self):
        """Create a test user for development"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if test user already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", ("test@sukusuku.ai",))
            if cursor.fetchone():
                logging.info("Test user already exists")
                conn.close()
                return
            
            # Create test user
            cursor.execute("""
                INSERT INTO users (username, email, credits, google_id)
                VALUES (?, ?, ?, ?)
            """, ("testuser", "test@sukusuku.ai", 50, "google_test_123"))
            
            conn.commit()
            conn.close()
            
            logging.info("Test user created: test@sukusuku.ai with 50 credits")
            
        except Exception as e:
            logging.error(f"Error creating test user: {e}")
    
    def get_user_credits(self, user_id):
        """Get real-time credits for user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else 0
            
        except Exception as e:
            logging.error(f"Error fetching credits: {e}")
            return 0
    
    def deduct_credits(self, user_id, amount, note=""):
        """Deduct credits from user account"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current credits
            cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            
            if not result or result[0] < amount:
                conn.close()
                return False
            
            new_credits = result[0] - amount
            
            # Update credits
            cursor.execute("""
                UPDATE users 
                SET credits = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (new_credits, user_id))
            
            # Log transaction
            cursor.execute("""
                INSERT INTO transactions (user_id, amount, type, note)
                VALUES (?, ?, 'deduction', ?)
            """, (user_id, amount, note))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Deducted {amount} credits from user {user_id}. New balance: {new_credits}")
            return True
            
        except Exception as e:
            logging.error(f"Error deducting credits: {e}")
            return False
    
    def add_credits(self, user_id, amount, note=""):
        """Add credits to user account"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current credits
            cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False
            
            new_credits = result[0] + amount
            
            # Update credits
            cursor.execute("""
                UPDATE users 
                SET credits = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (new_credits, user_id))
            
            # Log transaction
            cursor.execute("""
                INSERT INTO transactions (user_id, amount, type, note)
                VALUES (?, ?, 'purchase', ?)
            """, (user_id, amount, note))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Added {amount} credits to user {user_id}. New balance: {new_credits}")
            return True
            
        except Exception as e:
            logging.error(f"Error adding credits: {e}")
            return False
    
    def log_generation(self, user_id, prompt, content, generation_type, credits_used):
        """Log text generation in shared database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO generations (user_id, prompt, content, generation_type, credits_used)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, prompt, content, generation_type, credits_used))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Logged generation for user {user_id}: {generation_type}")
            return True
            
        except Exception as e:
            logging.error(f"Error logging generation: {e}")
            return False

# Global shared DB manager
shared_db = SharedDBManager("users.db")