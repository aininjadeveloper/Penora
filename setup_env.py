#!/usr/bin/env python3
"""
Setup script to create .env file for PenoraWriter
This script generates secure keys and creates a .env file
"""

import secrets
import os
from pathlib import Path

def generate_secret_key():
    """Generate a secure random key"""
    return secrets.token_hex(32)

def create_env_file():
    """Create .env file with generated keys and placeholders"""
    env_path = Path('.env')
    
    if env_path.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (yes/no): ").lower()
        if response != 'yes':
            print("❌ Aborted. Existing .env file preserved.")
            return
    
    # Generate secure keys
    secret_key = generate_secret_key()
    session_secret = generate_secret_key()
    jwt_secret = generate_secret_key()
    penora_api_key = generate_secret_key()
    
    env_content = f"""# PenoraWriter Environment Variables
# Generated automatically - Replace placeholder values with your actual API keys

# ============================================
# REQUIRED - Core Configuration
# ============================================
SECRET_KEY={secret_key}
SESSION_SECRET={session_secret}
JWT_SECRET_KEY={jwt_secret}

# Database Configuration (SQLite for development)
DATABASE_URL=sqlite:///users.db

# ============================================
# REQUIRED - AI Service
# ============================================
# TODO: Get your API key from https://deepinfra.com and replace this value
DEEPINFRA_API_KEY=your-deepinfra-api-key-here

# ============================================
# OPTIONAL - Google OAuth
# ============================================
# TODO: Get from Google Cloud Console: https://console.cloud.google.com/apis/credentials
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=

# ============================================
# OPTIONAL - Payment Processing (Razorpay)
# ============================================
# TODO: Get from Razorpay Dashboard: https://dashboard.razorpay.com
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=

# ============================================
# OPTIONAL - External Integrations
# ============================================
SUKUSUKU_MAIN_URL=https://suku-suku-site-developeraim.replit.app
PENORA_API_KEY={penora_api_key}
AUTO_LOGIN=false
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
        print("\n📝 Next steps:")
        print("   1. Edit .env file and add your DEEPINFRA_API_KEY")
        print("   2. (Optional) Add Google OAuth credentials if needed")
        print("   3. (Optional) Add Razorpay credentials if needed")
        print("\n⚠️  IMPORTANT: Never commit .env file to version control!")
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

if __name__ == "__main__":
    print("🚀 PenoraWriter Environment Setup")
    print("=" * 50)
    create_env_file()

