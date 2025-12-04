#!/usr/bin/env python3
"""
Integrated authentication blueprint that works with main website
"""
from flask import Blueprint, request, redirect, url_for, session, flash, render_template
from website_integration import website_integration, get_current_website_user, sync_user_with_website

integrated_auth_bp = Blueprint('integrated_auth', __name__, url_prefix='/integrated')

@integrated_auth_bp.route('/login')
def login():
    """Handle login - redirect to main website or verify existing session"""
    # Check if user is already authenticated via main website
    if sync_user_with_website():
        flash('Welcome to Penora! You are now logged in.', 'success')
        return redirect(url_for('index'))
    
    # Check existing session
    user_data = get_current_website_user()
    if user_data:
        return redirect(url_for('index'))
    
    # Redirect to main website login with return URL
    return_url = request.args.get('next', url_for('index', _external=True))
    login_url = f"https://c1ba9609-94a3-4895-8d7d-a2f5a0c196c7-00-1q7j60lf4r7la.riker.replit.dev/login?redirect={return_url}"
    
    return redirect(login_url)

@integrated_auth_bp.route('/callback')
def callback():
    """Handle callback from main website with session token"""
    session_token = request.args.get('token')
    if not session_token:
        flash('Authentication failed. Please try logging in again.', 'danger')
        return redirect(url_for('integrated_auth.login'))
    
    # Verify session with main website
    user_data = website_integration.verify_user_session(session_token)
    if user_data:
        session['user_data'] = user_data
        session['website_session_token'] = session_token
        flash(f"Welcome to Penora, {user_data.get('username', 'User')}!", 'success')
        return redirect(url_for('index'))
    else:
        flash('Authentication verification failed. Please try again.', 'danger')
        return redirect(url_for('integrated_auth.login'))

@integrated_auth_bp.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('You have been logged out from Penora.', 'info')
    
    # Redirect to main website logout
    return redirect("https://c1ba9609-94a3-4895-8d7d-a2f5a0c196c7-00-1q7j60lf4r7la.riker.replit.dev/logout")

@integrated_auth_bp.route('/status')
def status():
    """Check authentication status"""
    user_data = get_current_website_user()
    if user_data:
        # Get current credits from main website
        credits = website_integration.get_user_credits(user_data.get('user_id'))
        return {
            'authenticated': True,
            'user': user_data,
            'credits': credits
        }
    else:
        return {
            'authenticated': False,
            'user': None,
            'credits': 0
        }