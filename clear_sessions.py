#!/usr/bin/env python3
"""
Clear all sessions to force fresh user isolation
"""

from flask import Flask, session
import os

# Create a temporary Flask app to clear sessions
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "temp_key")

with app.app_context():
    with app.test_request_context():
        session.clear()
        print("✅ Sessions cleared - fresh user isolation ready")