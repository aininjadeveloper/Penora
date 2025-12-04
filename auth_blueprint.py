import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User, Transaction
import requests

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialize OAuth with proper configuration
from authlib.integrations.flask_client import OAuth
import os
import requests

oauth = OAuth()

def init_oauth_with_app(app):
    """Initialize OAuth with Flask app"""
    oauth.init_app(app)
    google = oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_OAUTH_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    return google

# This will be called from app.py
google_oauth = None

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        username = request.form.get('username', '').strip()
        
        # Validation
        if not email or not password or not username:
            flash('All fields are required.', 'danger')
            return render_template('auth/signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/signup.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login instead.', 'danger')
            return render_template('auth/signup.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken. Please choose another.', 'danger')
            return render_template('auth/signup.html')
        
        # Create new user with 10 free credits
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            credits=10
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create welcome transaction
        transaction = Transaction(
            user_id=user.id,
            transaction_type='purchase',
            amount=10,
            description='Welcome bonus - 10 free credits'
        )
        db.session.add(transaction)
        db.session.commit()
        
        login_user(user, remember=True, duration=None)  # 30 days
        flash('Account created successfully! You have received 10 free credits.', 'success')
        return redirect(url_for('index'))
    
    return render_template('auth/signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.password_hash and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/google/login')
def google_login():
    """Initiate Google OAuth login"""
    global google_oauth
    if not google_oauth:
        flash('Google OAuth is not properly configured.', 'danger')
        return redirect(url_for('auth.login'))
    
    redirect_uri = url_for('auth.google_callback', _external=True)
    return google_oauth.authorize_redirect(redirect_uri)

@auth_bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    global google_oauth
    if not google_oauth:
        flash('Google OAuth is not properly configured.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Handle Google returning 'access_denied'
    if 'error' in request.args and request.args.get('error') == 'access_denied':
        flash("Google refused access. Is this Gmail added as a Test User? Check if the app is published or add your email as a test user in Google Console.", "warning")
        return redirect(url_for('auth.login'))
    
    try:
        token = google_oauth.authorize_access_token()
        user_info = token.get('userinfo')
        
        if not user_info:
            flash('Failed to get user information from Google.', 'danger')
            return redirect(url_for('auth.login'))
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', '')
        
        if not google_id or not email:
            flash('Incomplete user information from Google.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Check if user already exists by Google ID
        user = User.query.filter_by(google_id=google_id).first()
        
        if not user:
            # Check if user exists by email
            user = User.query.filter_by(email=email.lower()).first()
            if user:
                # Link Google account to existing user
                user.google_id = google_id
                db.session.commit()
            else:
                # Create new user
                # Generate a unique username from the name
                base_username = name.replace(' ', '').lower()[:20]
                username = base_username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User(
                    username=username,
                    email=email.lower(),
                    google_id=google_id,
                    credits=10  # 10 free credits for new users
                )
                
                db.session.add(user)
                db.session.commit()
                
                # Create welcome transaction
                transaction = Transaction(
                    user_id=user.id,
                    transaction_type='purchase',
                    amount=10,
                    description='Welcome bonus - 10 free credits (Google signup)'
                )
                db.session.add(transaction)
                db.session.commit()
                
                flash('Account created successfully with Google! You have received 10 free credits.', 'success')
        
        login_user(user, remember=True)
        flash(f'Welcome, {user.username}!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash("Google sign-in unavailable right now, please use email login.", "danger")
        return redirect(url_for('auth.login'))