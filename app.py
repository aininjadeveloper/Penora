import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
migrate = Migrate()
login_manager = LoginManager()

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or os.environ.get("SECRET_KEY") or "dev-secret-key"

# OAuth configuration
app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
}

# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)
migrate.init_app(app, db)

# Initialize Flask-Login
login_manager.init_app(app)
# login_manager.login_view = 'auth.login'  # Commented out for sukusuku.ai integration
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401

    db.create_all()
    
    # Create initial credit packages if they don't exist
    from models import CreditPackage
    if not CreditPackage.query.first():
        packages = [
            CreditPackage(),
            CreditPackage(), 
            CreditPackage(),
            CreditPackage()
        ]
        # Set package attributes individually
        packages[0].name = "Starter Pack"
        packages[0].credits = 10
        packages[0].price = 15.0  # INR 15
        
        packages[1].name = "Writer Pack"
        packages[1].credits = 25
        packages[1].price = 30.0  # INR 30
        
        packages[2].name = "Pro Pack"
        packages[2].credits = 50
        packages[2].price = 50.0  # INR 50
        
        packages[3].name = "Ultimate Pack"
        packages[3].credits = 100
        packages[3].price = 100.0  # INR 100
        
        for package in packages:
            db.session.add(package)
        db.session.commit()

# Initialize OAuth after app creation
from auth_blueprint import init_oauth_with_app
try:
    google_oauth = init_oauth_with_app(app)
    # Make Google OAuth available to auth_blueprint
    import auth_blueprint
    auth_blueprint.google_oauth = google_oauth
    print("Google OAuth initialized successfully")
except Exception as e:
    print(f"Warning: Google OAuth initialization failed: {e}")
    print("Google authentication will not be available")

# Import and register blueprints - only the correct ones
from auth_blueprint import auth_bp
from credits_blueprint import credits_bp
from integrated_auth import integrated_auth_bp

app.register_blueprint(auth_bp)
app.register_blueprint(credits_bp)
app.register_blueprint(integrated_auth_bp)

# Initialize sukusuku.ai integration
from sukusuku_integration import sukusuku_integration

# Initialize shared database
sukusuku_integration.init_shared_database()

# Add before_request handler for sukusuku.ai authentication
@app.before_request
def check_sukusuku_auth():
    """Check authentication on every request via sukusuku.ai integration"""
    from flask import request, g
    from sukusuku_integration import get_current_sukusuku_user
    # Skip auth check for static files
    if request.endpoint and request.endpoint.startswith('static'):
        return
    
    # Get user data and store in Flask context
    user_data = get_current_sukusuku_user()
    if user_data:
        logging.debug(f"👤 Auth Check: User {user_data.get('username')} authenticated")
    else:
        logging.debug("👤 Auth Check: No user authenticated")
    g.user = user_data

# Import routes
import routes  # noqa: F401