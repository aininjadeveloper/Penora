#!/bin/bash
# Penora Deployment Script
# Production-ready deployment with optimized database handling

echo "🚀 Starting Penora deployment..."

# Clean caches
echo "🧹 Cleaning Python cache files..."
rm -rf __pycache__ **/__pycache__

# Environment variables (prefer adding these in Replit Secrets)
echo "🔧 Setting up environment..."
export DEEPINFRA_API_KEY="${DEEPINFRA_API_KEY:-YOUR_DEEPINFRA_KEY}"
export SECRET_KEY="${SECRET_KEY:-$(python -c 'import secrets; print(secrets.token_hex(32))')}"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-$(python -c 'import secrets; print(secrets.token_hex(32))')}"
export SUKUSUKU_MAIN_URL="${SUKUSUKU_MAIN_URL:-https://sukusuku.ai}"
export AUTO_LOGIN="${AUTO_LOGIN:-false}"
export SESSION_SECRET="${SESSION_SECRET:-$(python -c 'import secrets; print(secrets.token_hex(32))')}"

# Install dependencies from pyproject.toml
echo "📦 Installing dependencies..."
python - <<'PY'
import tomllib, subprocess, sys
try:
    py = tomllib.load(open("pyproject.toml","rb"))
    deps = py.get("project",{}).get("dependencies",[])
    subprocess.check_call([sys.executable,"-m","pip","install","--upgrade","pip","wheel","setuptools"])
    if deps: 
        subprocess.check_call([sys.executable,"-m","pip","install",*deps])
    print("✅ Dependencies installed successfully.")
except Exception as e:
    print(f"❌ Error installing dependencies: {e}")
    sys.exit(1)
PY

# Initialize database tables
echo "🗄️ Initializing database..."
python - <<'PY'
try:
    from app import app, db
    with app.app_context():
        db.create_all()
    print("✅ Database initialized successfully.")
except Exception as e:
    print(f"❌ Error initializing database: {e}")
    sys.exit(1)
PY

# Health check before starting
echo "🔍 Running pre-deployment health check..."
python - <<'PY'
try:
    from sukusuku_integration import sukusuku_integration
    sukusuku_integration.init_database()
    print("✅ Database connection test passed.")
except Exception as e:
    print(f"⚠️ Database connection warning: {e}")
PY

# Start the application with optimized settings
echo "🌟 Starting Penora application..."
echo "📊 Health endpoints available:"
echo "   - Fast: /health"
echo "   - Detailed: /health/detailed"
echo "🌐 Starting server on http://0.0.0.0:5000"

# Use gunicorn with production settings
exec gunicorn --bind 0.0.0.0:5000 --reload --workers 1 --timeout 120 --keep-alive 5 --max-requests 1000 --max-requests-jitter 50 main:app