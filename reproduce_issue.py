
from flask import Flask, session, request, redirect, url_for
from jwt_sukusuku_auth import sukusuku_jwt_auth
from sukusuku_integration import get_user_data
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = 'test_secret'

@app.route('/')
def index():
    # Simulate the logic in routes.py
    
    # 1. Try to authenticate from params
    authentic_user = sukusuku_jwt_auth.authenticate_user(request)
    if authentic_user:
        print(f"Authenticated user from params: {authentic_user['username']}")
        sukusuku_jwt_auth.create_user_session(authentic_user)
        return f"Redirecting... (Session set to {authentic_user['username']})"
    
    # 2. Fallback to get_user_data (which checks session)
    user_data = get_user_data()
    if user_data:
         print(f"User from session/fallback: {user_data['username']}")
         return f"Logged in as {user_data['username']}"
    
    return "Guest"

def test_reproduction():
    with app.test_client() as client:
        with client.session_transaction() as sess:
            # Set initial session to "Lucifer"
            sess['user_data'] = {
                'user_id': 'lucifer_id',
                'username': 'Lucifer',
                'email': 'lucifer@example.com',
                'credits': 50,
                'authenticated': True
            }
            sess['authenticated'] = True
        
        print("--- Initial State: Logged in as Lucifer ---")
        response = client.get('/')
        print(f"Response: {response.data.decode()}")
        
        print("\n--- Attempting Login as New User (via params) ---")
        # Simulate incoming request from sukusuku.ai with new user params
        response = client.get('/?user_id=new_user&email=new@example.com&first_name=New&last_name=User&credits=100')
        print(f"Response: {response.data.decode()}")
        
        # Check if session is updated
        with client.session_transaction() as sess:
            current_user = sess.get('user_data', {}).get('username')
            print(f"Current Session User: {current_user}")
            
            if current_user == 'New User':
                print("SUCCESS: Session was updated.")
            else:
                print("FAILURE: Session was NOT updated.")

if __name__ == "__main__":
    test_reproduction()
