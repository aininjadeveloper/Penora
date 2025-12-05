#!/usr/bin/env python3
"""
Unified API Endpoints for Penora + ImageGene Integration
Provides shared credit and workspace APIs for both applications
"""

from flask import Flask, request, jsonify, session
import logging
import os
from datetime import datetime
from shared_credit_workspace_system import unified_system

logger = logging.getLogger(__name__)

def register_unified_apis(app):
    """Register unified API endpoints with Flask app"""
    
    def verify_api_key():
        """Verify API key for external app access"""
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        valid_api_key = os.environ.get('PENORA_API_KEY')
        
        if not api_key or not valid_api_key:
            return False
        
        return api_key == valid_api_key
    
    def require_api_key():
        """Decorator to require API key for external endpoints"""
        if not verify_api_key():
            return jsonify({
                'success': False,
                'error': 'Invalid or missing API key. Include X-API-Key header or api_key parameter.'
            }), 401
        return None
    
    @app.route('/api/unified/user-info', methods=['GET'])
    def get_unified_user_info():
        """Get unified user information including credits and storage"""
        # Check API key for external access
        auth_error = require_api_key()
        if auth_error:
            return auth_error
            
        try:
            user_id = request.args.get('user_id') or session.get('user_id')
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID required'}), 401
            
            # Get user credits and storage info
            credits = unified_system.get_user_credits(user_id)
            
            # Return exact format required by SukuSuku
            return jsonify({
                'credits': credits,
                'user_id': user_id
            })
            
        except Exception as e:
            logger.error(f"Error getting unified user info: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/unified/add-credits', methods=['POST'])
    def add_unified_credits():
        """Add credits to user account (SukuSuku integration)"""
        # Check API key for external access
        auth_error = require_api_key()
        if auth_error:
            return auth_error
            
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            amount = data.get('amount')
            transaction_type = data.get('transaction_type', 'purchase')
            description = data.get('description', 'Credit addition')
            
            if not all([user_id, amount]):
                return jsonify({
                    'success': False, 
                    'error': 'Missing required fields: user_id, amount'
                }), 400
            
            # Use unified system to add credits (we'll use a negative deduction or implement add_credits in shared system)
            # Since unified_system.deduct_credits only deducts, we need to check if it supports adding or use a direct DB call
            # For now, we'll assume we can use the underlying integration directly if needed, 
            # but let's check if we can add a method to unified_system first.
            # Actually, let's use the sukusuku_integration directly for this specific operation if needed,
            # or better, assume unified_system has or will have add_credits.
            
            # Let's try to use the sukusuku_integration directly for now as it has add_credits
            from sukusuku_integration import sukusuku_integration
            success = sukusuku_integration.add_credits(user_id, amount, description)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Successfully added {amount} credits',
                    'user_id': user_id,
                    'amount_added': amount
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to add credits'
                }), 500
                
        except Exception as e:
            logger.error(f"Error adding unified credits: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/unified/projects', methods=['GET'])
    def get_unified_projects():
        """Get all user projects from both Penora and ImageGene"""
        # Check API key for external access
        auth_error = require_api_key()
        if auth_error:
            return auth_error
            
        try:
            user_id = request.args.get('user_id') or session.get('user_id')
            app_filter = request.args.get('app')  # 'penora', 'imagegene', or None for all
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID required'}), 401
            
            # Get projects with optional app filtering
            projects = unified_system.get_user_projects(user_id, app_filter)
            
            # Separate by app for merged display
            penora_projects = [p for p in projects if p['app_source'] == 'penora']
            imagegene_projects = [p for p in projects if p['app_source'] == 'imagegene']
            
            return jsonify({
                'success': True,
                'all_projects': projects,
                'penora_projects': penora_projects,
                'imagegene_projects': imagegene_projects,
                'total_count': len(projects),
                'penora_count': len(penora_projects),
                'imagegene_count': len(imagegene_projects),
                'storage_stats': unified_system.get_storage_stats(user_id),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting unified projects: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/unified/project/<project_code>', methods=['GET'])
    def get_unified_project_details(project_code):
        """Get specific project details from unified workspace"""
        try:
            user_id = request.args.get('user_id') or session.get('user_id')
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID required'}), 401
            
            project = unified_system.get_project_by_code(user_id, project_code)
            
            if not project:
                return jsonify({'success': False, 'error': 'Project not found'}), 404
            
            return jsonify({
                'success': True,
                'project': project,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting unified project details: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/unified/transactions', methods=['GET'])
    def get_unified_transactions():
        """Get user's credit transaction history across both apps"""
        try:
            user_id = request.args.get('user_id') or session.get('user_id')
            limit = int(request.args.get('limit', 50))
            
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID required'}), 401
            
            transactions = unified_system.get_user_transactions(user_id, limit)
            
            # Separate by app for analysis
            penora_transactions = [t for t in transactions if t['app_name'] == 'penora']
            imagegene_transactions = [t for t in transactions if t['app_name'] == 'imagegene']
            
            return jsonify({
                'success': True,
                'all_transactions': transactions,
                'penora_transactions': penora_transactions,
                'imagegene_transactions': imagegene_transactions,
                'total_count': len(transactions),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting unified transactions: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/unified/deduct-credits', methods=['POST'])
    def deduct_unified_credits():
        """Deduct credits from unified system (for both apps)"""
        # Check API key for external access
        auth_error = require_api_key()
        if auth_error:
            return auth_error
            
        try:
            data = request.get_json()
            user_id = data.get('user_id') or session.get('user_id')
            amount = data.get('amount')
            app_name = data.get('app_name')  # 'penora' or 'imagegene'
            description = data.get('description', 'Credit usage')
            project_code = data.get('project_code')
            
            if not all([user_id, amount, app_name]):
                return jsonify({
                    'success': False, 
                    'error': 'Missing required fields: user_id, amount, app_name'
                }), 400
            
            success = unified_system.deduct_credits(
                user_id, amount, app_name, description, project_code
            )
            
            if success:
                new_balance = unified_system.get_user_credits(user_id)
                return jsonify({
                    'success': True,
                    'credits_deducted': amount,
                    'new_balance': new_balance,
                    'app_name': app_name,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Insufficient credits or deduction failed'
                }), 400
                
        except Exception as e:
            logger.error(f"Error deducting unified credits: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/unified/save-project', methods=['POST'])
    def save_unified_project():
        """Save project to unified workspace (for both apps)"""
        # Check API key for external access
        auth_error = require_api_key()
        if auth_error:
            return auth_error
            
        try:
            data = request.get_json()
            user_id = data.get('user_id') or session.get('user_id')
            app_source = data.get('app_source')  # 'penora' or 'imagegene'
            project_type = data.get('project_type')  # 'text', 'image', 'ai_art', etc.
            title = data.get('title')
            content = data.get('content')
            metadata = data.get('metadata', {})
            
            if not all([user_id, app_source, project_type, title, content]):
                return jsonify({
                    'success': False,
                    'error': 'Missing required fields: user_id, app_source, project_type, title, content'
                }), 400
            
            result = unified_system.save_project(
                user_id, app_source, project_type, title, content, metadata
            )
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'project_code': result['project_code'],
                    'title': result['title'],
                    'size_mb': result['size_mb'],
                    'app_source': app_source,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logger.error(f"Error saving unified project: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/unified/storage-stats', methods=['GET'])
    def get_unified_storage_stats():
        """Get user's storage statistics across both apps"""
        try:
            user_id = request.args.get('user_id') or session.get('user_id')
            if not user_id:
                return jsonify({'success': False, 'error': 'User ID required'}), 401
            
            storage_stats = unified_system.get_storage_stats(user_id)
            
            # Get project breakdown by app
            projects = unified_system.get_user_projects(user_id)
            penora_size = sum(p['size_bytes'] for p in projects if p['app_source'] == 'penora')
            imagegene_size = sum(p['size_bytes'] for p in projects if p['app_source'] == 'imagegene')
            
            return jsonify({
                'success': True,
                'storage_stats': storage_stats,
                'breakdown': {
                    'penora_mb': round(penora_size / (1024 * 1024), 2),
                    'imagegene_mb': round(imagegene_size / (1024 * 1024), 2),
                    'total_projects': len(projects),
                    'penora_projects': len([p for p in projects if p['app_source'] == 'penora']),
                    'imagegene_projects': len([p for p in projects if p['app_source'] == 'imagegene'])
                },
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting unified storage stats: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/unified/create-user', methods=['POST'])
    def create_unified_user():
        """Create or update user in unified system"""
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            username = data.get('username')
            email = data.get('email')
            initial_credits = data.get('initial_credits', 60)
            
            if not all([user_id, username, email]):
                return jsonify({
                    'success': False,
                    'error': 'Missing required fields: user_id, username, email'
                }), 400
            
            user_data = unified_system.create_or_update_user(
                user_id, username, email, initial_credits
            )
            
            if user_data:
                return jsonify({
                    'success': True,
                    'user': user_data,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to create/update user'
                }), 500
                
        except Exception as e:
            logger.error(f"Error creating unified user: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/unified/give-bonus-credits', methods=['POST'])
    def give_bonus_credits_to_all():
        """Give bonus credits to all existing users (Admin function)"""
        try:
            data = request.get_json() or {}
            bonus_amount = data.get('bonus_amount', 10)
            admin_key = data.get('admin_key')
            
            # Simple admin key check (you can implement proper admin auth)
            if admin_key != 'penora_admin_2025':
                return jsonify({
                    'success': False,
                    'error': 'Unauthorized - Admin key required'
                }), 401
            
            result = unified_system.give_bonus_credits_to_all_users(bonus_amount)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': f'Successfully gave {bonus_amount} bonus credits to all users',
                    'users_updated': result['users_updated'],
                    'total_credits_distributed': result['total_credits_distributed'],
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify(result), 500
                
        except Exception as e:
            logger.error(f"Error giving bonus credits to all users: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    return app