"""
Cross-App Integration Service for Penora
Enables external applications to access user's Penora workspace
"""

import logging
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class CrossAppIntegration:
    def __init__(self, base_url: str = None):
        """Initialize cross-app integration service"""
        self.base_url = base_url or "https://e1e07499-d292-4451-b55b-9647412a4052-00-3cl7v3i6gfvjy.spock.replit.dev"
        self.session = requests.Session()
        
    def authenticate_user(self, jwt_token: str, user_id: str, email: str = None, 
                         first_name: str = None, last_name: str = None) -> Dict[str, Any]:
        """Authenticate user for cross-app access"""
        try:
            auth_data = {
                'jwt_token': jwt_token,
                'user_id': user_id,
                'email': email,
                'first_name': first_name,
                'last_name': last_name
            }
            
            response = self.session.post(
                f"{self.base_url}/api/cross-app/auth",
                json=auth_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logging.info(f"Cross-app auth successful for user {user_id}")
                    return result
                else:
                    logging.error(f"Cross-app auth failed: {result.get('error')}")
                    return {'success': False, 'error': result.get('error')}
            else:
                logging.error(f"Cross-app auth HTTP error: {response.status_code}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            logging.error(f"Cross-app authentication error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_projects(self, jwt_token: str, user_id: str) -> Dict[str, Any]:
        """Get user's Penora projects for external app"""
        try:
            # First authenticate
            auth_result = self.authenticate_user(jwt_token, user_id)
            if not auth_result.get('success'):
                return auth_result
            
            # Get projects
            response = self.session.get(
                f"{self.base_url}/api/user-projects",
                params={'jwt_token': jwt_token, 'user_id': user_id},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logging.info(f"Retrieved {len(result.get('projects', []))} projects for user {user_id}")
                return result
            else:
                logging.error(f"Get projects HTTP error: {response.status_code}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            logging.error(f"Get user projects error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_project_content(self, project_code: str, jwt_token: str, user_id: str) -> Dict[str, Any]:
        """Get specific project content"""
        try:
            # First authenticate
            auth_result = self.authenticate_user(jwt_token, user_id)
            if not auth_result.get('success'):
                return auth_result
            
            # Get project details
            response = self.session.get(
                f"{self.base_url}/api/project/{project_code}",
                params={'jwt_token': jwt_token, 'user_id': user_id},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logging.info(f"Retrieved project {project_code} for user {user_id}")
                return result
            else:
                logging.error(f"Get project content HTTP error: {response.status_code}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            logging.error(f"Get project content error: {e}")
            return {'success': False, 'error': str(e)}
    
    def format_projects_for_dropdown(self, projects_response: Dict[str, Any]) -> List[Dict[str, str]]:
        """Format projects for dropdown display in external apps"""
        try:
            if not projects_response.get('success'):
                return []
            
            projects = projects_response.get('projects', [])
            formatted = []
            
            for project in projects:
                # Create display title with word count
                title = project.get('title', 'Untitled Project')
                word_count = project.get('word_count', 0)
                display_title = f"{title} ({word_count} words)"
                
                formatted.append({
                    'id': project.get('id'),
                    'title': display_title,
                    'content': project.get('content', ''),
                    'original_title': title,
                    'word_count': word_count,
                    'created_at': project.get('created_at'),
                    'size': project.get('size', 0)
                })
            
            # Sort by creation date (newest first)
            formatted.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return formatted
            
        except Exception as e:
            logging.error(f"Format projects error: {e}")
            return []

# Global instance for easy import
cross_app_service = CrossAppIntegration()

def get_penora_projects_for_external_app(jwt_token: str, user_id: str) -> List[Dict[str, str]]:
    """Convenience function for external apps to get formatted project list"""
    try:
        # Get projects
        projects_response = cross_app_service.get_user_projects(jwt_token, user_id)
        
        # Format for dropdown
        return cross_app_service.format_projects_for_dropdown(projects_response)
        
    except Exception as e:
        logging.error(f"External app projects fetch error: {e}")
        return []

def get_penora_project_content_for_external_app(project_code: str, jwt_token: str, user_id: str) -> Dict[str, Any]:
    """Convenience function for external apps to get project content"""
    try:
        return cross_app_service.get_project_content(project_code, jwt_token, user_id)
        
    except Exception as e:
        logging.error(f"External app project content error: {e}")
        return {'success': False, 'error': str(e)}