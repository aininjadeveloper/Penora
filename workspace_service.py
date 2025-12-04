"""
Workspace Service for My Workspace functionality
Handles all workspace operations with security and storage management
"""
from app import db
from datetime import datetime
from flask import flash
import logging

# Import models at module level to avoid circular imports
from models import WorkspaceProject, User

logger = logging.getLogger(__name__)

class WorkspaceService:
    """Service class for managing user workspace projects"""
    
    @staticmethod
    def save_generation(user_id, title, content, generation_type='single'):
        """
        Save a new generation to user's workspace
        Returns: (success: bool, project: WorkspaceProject|None, message: str)
        """
        try:
            # Calculate storage for sukusuku.ai users without requiring PostgreSQL User model
            total_storage_bytes = db.session.query(db.func.sum(WorkspaceProject.storage_size)).filter(
                WorkspaceProject.user_id == str(user_id),
                WorkspaceProject.is_deleted == False
            ).scalar() or 0
            
            storage_used_mb = total_storage_bytes / (1024 * 1024)
            
            # Calculate new content storage size
            text_size = len(title.encode('utf-8')) + len(content.encode('utf-8')) + 1024  # 1KB overhead
            content_size_mb = text_size / (1024 * 1024)
            
            # Set 1MB storage limit for all new users
            if storage_used_mb + content_size_mb > 1.0:
                available_mb = max(0, 1.0 - storage_used_mb)
                return False, None, f"Storage limit exceeded. Used: {storage_used_mb:.2f}MB, Available: {available_mb:.2f}MB (1MB limit)"
            
            # Create new workspace project
            project = WorkspaceProject(
                user_id=str(user_id),
                project_title=title,
                generation_text=content
            )
            
            db.session.add(project)
            db.session.commit()
            
            logging.info(f"Saved generation '{title}' for user {user_id}, code: {project.code}")
            return True, project, f"Project saved successfully! Code: {project.code}"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving generation: {e}")
            return False, None, "Error saving project. Please try again."
    
    @staticmethod
    def get_user_projects(user_id):
        """Get all active workspace projects for a user"""
        try:
            # CRITICAL FIX: Ensure proper user isolation
            logger.info(f"🔍 WORKSPACE: Getting projects for user_id: {user_id}")
            
            projects = WorkspaceProject.query.filter_by(
                user_id=str(user_id),
                is_deleted=False
            ).order_by(WorkspaceProject.updated_at.desc()).all()
            
            # DEBUG: Log what projects were found
            logger.info(f"📁 Found {len(projects)} projects for user {user_id}")
            
            # If user has no projects, create a clean workspace (don't show other users' projects)
            if not projects:
                logger.info(f"✅ Clean workspace for new user {user_id} - no existing projects")
                return []
            
            return projects
            
        except Exception as e:
            logger.error(f"Error fetching user projects: {e}")
            return []
    
    @staticmethod
    def get_project_by_code(user_id, code):
        """Get a specific project by code (security: user must own it)"""
        try:
            project = WorkspaceProject.query.filter_by(
                user_id=str(user_id),
                code=code,
                is_deleted=False
            ).first()
            
            return project
            
        except Exception as e:
            logger.error(f"Error fetching project by code: {e}")
            return None
    
    @staticmethod
    def update_project(user_id, code, title, content):
        """
        Update an existing project
        Returns: (success: bool, project: WorkspaceProject|None, message: str)
        """
        try:
            project = WorkspaceService.get_project_by_code(user_id, code)
            if not project:
                return False, None, "Project not found or access denied"
            
            # Calculate storage without requiring PostgreSQL User model
            total_storage_bytes = db.session.query(db.func.sum(WorkspaceProject.storage_size)).filter(
                WorkspaceProject.user_id == str(user_id),
                WorkspaceProject.is_deleted == False
            ).scalar() or 0
            
            current_used_mb = total_storage_bytes / (1024 * 1024)
            
            # Calculate new size
            old_size = project.storage_size
            new_text_size = len(title.encode('utf-8')) + len(content.encode('utf-8')) + 1024
            size_difference = (new_text_size - old_size) / (1024 * 1024)  # MB
            
            # Check if update would exceed storage limit (1MB limit)
            if size_difference > 0:
                if current_used_mb + size_difference > 1.0:
                    return False, None, f"Update would exceed storage limit. Current: {current_used_mb:.2f}MB (1MB limit)"
            
            # Update project
            project.update_content(title, content)
            db.session.commit()
            
            logger.info(f"Updated project {code} for user {user_id}")
            return True, project, "Project updated successfully!"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating project: {e}")
            return False, None, "Error updating project. Please try again."
    
    @staticmethod
    def delete_project(user_id, code):
        """
        Soft delete a project
        Returns: (success: bool, message: str)
        """
        try:
            project = WorkspaceService.get_project_by_code(user_id, code)
            if not project:
                return False, "Project not found or access denied"
            
            project.soft_delete()
            db.session.commit()
            
            logger.info(f"Deleted project {code} for user {user_id}")
            return True, "Project deleted successfully!"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting project: {e}")
            return False, "Error deleting project. Please try again."
    
    @staticmethod
    def get_storage_stats(user_id):
        """Get storage statistics for user"""
        try:
            # For sukusuku.ai users, provide default storage stats
            # since they're not in the PostgreSQL User model
            total_projects = WorkspaceProject.query.filter_by(
                user_id=str(user_id),
                is_deleted=False
            ).count()
            
            # Calculate used storage from projects
            total_storage_bytes = db.session.query(db.func.sum(WorkspaceProject.storage_size)).filter(
                WorkspaceProject.user_id == str(user_id),
                WorkspaceProject.is_deleted == False
            ).scalar() or 0
            
            used_mb = round(total_storage_bytes / (1024 * 1024), 2)
            remaining_mb = max(0, 1.0 - used_mb)
            
            return {
                'used_mb': used_mb,
                'remaining_mb': remaining_mb,
                'total_mb': 1.0,
                'usage_percentage': round((used_mb / 1.0) * 100, 1),
                'total_projects': total_projects
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            # Return default stats for new users
            return {
                'used_mb': 0,
                'remaining_mb': 1.0,
                'total_mb': 1.0,
                'usage_percentage': 0,
                'total_projects': 0
            }
    
    @staticmethod
    def can_save_content(user_id, content):
        """Check if user can save new content without exceeding storage limit"""
        try:
            # Calculate storage without requiring PostgreSQL User model
            total_storage_bytes = db.session.query(db.func.sum(WorkspaceProject.storage_size)).filter(
                WorkspaceProject.user_id == str(user_id),
                WorkspaceProject.is_deleted == False
            ).scalar() or 0
            
            current_used_mb = total_storage_bytes / (1024 * 1024)
            content_size_mb = (len(content.encode('utf-8')) + 1024) / (1024 * 1024)
            remaining_mb = max(0, 1.0 - current_used_mb)
            
            return remaining_mb >= content_size_mb
            
        except Exception as e:
            logger.error(f"Error checking storage capacity: {e}")
            return False