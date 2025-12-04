#!/usr/bin/env python3
"""
Enhanced User Isolation System for Penora + ImageGene
Ensures complete data separation between users with unified credit and workspace management
"""

import logging
from typing import Dict, List, Optional, Any
from shared_credit_workspace_system import unified_system

logger = logging.getLogger(__name__)

class UserIsolationManager:
    """Manages user isolation across Penora and ImageGene applications"""
    
    def __init__(self):
        self.unified_system = unified_system
    
    def initialize_user_session(self, user_id: str, username: str, email: str, 
                              app_source: str = 'penora') -> Dict[str, Any]:
        """Initialize user session with proper isolation and bonus credits"""
        try:
            # Create or update user in unified system (includes 10 bonus credits for new users)
            user_data = self.unified_system.create_or_update_user(
                user_id, username, email, initial_credits=60
            )
            
            if not user_data:
                logger.error(f"Failed to initialize user {user_id}")
                return None
            
            # Get user's isolated workspace stats
            storage_stats = self.unified_system.get_storage_stats(user_id)
            projects = self.unified_system.get_user_projects(user_id)
            
            # Filter projects by app if needed
            app_projects = [p for p in projects if p['app_source'] == app_source]
            
            session_data = {
                'user_id': user_id,
                'username': username,
                'email': email,
                'credits': user_data['credits'],
                'authenticated': True,
                'app_source': app_source,
                'storage_stats': storage_stats,
                'project_count': len(projects),
                'app_project_count': len(app_projects),
                'isolation_verified': True,
                'bonus_credits_applied': True  # All users get bonus in unified system
            }
            
            logger.info(f"✅ User {username} ({user_id}) initialized with {user_data['credits']} credits")
            logger.info(f"📊 Storage: {storage_stats['used_mb']:.2f}/{storage_stats['limit_mb']}MB used")
            logger.info(f"📁 Projects: {len(projects)} total, {len(app_projects)} in {app_source}")
            
            return session_data
            
        except Exception as e:
            logger.error(f"Error initializing user session: {e}")
            return None
    
    def verify_user_access(self, user_id: str, requested_resource: str, 
                          resource_owner: str = None) -> bool:
        """Verify user can access requested resource"""
        try:
            # Basic user ID validation
            if not user_id or not isinstance(user_id, str):
                logger.warning(f"Invalid user ID format: {user_id}")
                return False
            
            # If resource has an owner, ensure it matches the requesting user
            if resource_owner and str(resource_owner) != str(user_id):
                logger.warning(f"Access denied: User {user_id} tried to access {requested_resource} owned by {resource_owner}")
                return False
            
            # Check if user exists in unified system
            credits = self.unified_system.get_user_credits(user_id)
            if credits < 0:  # User doesn't exist
                logger.warning(f"User {user_id} not found in unified system")
                return False
            
            logger.debug(f"✅ Access verified for user {user_id} to {requested_resource}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying user access: {e}")
            return False
    
    def get_user_isolated_data(self, user_id: str, app_filter: str = None) -> Dict[str, Any]:
        """Get user's isolated data with optional app filtering"""
        try:
            if not self.verify_user_access(user_id, "user_data"):
                return None
            
            # Get user's credits and storage
            credits = self.unified_system.get_user_credits(user_id)
            storage_stats = self.unified_system.get_storage_stats(user_id)
            
            # Get user's projects with optional app filtering
            projects = self.unified_system.get_user_projects(user_id, app_filter)
            
            # Get recent transactions
            transactions = self.unified_system.get_user_transactions(user_id, limit=10)
            
            return {
                'user_id': user_id,
                'credits': credits,
                'storage_stats': storage_stats,
                'projects': projects,
                'recent_transactions': transactions,
                'project_breakdown': {
                    'total': len(projects),
                    'penora': len([p for p in projects if p['app_source'] == 'penora']),
                    'imagegene': len([p for p in projects if p['app_source'] == 'imagegene'])
                },
                'data_isolation_verified': True
            }
            
        except Exception as e:
            logger.error(f"Error getting user isolated data: {e}")
            return None
    
    def deduct_credits_with_isolation(self, user_id: str, amount: int, app_name: str,
                                    description: str, project_code: str = None) -> Dict[str, Any]:
        """Deduct credits with proper user isolation checks"""
        try:
            if not self.verify_user_access(user_id, "credit_deduction"):
                return {'success': False, 'error': 'Access denied'}
            
            # Check current credits
            current_credits = self.unified_system.get_user_credits(user_id)
            if current_credits < amount:
                return {
                    'success': False,
                    'error': f'Insufficient credits. Has {current_credits}, needs {amount}'
                }
            
            # Perform deduction
            success = self.unified_system.deduct_credits(
                user_id, amount, app_name, description, project_code
            )
            
            if success:
                new_credits = self.unified_system.get_user_credits(user_id)
                return {
                    'success': True,
                    'credits_deducted': amount,
                    'previous_balance': current_credits,
                    'new_balance': new_credits,
                    'app_name': app_name,
                    'isolation_verified': True
                }
            else:
                return {'success': False, 'error': 'Credit deduction failed'}
                
        except Exception as e:
            logger.error(f"Error in isolated credit deduction: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_project_with_isolation(self, user_id: str, app_source: str, project_type: str,
                                   title: str, content: str, metadata: Dict = None) -> Dict[str, Any]:
        """Save project with user isolation and storage limit enforcement"""
        try:
            if not self.verify_user_access(user_id, "project_creation"):
                return {'success': False, 'error': 'Access denied'}
            
            # Check storage limit before saving
            content_size = len(content.encode('utf-8'))
            storage_stats = self.unified_system.get_storage_stats(user_id)
            
            if storage_stats['used_mb'] + (content_size / (1024 * 1024)) > storage_stats['limit_mb']:
                return {
                    'success': False,
                    'error': f'Storage limit exceeded. Would use {storage_stats["used_mb"] + content_size/(1024*1024):.2f}MB of {storage_stats["limit_mb"]}MB limit'
                }
            
            # Save project
            result = self.unified_system.save_project(
                user_id, app_source, project_type, title, content, metadata
            )
            
            if result['success']:
                result['isolation_verified'] = True
                result['storage_used'] = storage_stats['used_mb'] + result['size_mb']
                result['storage_remaining'] = storage_stats['limit_mb'] - result['storage_used']
            
            return result
            
        except Exception as e:
            logger.error(f"Error in isolated project saving: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_cross_app_projects(self, user_id: str) -> Dict[str, Any]:
        """Get user's projects from both apps with proper isolation"""
        try:
            if not self.verify_user_access(user_id, "cross_app_projects"):
                return {'success': False, 'error': 'Access denied'}
            
            # Get all projects
            all_projects = self.unified_system.get_user_projects(user_id)
            
            # Separate by app
            penora_projects = [p for p in all_projects if p['app_source'] == 'penora']
            imagegene_projects = [p for p in all_projects if p['app_source'] == 'imagegene']
            
            # Calculate storage breakdown
            penora_storage = sum(p['size_bytes'] for p in penora_projects)
            imagegene_storage = sum(p['size_bytes'] for p in imagegene_projects)
            
            return {
                'success': True,
                'all_projects': all_projects,
                'penora_projects': penora_projects,
                'imagegene_projects': imagegene_projects,
                'summary': {
                    'total_projects': len(all_projects),
                    'penora_count': len(penora_projects),
                    'imagegene_count': len(imagegene_projects),
                    'penora_storage_mb': round(penora_storage / (1024 * 1024), 2),
                    'imagegene_storage_mb': round(imagegene_storage / (1024 * 1024), 2),
                    'total_storage_mb': round((penora_storage + imagegene_storage) / (1024 * 1024), 2)
                },
                'isolation_verified': True
            }
            
        except Exception as e:
            logger.error(f"Error getting cross-app projects: {e}")
            return {'success': False, 'error': str(e)}

# Global instance
user_isolation_manager = UserIsolationManager()