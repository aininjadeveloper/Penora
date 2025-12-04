#!/usr/bin/env python3
"""
Authentic SukuSuku.ai JWT Authentication System
Handles proper JWT token validation and user data extraction
"""

import jwt
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from flask import request, session

logger = logging.getLogger(__name__)

class SukusukuJWTAuth:
    """Authentic JWT authentication for sukusuku.ai integration"""
    
    def __init__(self):
        self.jwt_secret = "sukusuku-ai-secret-key-2025"
        self.token_expiry_hours = 1  # App tokens: 1 hour
        self.general_token_days = 7  # General tokens: 7 days
    
    def decode_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate JWT token from sukusuku.ai"""
        try:
            # Decode JWT token with the official sukusuku.ai secret
            decoded_token = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=["HS256"]
            )
            
            logger.info(f"✅ JWT DECODED: Valid token for user {decoded_token.get('userId')}")
            return decoded_token
            
        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ JWT EXPIRED: Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"❌ JWT INVALID: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ JWT ERROR: {e}")
            return None
    
    def extract_user_from_jwt(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user data from decoded JWT token"""
        try:
            # Get user ID - handle both string and numeric formats
            user_id = token_data.get('userId') or token_data.get('user_id')
            if not user_id:
                logger.error("❌ JWT missing user ID")
                return None
            
            # Get email - required field
            email = token_data.get('email')
            if not email:
                logger.error("❌ JWT missing email")
                return None
            
            # Build username from first/last name or use email
            first_name = token_data.get('firstName') or token_data.get('first_name') or ''
            last_name = token_data.get('lastName') or token_data.get('last_name') or ''
            username = f"{first_name} {last_name}".strip()
            if not username:
                # Fallback to email username part
                username = email.split('@')[0] if '@' in email else f"User_{str(user_id)[:8]}"
            
            # Get credits from token or use default
            credits = token_data.get('penoraCredits') or token_data.get('penora_credits') or token_data.get('credits') or 50
            
            # Map JWT fields to consistent user data structure
            user_data = {
                'user_id': str(user_id),  # Ensure string format
                'email': email,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'profile_image': token_data.get('profileImageUrl') or token_data.get('profile_image'),
                'credits': int(credits),
                'penora_credits': token_data.get('penoraCredits', credits),
                'imagegene_credits': token_data.get('imagegeneCredits', 50),
                'app_name': token_data.get('appName', 'penora'),
                'subscription_status': token_data.get('subscriptionStatus', 'premium'),
                'authenticated': True,
                'auth_method': 'jwt',
                'token_issued_at': token_data.get('iat'),
                'bio': f"Authenticated via sukusuku.ai",
                'website': 'https://sukusuku.ai',
                'original_credits': int(credits),
                'credits_used': 0
            }
            
            logger.info(f"✅ JWT USER EXTRACTED: {user_data['username']} ({user_data['email']}) with {user_data['credits']} credits")
            return user_data
            
        except Exception as e:
            logger.error(f"❌ JWT EXTRACTION ERROR: {e}")
            return None
    
    def extract_user_from_url_params(self, request_args: Dict) -> Optional[Dict[str, Any]]:
        """Extract user data from URL parameters (SSO format)"""
        try:
            # Check if required parameters are present
            user_id = request_args.get('user_id')
            email = request_args.get('email')
            first_name = request_args.get('first_name')
            last_name = request_args.get('last_name')
            
            # user_id and email are required
            if not user_id or not email:
                logger.debug(f"⚠️ Missing required params: user_id={bool(user_id)}, email={bool(email)}")
                return None
            
            # Build username from first/last name or use email
            username = f"{first_name or ''} {last_name or ''}".strip()
            if not username:
                # Fallback to email username part
                username = email.split('@')[0] if '@' in email else f"User_{str(user_id)[:8]}"
            
            # Get credits from URL params or use default
            credits = int(request_args.get('credits', 50))
            
            user_data = {
                'user_id': str(user_id),  # Ensure string format
                'email': email,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'profile_image': request_args.get('profile_image'),
                'credits': credits,
                'subscription_status': request_args.get('subscription_status', 'premium'),
                'authenticated': True,
                'auth_method': 'url_params',
                'bio': f"SSO from sukusuku.ai",
                'website': 'https://sukusuku.ai',
                'original_credits': credits,
                'credits_used': 0
            }
            
            logger.info(f"✅ SSO USER EXTRACTED: {username} ({email}) authenticated via URL parameters with {credits} credits")
            return user_data
            
        except Exception as e:
            logger.error(f"❌ URL PARAM EXTRACTION ERROR: {e}")
            return None
    
    def authenticate_user(self, request_obj=None) -> Optional[Dict[str, Any]]:
        """Main authentication method - tries JWT first, then URL parameters"""
        if not request_obj:
            request_obj = request
        
        try:
            # Method 1: JWT Token Authentication
            jwt_token = request_obj.args.get('jwt_token') or request_obj.headers.get('Authorization')
            if jwt_token:
                # Handle Bearer token format
                if jwt_token.startswith('Bearer '):
                    jwt_token = jwt_token[7:]
                
                token_data = self.decode_jwt_token(jwt_token)
                if token_data:
                    user_data = self.extract_user_from_jwt(token_data)
                    if user_data:
                        return user_data
            
            # Method 2: URL Parameters Authentication (SSO)
            user_data = self.extract_user_from_url_params(dict(request_obj.args))
            if user_data:
                return user_data
            
            logger.info("ℹ️ No valid JWT token or URL parameters found")
            return None
            
        except Exception as e:
            logger.error(f"❌ AUTHENTICATION ERROR: {e}")
            return None
    
    def create_user_session(self, user_data: Dict[str, Any]) -> bool:
        """Create Flask session for authenticated user"""
        try:
            # Clear any existing session
            session.clear()
            
            # Set user session data
            session['user_data'] = user_data
            session['user_id'] = user_data['user_id']
            session['authenticated'] = True
            session['auth_method'] = user_data.get('auth_method', 'unknown')
            session['sukusuku_user'] = True
            session.permanent = True
            
            # Initialize user-specific credits for isolation
            user_session_key = f"user_credits_{user_data['user_id']}"
            session[user_session_key] = user_data['credits']
            
            logger.info(f"✅ SESSION CREATED: {user_data['username']} authenticated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ SESSION CREATION ERROR: {e}")
            return False

# Global instance
sukusuku_jwt_auth = SukusukuJWTAuth()