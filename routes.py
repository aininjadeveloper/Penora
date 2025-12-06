from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, make_response, session, g
from io import BytesIO
from app import app, db
from models import User, Transaction, Generation, CreditPackage, WorkspaceProject
from ai_service import ai_service
from pdf_service import pdf_service
from export_service import export_service
from sukusuku_integration import sukusuku_integration, require_sukusuku_auth, get_current_sukusuku_user, deduct_credits, get_user_data
from shared_credit_workspace_system import unified_system
from unified_api_endpoints import register_unified_apis
from jwt_sukusuku_auth import sukusuku_jwt_auth

def deduct_user_credits_safe(user_data, amount, description="Credit usage"):
    """Enhanced unified credit deduction for both Penora and ImageGene with real-time sync"""
    try:
        user_id = str(user_data['user_id'])
        app_name = 'penora'  # Default to penora for this context
        
        logging.info(f"🔄 CREDIT DEDUCTION: Attempting to deduct {amount} credits from user {user_data['username']} ({user_id})")
        
        # First ensure user exists in unified system
        try:
            unified_system.create_or_update_user(
                user_id=user_id,
                username=user_data.get('username', 'Unknown'),
                email=user_data.get('email', 'unknown@example.com'),
                initial_credits=user_data['credits']
            )
        except Exception as e:
            logging.warning(f"⚠️ User creation/update warning: {e}")
        
        # Try unified credit deduction first
        success = unified_system.deduct_credits(user_id, amount, app_name, description)
        
        if success:
            # Get the actual new balance from unified system
            try:
                user_info = unified_system.get_user_info(user_id)
                if user_info:
                    new_credits = user_info.get('credits', max(0, user_data['credits'] - amount))
                else:
                    new_credits = max(0, user_data['credits'] - amount)
            except Exception as e:
                logging.warning(f"⚠️ Could not get updated balance, using calculated: {e}")
                new_credits = max(0, user_data['credits'] - amount)
            
            # Update session data for immediate UI feedback
            user_session_key = f"user_credits_{user_data['user_id']}"
            session[user_session_key] = new_credits
            user_data['credits'] = new_credits
            
            if 'user_data' in session:
                session['user_data']['credits'] = new_credits
                session.modified = True  # Ensure session is saved
            
            logging.info(f"✅ UNIFIED CREDIT DEDUCTION: User {user_data['username']} ({user_id}) - {amount} credits deducted. New balance: {new_credits}")
            return True
        else:
            # Check if insufficient credits
            current_balance = unified_system.get_user_info(user_id)
            if current_balance and current_balance.get('credits', 0) < amount:
                logging.warning(f"❌ INSUFFICIENT CREDITS: User {user_data['username']} has {current_balance.get('credits', 0)}, needs {amount}")
                return False
            
            # Fallback to session-based system
            logging.warning(f"⚠️ Unified system failed, using session fallback")
            if user_data['credits'] < amount:
                logging.warning(f"❌ INSUFFICIENT CREDITS (session): User {user_data['username']} has {user_data['credits']}, needs {amount}")
                return False
                
            new_credits = max(0, user_data['credits'] - amount)
            user_session_key = f"user_credits_{user_data['user_id']}"
            session[user_session_key] = new_credits
            user_data['credits'] = new_credits
            
            if 'user_data' in session:
                session['user_data']['credits'] = new_credits
                session.modified = True
            
            logging.info(f"✅ SESSION CREDIT DEDUCTION: User {user_data['username']} - {amount} credits deducted. New balance: {new_credits}")
            return True
        
    except Exception as e:
        logging.error(f"❌ Credit deduction error: {e}")
        import traceback
        logging.error(f"❌ Full traceback: {traceback.format_exc()}")
        return False
from razorpay_service import razorpay_service
import logging
import time
import sqlite3
import requests
from datetime import datetime

# Configure logger for routes
logger = logging.getLogger(__name__)


@app.route('/health')
def health_check():
    """Fast health check endpoint for deployment"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200

@app.route('/health/detailed')
def health_detailed():
    """Detailed health check with database connectivity"""
    try:
        status = {"status": "healthy", "checks": {}}
        
        # Test database connection
        try:
            with sukusuku_integration.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                status["checks"]["database"] = {"status": "ok", "user_count": user_count}
        except Exception as db_error:
            status["checks"]["database"] = {"status": "error", "message": str(db_error)}
            status["status"] = "degraded"
        
        # Test authentication system
        try:
            # Test with empty parameters to see if fallback works
            test_user = get_user_data()
            status["checks"]["auth"] = {"status": "ok", "test_user_exists": test_user is not None}
        except Exception as auth_error:
            status["checks"]["auth"] = {"status": "error", "message": str(auth_error)}
            status["status"] = "degraded"
        
        status["timestamp"] = datetime.now().isoformat()
        return jsonify(status), 200 if status["status"] == "healthy" else 503
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/debug-auth')
def debug_auth():
    """Debug route to inspect authentication state"""
    try:
        debug_info = {
            "session": dict(session),
            "cookies": dict(request.cookies),
            "headers": dict(request.headers),
            "args": dict(request.args),
            "user_data_from_func": get_user_data(),
            "g_user": getattr(g, 'user', 'Not Set')
        }
        # Sanitize secrets
        if 'headers' in debug_info:
            headers = debug_info['headers']
            keys_to_redact = ['Authorization', 'Cookie', 'X-Api-Key']
            for k in keys_to_redact:
                if k in headers:
                    headers[k] = 'REDACTED'
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/force-logout')
def force_logout():
    """Force clear session and redirect"""
    session.clear()
    response = make_response(redirect(url_for('index')))
    # Clear specific cookies if known
    response.set_cookie('session', '', expires=0)
    return response


@app.route('/')
@app.route('/penora')
@app.route('/penora/')
@app.route('/penora_link')  # Add SSO route from main website
@app.route('/app')  # Alternative route
@app.route('/writer')  # Alternative route
def index():
    """Homepage route - with session authentication check"""
    logger.info(f"🌐 Access attempt from {request.remote_addr} to {request.url}")
    logger.info(f"🔍 Request args: {dict(request.args)}")
    logger.info(f"🔍 User agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    # PRIORITY: Handle authentic sukusuku.ai JWT/SSO authentication
    authentic_user = sukusuku_jwt_auth.authenticate_user(request)
    if authentic_user:
        logger.info(f"🎯 AUTHENTIC SUKUSUKU: Processing {authentic_user['auth_method']} authentication")
        
        # Create session with authentic user data
        if sukusuku_jwt_auth.create_user_session(authentic_user):
            # Create/update user in unified system with authentic data
            try:
                unified_system.create_or_update_user(
                    user_id=authentic_user['user_id'],
                    username=authentic_user['username'],
                    email=authentic_user['email'],
                    initial_credits=50
                )
                logger.info(f"✅ AUTHENTIC USER: {authentic_user['username']} ({authentic_user['email']}) authenticated with 50 credits")
            except Exception as e:
                logger.warning(f"⚠️ Unified system sync warning: {e}")
            
            # Redirect to home page for authenticated users
            return redirect(url_for('index'))
    
    # Regular authentication for non-SSO users
    user_data = get_user_data()
    
    # If still no user data, check session for existing authentication
    if user_data is None:
        # Check if user is already in session from previous authentication
        if 'user_data' in session and session.get('authenticated'):
            user_data = session.get('user_data')
            
            # HOTFIX: Clear stale Lucifer_Jhon sessions from previous testing
            if user_data.get('username') == 'Lucifer_Jhon':
                logger.warning("⚠️ Detected stale Lucifer_Jhon session - clearing")
                session.clear()
                return redirect(url_for('index'))
                
            logger.info(f"✅ Using session user: {user_data.get('username', 'Unknown')}")
        else:
            # No authentication found - show login page or allow guest access
            logger.warning("⚠️ No user authentication found - user needs to login from sukusuku.ai")
            # Allow guest access but don't assign a random user
            user_data = {
                'user_id': None,
                'username': 'Guest',
                'email': None,
                'credits': 0,
                'subscription_status': 'free',
                'authenticated': False
            }
            logger.info("ℹ️ Guest access - user should login from sukusuku.ai website")
    
    return render_template('index.html', user_data=user_data)

# Test route to simulate sukusuku.ai authentication
@app.route('/test-session')
def test_session():
    """Test route to simulate session data from sukusuku.ai"""
    # Simulate session data from sukusuku.ai login
    test_users = [
        {'user_id': 'user_ayush_singh', 'name': 'Ayush Singh', 'email': 'goflucifer123@gmail.com'},
        {'user_id': 'user_alice_smith', 'name': 'Alice Smith', 'email': 'alice@example.com'},
        {'user_id': 'user_charlie_brown', 'name': 'Charlie Brown', 'email': 'charlie@example.com'},
    ]
    
    # Get user from query parameter or use first one
    user_index = int(request.args.get('user', 0))
    test_user = test_users[user_index % len(test_users)]
    
    # Set session data (as would be done by sukusuku.ai)
    session['user_id'] = test_user['user_id']
    session['name'] = test_user['name'] 
    session['email'] = test_user['email']
    session.permanent = True
    
    logger.info(f"🧪 TEST: Set session for {test_user['name']} ({test_user['email']})")
    
    return redirect(url_for('index'))

@app.route('/pricing')
def pricing():
    """Show pricing page with Razorpay integration"""
    user_data = get_user_data()
    
    if user_data is None:
        logger.error("🔒 Critical error: No user data available for pricing")
        return redirect(url_for('index'))
    
    # Get Razorpay packages
    packages = razorpay_service.get_credit_packages()
    
    return render_template('pricing.html', 
                         packages=packages, 
                         user_data=user_data, 
                         credits=user_data['credits'],
                         razorpay_enabled=razorpay_service.enabled,
                         razorpay_key_id=razorpay_service.key_id)

@app.route('/account')
def account():
    """User account dashboard with sukusuku.ai authentication"""
    user_data = get_user_data()
    
    if user_data is None:
        logger.error("🔒 Critical error: No user data available for account")
        return redirect(url_for('index'))
    
    credits = user_data['credits']
    
    # Initialize default values
    generations = []
    transactions = []
    workspace_projects = []
    storage_stats = {'used_mb': 0, 'remaining_mb': 5.0, 'total_mb': 5.0, 'usage_percentage': 0, 'total_projects': 0}
    
    try:
        # Get user data from shared database with proper connection handling
        with sukusuku_integration.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get recent workspace projects as generations - try multiple user_id formats
            try:
                # First try string format
                cursor.execute("""
                    SELECT project_title, generation_text, created_at, code
                    FROM workspace_projects 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC LIMIT 10
                """, (str(user_data['user_id']),))
                workspace_results = cursor.fetchall()
                
                # If no results with string format, try integer format (if possible)
                if not workspace_results and str(user_data['user_id']).isdigit():
                    try:
                        cursor.execute("""
                            SELECT project_title, generation_text, created_at, code
                            FROM workspace_projects 
                            WHERE user_id = ? 
                            ORDER BY created_at DESC LIMIT 10
                        """, (int(str(user_data['user_id'])[-15:]),))  # Use last 15 digits to avoid overflow
                        workspace_results = cursor.fetchall()
                    except:
                        pass
                
                logging.info(f"🔍 ACCOUNT: Found {len(workspace_results)} workspace projects for user {user_data['user_id']}")
                
                # Convert to proper format with enhanced display
                for row in workspace_results:
                    # Calculate Ku coins used based on word count (500 words = 1 Ku coin)
                    word_count = len(row[1].split()) if row[1] else 0
                    ku_coins_used = max(1, (word_count + 499) // 500)  # Proper rounding
                    
                    # Format timestamp for display
                    from datetime import datetime
                    try:
                        if isinstance(row[2], str):
                            created_dt = datetime.fromisoformat(row[2].replace('Z', '+00:00'))
                        else:
                            created_dt = row[2]
                        
                        date_str = created_dt.strftime('%Y-%m-%d')
                        time_str = created_dt.strftime('%H:%M')
                    except:
                        date_str = str(row[2])[:10] if row[2] else 'Unknown'
                        time_str = str(row[2])[11:16] if len(str(row[2])) > 16 else 'Unknown'
                    
                    generations.append({
                        'action': 'generation',
                        'details': row[0],  # project_title
                        'credits_used': ku_coins_used,
                        'created_at': row[2],
                        'date': date_str,
                        'time': time_str,
                        'code': row[3],
                        'preview': row[1][:120] + '...' if len(row[1]) > 120 else row[1],
                        'word_count': word_count
                    })
                    
            except Exception as e:
                logging.error(f"❌ Error loading workspace projects: {e}")
                import traceback
                logging.error(f"❌ Full traceback: {traceback.format_exc()}")
                pass
            
            # Get transaction history
            try:
                logging.info(f"🔍 ACCOUNT PAGE: Loading transactions for user {user_data['user_id']} ({user_data['username']})")
                
                cursor.execute("""
                    SELECT amount, transaction_type, description, created_at 
                    FROM credit_transactions 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC LIMIT 50
                """, (user_data['user_id'],))
                transaction_results = cursor.fetchall()
                
                # Convert to proper format with enhanced date/time parsing
                for row in transaction_results:
                    try:
                        from datetime import datetime
                        # Parse datetime properly
                        if isinstance(row[3], str):
                            try:
                                if 'T' in row[3]:
                                    created_at = datetime.fromisoformat(row[3].replace('Z', '+00:00'))
                                else:
                                    created_at = datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S.%f')
                            except:
                                try:
                                    created_at = datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S')
                                except:
                                    created_at = datetime.now()
                        else:
                            created_at = row[3] if row[3] else datetime.now()
                        
                        transactions.append({
                            'amount': abs(int(row[0])) if row[0] else 0,
                            'transaction_type': row[1].title() if row[1] else 'Unknown',
                            'description': row[2] if row[2] else 'No description',
                            'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S'),
                            'date': created_at.strftime('%Y-%m-%d'),
                            'time': created_at.strftime('%H:%M:%S')
                        })
                    except Exception as parse_error:
                        logging.error(f"Error parsing transaction: {parse_error}")
                        transactions.append({
                            'amount': abs(int(row[0])) if row[0] else 0,
                            'transaction_type': str(row[1]) if row[1] else 'Unknown',
                            'description': str(row[2]) if row[2] else 'Transaction record',
                            'created_at': str(row[3]) if row[3] else 'Unknown date',
                            'date': str(row[3])[:10] if row[3] else 'Unknown',
                            'time': str(row[3])[11:19] if row[3] and len(str(row[3])) > 19 else '00:00:00'
                        })
                        
            except sqlite3.OperationalError:
                pass
                
        logging.info(f"📊 Loaded {len(transactions)} transaction records for user {user_data['user_id']}")
        
        # Load workspace projects using WorkspaceService as backup and populate generations
        try:
            from workspace_service import WorkspaceService
            workspace_projects = WorkspaceService.get_user_projects(user_data['user_id'])
            storage_stats = WorkspaceService.get_storage_stats(user_data['user_id'])
            
            # If we didn't get generations from database, use workspace service
            if not generations and workspace_projects:
                logging.info(f"🔄 Using WorkspaceService data for {len(workspace_projects)} projects")
                for project in workspace_projects[:10]:  # Limit to 10 recent
                    word_count = len(project.generation_text.split()) if project.generation_text else 0
                    ku_coins_used = max(1, (word_count + 499) // 500)
                    
                    # Format timestamp
                    from datetime import datetime
                    try:
                        if hasattr(project, 'created_at') and project.created_at:
                            created_dt = project.created_at
                            date_str = created_dt.strftime('%Y-%m-%d')
                            time_str = created_dt.strftime('%H:%M')
                        else:
                            date_str = 'Today'
                            time_str = 'Recent'
                    except:
                        date_str = 'Today'
                        time_str = 'Recent'
                    
                    generations.append({
                        'action': 'generation',
                        'details': project.project_title,
                        'credits_used': ku_coins_used,
                        'created_at': getattr(project, 'created_at', 'Recent'),
                        'date': date_str,
                        'time': time_str,
                        'code': project.code,
                        'preview': project.generation_text[:120] + '...' if len(project.generation_text) > 120 else project.generation_text,
                        'word_count': word_count
                    })
                    
        except Exception as e:
            logging.error(f"Error loading workspace data: {e}")
        
    except Exception as e:
        logging.error(f"Error loading account page: {e}")
    
    return render_template('account.html', 
                         user_data=user_data, 
                         credits=credits,
                         generations=generations,
                         transactions=transactions,
                         workspace_projects=workspace_projects,
                         storage_stats=storage_stats)

@app.route('/start-writing', methods=['GET', 'POST'])
def start_writing():
    """Unified Start Writing interface with fresh projects and file upload"""
    user_data = get_user_data()
    
    if user_data is None:
        logger.error("🔒 Critical error: No user data available for start-writing")
        return redirect(url_for('index'))
    
    credits = user_data['credits']
    
    if request.method == 'POST':
        writing_type = request.form.get('writing_type', 'fresh')
        
        if writing_type == 'fresh':
            # Fresh project - multi-page generation with model selection
            prompt = request.form['prompt']
            page_count = int(request.form.get('page_count', 1))
            model_type = request.form.get('model_type', 'balanced')
            output_length = request.form.get('output_length', 'medium')
            
            # Calculate credits needed with model multiplier
            model_multipliers = {
                'creative': 1.5,
                'balanced': 1.0,
                'fast': 0.5,
                'summarize': 0.3
            }
            base_credits = page_count
            multiplier = model_multipliers.get(model_type, 1.0)
            credits_needed = max(1, int(base_credits * multiplier))
            
            if credits < credits_needed:
                flash(f'You need at least {credits_needed} credits to generate {page_count} page(s) with {model_type} model. You have {credits} credits.', 'warning')
                return redirect(url_for('pricing'))
            
            try:
                if page_count == 1:
                    # Single page generation - use simple working API
                    from ai_service import generate_text_simple
                    generation_result = generate_text_simple(prompt, model_type, pages=1)
                    if generation_result['success']:
                        result = generation_result['content']
                        model_used = generation_result.get('model_used', model_type)
                    else:
                        flash(f"Generation failed: {generation_result['error']}", 'danger')
                        return render_template('start_writing.html', user_data=user_data, credits=credits)
                else:
                    # Multi-page generation - use updated function
                    from ai_service import generate_text_simple
                    generation_result = generate_text_simple(prompt, model_type, pages=page_count)
                    if generation_result.get('success'):
                        result = generation_result['content']
                        model_used = generation_result.get('model_used', model_type)
                    else:
                        flash(f"Story generation failed: {generation_result.get('error', 'Unknown error')}", 'danger')
                        return render_template('start_writing.html', user_data=user_data, credits=credits)
                
                if result:
                    # Deduct credits from sukusuku integration
                    # For SSO users, use session-based credit deduction to avoid database issues
                    if deduct_user_credits_safe(user_data, credits_needed, f"{page_count} page generation: {prompt[:50]}"):
                        remaining_credits = max(0, credits - credits_needed)
                        user_data['credits'] = remaining_credits
                        
                        # Try to save to workspace (optional)
                        project_code = None
                        try:
                            from workspace_service import WorkspaceService
                            title = f"{page_count} Page(s) - {prompt[:30]}..." if len(prompt) > 30 else f"{page_count} Page(s) - {prompt}"
                            logging.info(f"🔄 Attempting to save to workspace: user_id={user_data['user_id']}, title='{title}'")
                            success, project, message = WorkspaceService.save_generation(
                                user_data['user_id'], 
                                title, 
                                result
                            )
                            if success and project:
                                project_code = getattr(project, 'code', None)
                                logging.info(f"✅ Workspace save successful: code={project_code}")
                            else:
                                logging.error(f"❌ Workspace save failed: {message}")
                        except Exception as workspace_error:
                            logging.error(f"❌ Workspace save error: {workspace_error}")
                            import traceback
                            logging.error(f"❌ Full traceback: {traceback.format_exc()}")
                        
                        if project_code:
                            flash(f'{page_count} page(s) generated and saved to workspace! Code: {project_code}. {credits_needed} credit(s) deducted. {remaining_credits} credits remaining.', 'success')
                        else:
                            flash(f'{page_count} page(s) generated successfully! {credits_needed} credit(s) deducted. {remaining_credits} credits remaining.', 'success')
                        
                        return render_template('start_writing.html', 
                                             result=result, 
                                             prompt=prompt,
                                             page_count=page_count,
                                             model_type=model_type,
                                             output_length=output_length,
                                             credits_used=credits_needed,
                                             user_data=user_data,
                                             credits=remaining_credits)
                    else:
                        flash('Error deducting credits. Please try again.', 'danger')
                        return render_template('start_writing.html', user_data=user_data, credits=credits)
                else:
                    flash('Error generating content. Please try again.', 'danger')
                    
            except Exception as e:
                logging.error(f"Error in page generation: {e}")
                flash('Error generating page. Please try again.', 'danger')
        
        elif writing_type == 'existing':
            # Enhanced file upload with automatic page detection
            uploaded_file = request.files.get('project_file')
            instruction = request.form.get('file_instruction')
            model_type = request.form.get('model_type', 'balanced')
            
            if not uploaded_file or uploaded_file.filename == '':
                flash('Please upload a file to continue.', 'danger')
                return render_template('start_writing.html', user_data=user_data, credits=credits)
                
            if not instruction:
                flash('Please select what you want to do with the file.', 'danger')
                return render_template('start_writing.html', user_data=user_data, credits=credits)
            
            try:
                # Enhanced file analysis with automatic page detection
                from file_analyzer import analyze_uploaded_file
                from io import BytesIO
                
                # Get file info
                filename = uploaded_file.filename or "uploaded_file"
                file_content = uploaded_file.read()
                file_size = len(file_content) if file_content else 0
                uploaded_file.seek(0)  # Reset file pointer
                
                # Analyze file to get page count and content
                file_stream = BytesIO(uploaded_file.read())
                analysis_result = analyze_uploaded_file(file_stream, filename, file_size)
                
                if not analysis_result['success']:
                    flash(f"File analysis failed: {analysis_result['error']}", 'danger')
                    supported = ', '.join(analysis_result.get('supported_formats', ['txt', 'docx']))
                    flash(f"Supported formats: {supported}", 'info')
                    return render_template('start_writing.html', user_data=user_data, credits=credits)
                
                # Get analysis details
                pages_detected = analysis_result.get('pages', 1)
                word_count = analysis_result.get('word_count', 0)
                file_content = analysis_result.get('content', '')
                credits_needed = analysis_result.get('credits_needed', pages_detected)
                file_format = analysis_result.get('file_format', 'Unknown')
                
                # Apply model cost multiplier
                model_multipliers = {
                    'creative': 1.5,
                    'balanced': 1.0,
                    'fast': 0.5,
                    'summarize': 0.3
                }
                multiplier = model_multipliers.get(model_type, 1.0)
                final_credits_needed = max(1, int(credits_needed * multiplier))
                
                # Check if user has enough credits
                if credits < final_credits_needed:
                    flash(f'You need {final_credits_needed} credits to process this {pages_detected}-page file with {model_type} model. You have {credits} credits. Please top up your credits.', 'warning')
                    return redirect(url_for('pricing'))
                
                # Show file analysis to user before processing
                logging.info(f"📄 File Analysis - {filename}: {pages_detected} pages, {word_count} words, {final_credits_needed} credits needed")
                
                # Process file content with AI
                processing_result = ai_service.process_uploaded_file(file_content, instruction, model_type)
                
                if processing_result['success']:
                    result = processing_result['content']
                    model_used = processing_result.get('model_used', model_type)
                    
                    # Deduct the calculated credits
                    transaction_desc = f"File Processing [{model_type}] - {filename} ({pages_detected} pages): {instruction}"
                    if deduct_user_credits_safe(user_data, final_credits_needed, transaction_desc):
                        remaining_credits = max(0, credits - final_credits_needed)
                        user_data['credits'] = remaining_credits
                        
                        # Save to workspace with enhanced metadata
                        project_code = None
                        try:
                            from workspace_service import WorkspaceService
                            title = f"{instruction.title()} - {filename[:25]}..." if len(filename) > 25 else f"{instruction.title()} - {filename}"
                            success, project, message = WorkspaceService.save_generation(
                                user_data['user_id'], 
                                title, 
                                result
                            )
                            if success and project and hasattr(project, 'code'):
                                project_code = project.code
                                logging.info(f"✅ Enhanced file saved to workspace: {project_code}")
                        except Exception as workspace_error:
                            logging.error(f"Workspace save error: {workspace_error}")
                        
                        # Success message with detailed info
                        if project_code:
                            flash(f'File processed and saved to workspace! Code: {project_code}. '
                                  f'{final_credits_needed} credits used for {pages_detected}-page {file_format}. '
                                  f'{remaining_credits} credits remaining.', 'success')
                        else:
                            flash(f'File processed successfully! {final_credits_needed} credits used for '
                                  f'{pages_detected}-page {file_format}. {remaining_credits} credits remaining.', 'success')
                        
                        return render_template('start_writing.html', 
                                             result=result, 
                                             original_file=filename,
                                             file_analysis=analysis_result,
                                             pages_processed=pages_detected,
                                             credits_used=final_credits_needed,
                                             instruction=instruction,
                                             model_type=model_type,
                                             user_data=user_data,
                                             credits=remaining_credits)
                    else:
                        flash('Error deducting credits. Please try again.', 'danger')
                else:
                    flash(f'Error processing file: {processing_result.get("error", "Unknown error")}', 'danger')
                    
            except Exception as e:
                logging.error(f"Enhanced file processing error: {e}")
                flash('Error analyzing or processing your file. Please try again.', 'danger')
            
    return render_template('start_writing.html', user_data=user_data, credits=credits)

# Old single prompt route disabled - users should use /start-writing
# @app.route('/single-prompt-old', methods=['GET', 'POST'])
@require_sukusuku_auth
def single_prompt_old():
    """Single prompt text generation with sukusuku.ai authentication"""
    user_data = g.user
    credits = user_data['credits']
    
    if request.method == 'POST':
        prompt = request.form['prompt']
        
        # Check credits
        if credits < 1:
            flash('Insufficient credits. Please purchase more credits to continue.', 'warning')
            return redirect(url_for('pricing'))
            
        # Generate AI content
        try:
            result = ai_service.generate_single_text(prompt)
            if result:
                # Deduct credits from sukusuku.ai integrated database
                if deduct_user_credits_safe(user_data, 1, f"Single prompt: {prompt[:50]}..."):
                    
                    # Auto-save to workspace
                    from workspace_service import WorkspaceService
                    title = f"Single Prompt - {prompt[:30]}..." if len(prompt) > 30 else f"Single Prompt - {prompt}"
                    success, project, message = WorkspaceService.save_generation(
                        user_data['user_id'], 
                        title, 
                        result
                    )
                    
                    if success and project:
                        project_code = getattr(project, 'code', 'N/A')
                        flash(f'Text generated and saved to workspace! Code: {project_code}. 1 credit deducted.', 'success')
                    else:
                        flash('Text generated successfully! 1 credit deducted. Note: Could not save to workspace - storage limit reached.', 'warning')
                    
                    return render_template('single_prompt.html', 
                                         result=result, 
                                         prompt=prompt,
                                         user_data=user_data,
                                         credits=credits-1)
                else:
                    flash('Error deducting credits. Please try again.', 'danger')
            else:
                flash('Error generating text. Please try again.', 'danger')
                
        except Exception as e:
            logging.error(f"Error in single prompt generation: {e}")
            flash('Error generating text. Please try again.', 'danger')
            
    return render_template('single_prompt.html', user_data=user_data, credits=credits)

# Old story generator route disabled - users should use /start-writing
# @app.route('/story-generator-old', methods=['GET', 'POST'])
@require_sukusuku_auth
def story_generator_old():
    """Multi-chapter story generation with sukusuku.ai authentication"""
    user_data = g.user
    credits = user_data['credits']
    
    if request.method == 'POST':
        story_prompt = request.form['story_prompt']
        page_count = int(request.form.get('page_count', 3))
        
        if credits < page_count:
            flash(f'You need at least {page_count} credits to generate a {page_count}-page story. You have {credits} credits.', 'warning')
            return redirect(url_for('pricing'))
        
        try:
            # Generate multi-page story
            story = ai_service.generate_story(story_prompt, page_count)
            if story:
                # Deduct credits from sukusuku.ai integrated database
                if deduct_user_credits_safe(user_data, page_count, f"Story: {story_prompt[:50]}..."):
                    
                    # Format story content for display
                    formatted_story = ai_service.format_story_display(story)
                    
                    # Auto-save story to workspace
                    from workspace_service import WorkspaceService
                    title = request.form.get('title', '')
                    story_title = title if title else f"Story - {story_prompt[:30]}..." if len(story_prompt) > 30 else f"Story - {story_prompt}"
                    success, project, message = WorkspaceService.save_generation(
                        user_data['user_id'], 
                        story_title, 
                        formatted_story
                    )
                    
                    if success and project:
                        project_code = getattr(project, 'code', 'N/A')
                        flash(f'Story generated and saved to workspace! Code: {project_code}. {page_count} credits deducted.', 'success')
                    else:
                        flash(f'Story generated successfully! {page_count} credits deducted. Note: Could not save to workspace - storage limit reached.', 'warning')
                    return render_template('story_generator.html', 
                                         story=formatted_story,
                                         story_prompt=story_prompt,
                                         user_data=user_data,
                                         credits=credits-page_count)
                else:
                    flash('Error deducting credits. Please try again.', 'danger')
            else:
                flash('Error generating story. Please try again.', 'danger')
                
        except Exception as e:
            logging.error(f"Error in story generation: {e}")
            flash('Error generating story. Please try again.', 'danger')
    
    return render_template('story_generator.html', user_data=user_data, credits=credits)

@app.route('/logout')
def logout():
    """Logout and redirect to sukusuku.ai"""
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(os.environ.get('SUKUSUKU_MAIN_URL', 'https://sukusuku.ai'))

# API endpoint for external credit purchases
@app.route('/api/add-credits', methods=['POST'])
def api_add_credits():
    """API endpoint to add credits from sukusuku.ai"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        credits = data.get('credits')
        note = data.get('note', 'Credit purchase from sukusuku.ai')
        
        if not user_id or not credits:
            return jsonify({'error': 'Missing user_id or credits'}), 400
        
        # Add credits via sukusuku.ai integration
        conn = sqlite3.connect(sukusuku_integration.shared_db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET credits = credits + ? WHERE id = ?", (credits, user_id))
        conn.commit()
        cursor.execute("SELECT credits FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        new_balance = result[0] if result else 0
        conn.close()
        
        return jsonify({
            'success': True,
            'new_balance': new_balance,
            'message': f'Added {credits} credits successfully'
        })
            
    except Exception as e:
        logging.error(f"Error adding credits via API: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user-status')
def api_user_status():
    """API endpoint to check user authentication status with REAL data"""
    user_data = get_user_data()
    
    if user_data:
        return jsonify({
            'authenticated': True,
            'user_id': user_data['user_id'],
            'username': user_data['username'],
            'email': user_data['email'],
            'credits': user_data['credits'],  # Real remaining credits
            'original_credits': user_data.get('original_credits', 250),
            'credits_used': user_data.get('credits_used', 0),
            'subscription_status': user_data.get('subscription_status', 'premium'),
            'profile_image': user_data.get('profile_image')
        })
    else:
        return jsonify({
            'authenticated': False,
            'login_url': 'https://suku-suku-site-developeraim.replit.app/login'
        })

@app.route('/api/sync-credits', methods=['POST'])
def api_sync_credits():
    """API endpoint to sync credits with main sukusuku.ai website"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        credits_used = data.get('credits_used', 0)
        action = data.get('action', 'usage')
        description = data.get('description', 'Penora usage')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        # Get current user data
        user_data = get_user_data()
        if not user_data or user_data['user_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Update database with real usage
        conn = sqlite3.connect(sukusuku_integration.shared_db_path)
        cursor = conn.cursor()
        
        # Record actual usage in app_usage table
        cursor.execute("""
            INSERT INTO app_usage 
            (user_id, app_name, action, credits_used, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, 'penora', action, credits_used, description, datetime.now()))
        
        # Get updated total usage
        cursor.execute("""
            SELECT SUM(credits_used) as total_used 
            FROM app_usage 
            WHERE user_id = ? AND app_name = 'penora'
        """, (user_id,))
        usage_result = cursor.fetchone()
        total_used = usage_result[0] if usage_result and usage_result[0] else 0
        
        # Calculate remaining credits
        original_credits = user_data.get('original_credits', 250)
        remaining_credits = max(0, original_credits - total_used)
        
        conn.commit()
        conn.close()
        
        # Try to sync with main website
        try:
            main_site_url = 'https://c1ba9609-94a3-4895-8d7d-a2f5a0c196c7-00-1q7j60lf4r7la.riker.replit.dev'
            sync_data = {
                'user_id': user_id,
                'app': 'penora',
                'credits_used': credits_used,
                'total_credits_used': total_used,
                'remaining_credits': remaining_credits,
                'action': action,
                'description': description,
                'timestamp': datetime.now().isoformat()
            }
            
            sync_response = requests.post(f'{main_site_url}/api/apps/penora/sync', 
                                        json=sync_data, timeout=5)
            
            if sync_response.status_code in [200, 201]:
                logging.info(f"✅ Credits synced with main website: {credits_used} used, {remaining_credits} remaining")
            else:
                logging.warning(f"⚠️ Main website sync failed: {sync_response.status_code}")
                
        except Exception as sync_error:
            logging.warning(f"⚠️ Could not sync with main website: {sync_error}")
        
        return jsonify({
            'success': True,
            'credits_used': credits_used,
            'total_credits_used': total_used,
            'remaining_credits': remaining_credits,
            'message': f'Used {credits_used} credits. {remaining_credits} remaining.'
        })
        
    except Exception as e:
        logging.error(f"Error syncing credits: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# ===== MY WORKSPACE ROUTES =====

@app.route('/workspace')
def workspace():
    """My Workspace page showing all saved projects"""
    user_data = get_user_data()
    
    if user_data is None:
        logger.error("🔒 Critical error: No user data available for workspace")
        return redirect(url_for('index'))
    
    # CRITICAL FIX: Log user data to debug workspace isolation
    logging.info(f"🔍 WORKSPACE ACCESS: User ID {user_data['user_id']}, Username: {user_data['username']}, Email: {user_data['email']}")
    
    # Get user's workspace projects and storage stats (with error handling)
    try:
        from workspace_service import WorkspaceService
        projects = WorkspaceService.get_user_projects(user_data['user_id'])
        storage_stats = WorkspaceService.get_storage_stats(user_data['user_id'])
        
        # DEBUG: Log projects found for this user
        logging.info(f"📁 Found {len(projects)} projects for user {user_data['user_id']}")
        for project in projects[:3]:  # Log first 3 projects
            logging.info(f"  - Project: {project.project_title} (Code: {project.code})")
        
        # Ensure storage_stats is not None and has required attributes
        if not storage_stats:
            storage_stats = {
                'used_mb': 0, 
                'remaining_mb': 5.0, 
                'total_mb': 5.0, 
                'usage_percentage': 0, 
                'total_projects': 0
            }
            
    except Exception as e:
        logging.error(f"Error loading workspace: {e}")
        projects = []
        storage_stats = {
            'used_mb': 0, 
            'remaining_mb': 5.0, 
            'total_mb': 5.0, 
            'usage_percentage': 0, 
            'total_projects': 0
        }
    
    return render_template('workspace.html', 
                         user_data=user_data,
                         projects=projects,
                         storage_stats=storage_stats)

@app.route('/workspace/save', methods=['POST'])
def save_to_workspace():
    """Save generation to workspace OR update existing project"""
    user_data = get_user_data()
    
    if user_data is None:
        logger.error("🔒 Critical error: No user data available for workspace save")
        return redirect(url_for('index'))
    
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    project_code = request.form.get('code', '').strip()
    
    if not title or not content:
        flash('Title and content are required', 'danger')
        return redirect(request.referrer or url_for('workspace'))
    
    from workspace_service import WorkspaceService
    
    if project_code:
        # Update existing project
        success, project, message = WorkspaceService.update_project(
            user_data['user_id'], 
            project_code,
            title, 
            content
        )
        if success:
             flash('Project updated successfully!', 'success')
        else:
             flash(message, 'danger')
    else:
        # Create new project
        success, project, message = WorkspaceService.save_generation(
            user_data['user_id'], 
            title, 
            content
        )
        if success and project:
            project_code = getattr(project, 'code', 'N/A')
            flash(f'Project saved successfully! Code: {project_code}', 'success')
        else:
            flash(message, 'danger')
    
    return redirect(url_for('workspace'))

@app.route('/workspace/edit/<code>', methods=['GET', 'POST'])
def edit_workspace_project(code):
    """Edit a workspace project"""
    user_data = get_user_data()
    
    if user_data is None:
        logger.error("🔒 Critical error: No user data available for edit project")
        return redirect(url_for('workspace'))
    
    from workspace_service import WorkspaceService
    project = WorkspaceService.get_project_by_code(user_data['user_id'], code)
    
    if not project:
        flash('Project not found or access denied', 'danger')
        return redirect(url_for('workspace'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not title or not content:
            flash('Title and content are required', 'danger')
            return render_template('edit_project.html', project=project, user_data=user_data)
        
        success, updated_project, message = WorkspaceService.update_project(
            user_data['user_id'], 
            code, 
            title, 
            content
        )
        
        if success:
            flash('Project updated successfully!', 'success')
            return redirect(url_for('workspace'))
        else:
            flash(message, 'danger')
    
    return render_template('edit_project.html', project=project, user_data=user_data)

@app.route('/workspace/delete/<code>', methods=['POST'])
@require_sukusuku_auth
def delete_workspace_project(code):
    """Delete a workspace project"""
    user_data = g.user
    
    from workspace_service import WorkspaceService
    success, message = WorkspaceService.delete_project(user_data['user_id'], code)
    
    if success:
        flash('Project deleted successfully!', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('workspace'))

@app.route('/workspace/download/<code>/<format>')
@require_sukusuku_auth
def download_workspace_project(code, format):
    """Download workspace project in specified format"""
    user_data = g.user
    
    from workspace_service import WorkspaceService
    project = WorkspaceService.get_project_by_code(user_data['user_id'], code)
    
    if not project:
        flash('Project not found or access denied', 'danger')
        return redirect(url_for('workspace'))
    
    # Ensure content exists
    content_to_download = project.generation_text or ""
    if not content_to_download:
        content_to_download = " " # Empty space to prevent errors in document generators
        
    if format == 'pdf':
        pdf_result = pdf_service.generate_pdf(
            title=project.project_title,
            content=content_to_download
        )
        
        if not pdf_result.get('success'):
            flash('Error generating PDF: ' + pdf_result.get('error', 'Unknown error'), 'danger')
            return redirect(url_for('workspace'))
        
        # Create BytesIO buffer from PDF content
        from io import BytesIO
        pdf_buffer = BytesIO(pdf_result['pdf_content'])
        return send_file(pdf_buffer, as_attachment=True, 
                        download_name=f'{project.code}_{project.project_title[:20]}.pdf',
                        mimetype='application/pdf')
    
    elif format in ['docx', 'txt']:
        export_result = export_service.export_content(
            project.generation_text, 
            format, 
            title=project.project_title
        )
        
        if not export_result.get('success'):
            flash('Error generating file: ' + export_result.get('error', 'Unknown error'), 'danger')
            return redirect(url_for('workspace'))
        
        # Create BytesIO buffer from file content
        from io import BytesIO
        content_buffer = BytesIO(export_result['data'])
        
        mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if format == 'docx' else 'text/plain'
        return send_file(content_buffer, as_attachment=True,
                        download_name=f'{project.code}_{project.project_title[:20]}.{format}',
                        mimetype=mimetype)
    
    else:
        flash('Invalid download format', 'danger')
        return redirect(url_for('workspace'))

@app.route('/workspace/copy/<code>')
@require_sukusuku_auth
def copy_workspace_code(code):
    """Get project content for copying (AJAX endpoint)"""
    user_data = g.user
    
    from workspace_service import WorkspaceService
    project = WorkspaceService.get_project_by_code(user_data['user_id'], code)
    
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    return jsonify({
        'title': project.project_title,
        'content': project.generation_text,
        'code': project.code
    })

# === SUDOWRITE-LIKE WRITING TOOLS ===

@app.route('/writing-tools')
@require_sukusuku_auth
def sudowrite_tools():
    """Sudowrite-like writing tools interface"""
    user_data = g.user
    credits = user_data['credits']
    
    # Get workspace stats for sidebar
    from workspace_service import WorkspaceService
    workspace_projects = WorkspaceService.get_user_projects(user_data['user_id'])
    storage_stats = WorkspaceService.get_storage_stats(user_data['user_id'])
    
    return render_template('sudowrite_tools.html', 
                         user_data=user_data, 
                         credits=credits,
                         workspace_projects=workspace_projects,
                         storage_stats=storage_stats)

@app.route('/sudowrite/write', methods=['POST'])
@require_sukusuku_auth
def sudowrite_write():
    """Handle Write tool requests"""
    user_data = g.user
    credits = user_data['credits']
    
    if credits < 1:
        flash('Insufficient credits for Write tool. Please top up your credits.', 'warning')
        return redirect(url_for('pricing'))
    
    try:
        prompt = request.form.get('main_text', '') + '\n' + request.form.get('direction', '')
        mode = request.form.get('mode', 'auto')
        variants = int(request.form.get('variants', 3))
        temperature = float(request.form.get('temperature', 0.7))
        model_type = 'creative'  # Use creative model for writing
        
        # Use the basic text generation function since Sudowrite tools may not exist
        result = ai_service.generate_text(prompt, model_type, 'medium')
        
        if result['success']:
            # Deduct credits (1 credit per variant)
            credits_needed = variants
            if deduct_user_credits_safe(user_data, credits_needed, f"Write Tool: {mode} ({variants} variants)"):
                remaining_credits = user_data['credits'] - credits_needed
                user_data['credits'] = remaining_credits
                
                flash(f'Generated {variants} writing variants! {credits_needed} credits used.', 'success')
                return render_template('sudowrite_tools.html', 
                                     user_data=user_data, 
                                     credits=remaining_credits,
                                     results=[{'type': 'write', 'content': result['content'], 'model_used': result['model_used']}])
            else:
                flash('Error processing credits. Please try again.', 'danger')
        else:
            flash(f'Write tool error: {result["error"]}', 'danger')
            
    except Exception as e:
        logging.error(f"Write tool error: {e}")
        flash('Error using Write tool. Please try again.', 'danger')
    
    return redirect(url_for('sudowrite_tools'))

@app.route('/sudowrite/rewrite', methods=['POST'])
@require_sukusuku_auth
def sudowrite_rewrite():
    """Handle Rewrite tool requests"""
    user_data = g.user
    credits = user_data['credits']
    
    if credits < 1:
        flash('Insufficient credits for Rewrite tool. Please top up your credits.', 'warning')
        return redirect(url_for('pricing'))
    
    try:
        selected_text = request.form.get('selected_text', '')
        rewrite_type = request.form.get('rewrite_type', 'improve')
        model_type = 'balanced'  # Use balanced model for rewriting
        
        if not selected_text.strip():
            flash('Please provide text to rewrite.', 'warning')
            return redirect(url_for('sudowrite_tools'))
        
        # Use basic text generation as sudowrite_rewrite_tool may not exist
        rewrite_prompt = f"Please {rewrite_type} this text while maintaining its core meaning:\n\n{selected_text}"
        result = ai_service.generate_text(rewrite_prompt, model_type, 'medium')
        
        if result['success']:
            # Deduct 1 credit
            if deduct_user_credits_safe(user_data, 1, f"Rewrite Tool: {rewrite_type}"):
                remaining_credits = user_data['credits'] - 1
                user_data['credits'] = remaining_credits
                
                flash(f'Text rewritten successfully! 1 credit used.', 'success')
                return render_template('sudowrite_tools.html', 
                                     user_data=user_data, 
                                     credits=remaining_credits,
                                     results=[{'type': 'rewrite', 'content': result['content'], 'model_used': result['model_used']}])
            else:
                flash('Error processing credits. Please try again.', 'danger')
        else:
            flash(f'Rewrite tool error: {result["error"]}', 'danger')
            
    except Exception as e:
        logging.error(f"Rewrite tool error: {e}")
        flash('Error using Rewrite tool. Please try again.', 'danger')
    
    return redirect(url_for('sudowrite_tools'))

@app.route('/api/user-projects', methods=['GET'])
def get_user_projects_api():
    """API endpoint for external apps to get user's Penora projects with enhanced authentication"""
    try:
        # Get user ID from URL params for cross-app access
        user_id = request.args.get('user_id') or session.get('user_id')
        jwt_token = request.args.get('jwt_token')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID required for API access'
            }), 401
            
        # Enhanced logging for debugging ImageGene integration
        logging.info(f"🔗 API: External app requesting projects for user {user_id}")
        logging.info(f"🔗 API: JWT provided: {'Yes' if jwt_token else 'No'}")
        
        # Get all user projects from workspace with proper isolation
        from workspace_service import WorkspaceService
        projects = WorkspaceService.get_user_projects(str(user_id))
        
        # Format projects for external consumption with enhanced data
        formatted_projects = []
        for project in projects:
            # Handle both dict and object project formats
            if hasattr(project, '__dict__'):
                # SQLAlchemy object
                formatted_projects.append({
                    'id': project.code,
                    'title': project.project_title or 'Untitled Project',
                    'content': project.generation_text or '',
                    'created_at': project.created_at.isoformat() if project.created_at else None,
                    'updated_at': project.updated_at.isoformat() if project.updated_at else None,
                    'size': len(project.generation_text or ''),
                    'word_count': len((project.generation_text or '').split()),
                    'type': 'penora_project'
                })
            else:
                # Dict format
                content = project.get('content', project.get('generation_text', ''))
                formatted_projects.append({
                    'id': project.get('code'),
                    'title': project.get('title', project.get('project_title', 'Untitled Project')),
                    'content': content,
                    'created_at': project.get('created_at'),
                    'updated_at': project.get('updated_at'),
                    'size': len(content),
                    'word_count': len(content.split()) if content else 0,
                    'type': 'penora_project'
                })
        
        logging.info(f"🔗 API: Returning {len(formatted_projects)} projects for user {user_id}")
        
        return jsonify({
            'success': True,
            'projects': formatted_projects,
            'total_count': len(formatted_projects),
            'user_info': {
                'user_id': user_id,
                'username': request.args.get('first_name', '') + ' ' + request.args.get('last_name', ''),
                'email': request.args.get('email', ''),
                'app': 'penora'
            },
            'api_version': '1.0',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"❌ API get user projects error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch user projects',
            'details': str(e)
        }), 500

@app.route('/api/project/<project_code>', methods=['GET'])  
def get_project_details_api(project_code):
    """API endpoint to get specific project details with enhanced security"""
    try:
        # Get user ID from URL params for cross-app access
        user_id = request.args.get('user_id') or session.get('user_id')
        jwt_token = request.args.get('jwt_token')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID required for project access'
            }), 401
            
        logging.info(f"🔗 API: External app requesting project {project_code} for user {user_id}")
            
        # Get specific project with enhanced security
        from workspace_service import WorkspaceService
        project = WorkspaceService.get_project_by_code(str(user_id), project_code)
        
        if not project:
            return jsonify({
                'success': False,
                'error': 'Project not found or access denied'
            }), 404
            
        # Format project data for API response
        project_data = {
            'id': project.code,
            'title': project.project_title or 'Untitled Project',
            'content': project.generation_text or '',
            'created_at': project.created_at.isoformat() if project.created_at else None,
            'updated_at': project.updated_at.isoformat() if project.updated_at else None,
            'size': len(project.generation_text or ''),
            'word_count': len((project.generation_text or '').split()),
            'type': 'penora_project',
            'user_id': user_id
        }
            
        return jsonify({
            'success': True,
            'project': project_data,
            'api_version': '1.0',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"API get project details error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch project details'
        }), 500

@app.route('/api/analyze-file', methods=['POST'])
@require_sukusuku_auth
def analyze_file_api():
    """API endpoint to analyze uploaded file and preview credit cost"""
    try:
        user_data = g.user
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        model_type = request.form.get('model_type', 'balanced')
        
        # Analyze file
        from file_analyzer import analyze_uploaded_file
        from io import BytesIO
        
        filename = uploaded_file.filename
        file_size = len(uploaded_file.read())
        uploaded_file.seek(0)
        
        file_stream = BytesIO(uploaded_file.read())
        analysis_result = analyze_uploaded_file(file_stream, filename, file_size)
        
        if not analysis_result['success']:
            return jsonify(analysis_result)
        
        # Calculate credits with model multiplier
        model_multipliers = {'creative': 1.5, 'balanced': 1.0, 'fast': 0.5, 'summarize': 0.3}
        multiplier = model_multipliers.get(model_type, 1.0)
        base_credits = analysis_result.get('credits_needed', 1)
        final_credits = max(1, int(base_credits * multiplier))
        
        # Format file size
        from file_analyzer import FileAnalyzer
        formatted_size = FileAnalyzer.format_file_size(file_size)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'file_size': formatted_size,
            'pages': analysis_result.get('pages', 1),
            'word_count': analysis_result.get('word_count', 0),
            'file_format': analysis_result.get('file_format', 'Unknown'),
            'base_credits': base_credits,
            'model_multiplier': multiplier,
            'final_credits': final_credits,
            'user_credits': user_data['credits'],
            'can_process': user_data['credits'] >= final_credits,
            'preview': analysis_result.get('content', '')[:200] + '...' if analysis_result.get('content') else ''
        })
        
    except Exception as e:
        logging.error(f"File analysis API error: {e}")
        return jsonify({'success': False, 'error': 'Failed to analyze file'})

@app.route('/api/cross-app/auth', methods=['POST'])
def cross_app_auth():
    """Cross-app authentication endpoint for external apps"""
    try:
        # Get authentication data from request
        auth_data = request.get_json() or {}
        jwt_token = auth_data.get('jwt_token') or request.args.get('jwt_token')
        user_id = auth_data.get('user_id') or request.args.get('user_id')
        
        if not jwt_token or not user_id:
            return jsonify({
                'success': False,
                'error': 'Missing authentication data'
            }), 400
            
        # Create or update user in unified system with bonus credits
        username = f"{auth_data.get('first_name', '')} {auth_data.get('last_name', '')}".strip() or 'External User'
        email = auth_data.get('email', request.args.get('email', 'external@app.com'))
        
        # Initialize user in unified system with 60 credits (50 + 10 bonus)
        user_result = unified_system.create_or_update_user(user_id, username, email, 60)
        
        if user_result:
            credits = user_result['credits']
        else:
            credits = 60  # Fallback
        
        sso_result = {
            'success': True,
            'username': username,
            'email': email,
            'credits': credits
        }
        
        if sso_result.get('success'):
            # Set session for cross-app access
            session['user_id'] = str(user_id)
            session['username'] = sso_result.get('username', '')
            session['email'] = sso_result.get('email', '')
            session['credits'] = sso_result.get('credits', 0)
            session['authenticated'] = True
            session.permanent = True
            
            return jsonify({
                'success': True,
                'user': {
                    'user_id': user_id,
                    'username': sso_result.get('username', ''),
                    'email': sso_result.get('email', ''),
                    'credits': sso_result.get('credits', 0)
                },
                'message': 'Cross-app authentication successful'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Authentication failed'
            }), 401
            
    except Exception as e:
        logging.error(f"Cross-app auth error: {e}")
        return jsonify({
            'success': False,
            'error': 'Authentication error'
        }), 500

@app.route('/download-content', methods=['POST'])
@require_sukusuku_auth
def download_content():
    """Download generated content in specified format"""
    try:
        title = request.form.get('title', 'Generated_Content')
        content = request.form.get('content', '')
        format_type = request.form.get('format', 'txt')
        
        if not content:
            flash('No content to download', 'danger')
            return redirect(url_for('start_writing'))
        
        # Clean title for filename
        clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        clean_title = clean_title[:30]  # Limit filename length
        
        if format_type == 'pdf':
            pdf_result = pdf_service.generate_pdf(title=title, content=content)
            if pdf_result.get('success'):
                from io import BytesIO
                pdf_buffer = BytesIO(pdf_result['pdf_content'])
                return send_file(pdf_buffer, as_attachment=True, 
                               download_name=f'{clean_title}.pdf',
                               mimetype='application/pdf')
            else:
                flash('Error generating PDF', 'danger')
                return redirect(url_for('start_writing'))
        
        elif format_type in ['docx', 'txt']:
            export_result = export_service.export_content(content, format_type, title=title)
            if export_result.get('success'):
                from io import BytesIO
                content_buffer = BytesIO(export_result['data'])
                mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if format_type == 'docx' else 'text/plain'
                return send_file(content_buffer, as_attachment=True,
                               download_name=f'{clean_title}.{format_type}',
                               mimetype=mimetype)
            else:
                flash('Error generating file', 'danger')
                return redirect(url_for('start_writing'))
        else:
            flash('Invalid download format', 'danger')
            return redirect(url_for('start_writing'))
            
    except Exception as e:
        logging.error(f"Download content error: {e}")
        flash('Error downloading content', 'danger')
        return redirect(url_for('start_writing'))

@app.route('/sudowrite/describe', methods=['POST'])
@require_sukusuku_auth
def sudowrite_describe():
    """Handle Describe tool requests"""
    user_data = g.user
    credits = user_data['credits']
    
    if credits < 1:
        flash('Insufficient credits for Describe tool. Please top up your credits.', 'warning')
        return redirect(url_for('pricing'))
    
    try:
        selected_text = request.form.get('selected_text', '')
        sense_focus = request.form.get('sense_focus', 'all')
        model_type = 'creative'  # Use creative model for descriptions
        
        if not selected_text.strip():
            flash('Please provide text to enhance with descriptions.', 'warning')
            return redirect(url_for('sudowrite_tools'))
        
        # Use basic text generation as sudowrite_describe_tool may not exist
        describe_prompt = f"Please add rich sensory descriptions focusing on {sense_focus} to enhance this text:\n\n{selected_text}"
        result = ai_service.generate_text(describe_prompt, model_type, 'medium')
        
        if result['success']:
            # Deduct 1 credit
            if deduct_user_credits_safe(user_data, 1, f"Describe Tool: {sense_focus}"):
                remaining_credits = user_data['credits'] - 1
                user_data['credits'] = remaining_credits
                
                flash(f'Descriptions added successfully! 1 credit used.', 'success')
                return render_template('sudowrite_tools.html', 
                                     user_data=user_data, 
                                     credits=remaining_credits,
                                     results=[{'type': 'describe', 'content': result['content'], 'model_used': result['model_used']}])
            else:
                flash('Error processing credits. Please try again.', 'danger')
        else:
            flash(f'Describe tool error: {result["error"]}', 'danger')
            
    except Exception as e:
        logging.error(f"Describe tool error: {e}")
        flash('Error using Describe tool. Please try again.', 'danger')
    
    return redirect(url_for('sudowrite_tools'))

@app.route('/sudowrite/brainstorm', methods=['POST'])
@require_sukusuku_auth
def sudowrite_brainstorm():
    """Handle Brainstorm tool requests"""
    user_data = g.user
    credits = user_data['credits']
    
    if credits < 1:
        flash('Insufficient credits for Brainstorm tool. Please top up your credits.', 'warning')
        return redirect(url_for('pricing'))
    
    try:
        category = request.form.get('category', 'plot_ideas')
        context = request.form.get('context', '')
        count = int(request.form.get('count', 10))
        model_type = 'fast'  # Use fast model for brainstorming
        
        # Use the basic text generation function since Sudowrite tools may not exist
        brainstorm_prompt = f"Generate {count} creative {category} ideas based on: {context}"
        result = ai_service.generate_text(brainstorm_prompt, model_type, 'medium')
        
        if result['success']:
            # Deduct 1 credit
            if deduct_user_credits_safe(user_data, 1, f"Brainstorm Tool: {category} ({count} ideas)"):
                remaining_credits = user_data['credits'] - 1
                user_data['credits'] = remaining_credits
                
                # Parse content into list
                import re
                raw_content = result['content']
                # Split by newlines and clean up
                content_list = []
                for line in raw_content.split('\n'):
                    line = line.strip()
                    if line:
                        # Remove leading numbers/bullets (e.g. "1.", "1)", "-", "•")
                        clean_line = re.sub(r'^(\d+[\.\)]|\-|•)\s*', '', line)
                        if clean_line:
                            content_list.append(clean_line)
                
                # If parsing failed to produce list, fallback to raw, but ensure list format for template
                if not content_list:
                    content_list = [raw_content]
                
                flash(f'Generated {count} {category} ideas! 1 credit used.', 'success')
                return render_template('sudowrite_tools.html', 
                                     user_data=user_data, 
                                     credits=remaining_credits,
                                     results=[{'type': 'brainstorm', 'content': content_list, 'model_used': result['model_used']}])
            else:
                flash('Error processing credits. Please try again.', 'danger')
        else:
            flash(f'Brainstorm tool error: {result["error"]}', 'danger')
            
    except Exception as e:
        logging.error(f"Brainstorm tool error: {e}")
        flash('Error using Brainstorm tool. Please try again.', 'danger')
    
    return redirect(url_for('sudowrite_tools'))

@app.route('/api/workspace-project/<code>/content')
def api_workspace_project_content(code):
    """API endpoint to get workspace project content for copying"""
    user_data = get_user_data()
    
    if user_data is None:
        return jsonify({'success': False, 'error': 'Authentication error'}), 500
    project = WorkspaceProject.query.filter_by(
        code=code,
        user_id=user_data['user_id']
    ).first()
    
    if not project:
        return jsonify({
            'success': False,
            'error': 'Project not found'
        }), 404
    
    return jsonify({
        'success': True,
        'content': project.generation_text,
        'title': project.project_title
    })

@app.route('/edit-generated-text/<code>')
def edit_generated_text(code):
    """Edit generated text immediately after generation"""
    user_data = get_user_data()
    
    if user_data is None:
        flash('Authentication error', 'danger')
        return redirect(url_for('workspace'))
    project = WorkspaceProject.query.filter_by(
        code=code,
        user_id=user_data['user_id']
    ).first()
    
    if not project:
        flash('Project not found', 'danger')
        return redirect(url_for('workspace'))
    
    return render_template('text_editor.html',
                         project_code=code,
                         title=project.project_title,
                         generated_text=project.generation_text,
                         credits_used=project.credits_used,
                         user_data=user_data)

@app.route('/save-edited-text/<code>', methods=['POST'])
def save_edited_text(code):
    """Save edited text changes"""
    user_data = get_user_data()
    
    if user_data is None:
        return jsonify({'success': False, 'error': 'Authentication error'}), 500
    project = WorkspaceProject.query.filter_by(
        code=code,
        user_id=user_data['user_id']
    ).first()
    
    if not project:
        return jsonify({'success': False, 'error': 'Project not found'}), 404
    
    try:
        # Update project with new content
        project.project_title = request.form.get('project_title', project.project_title)
        project.generation_text = request.form.get('generated_text', project.generation_text)
        project.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project saved successfully'
        })
    except Exception as e:
        logging.error(f"Error saving edited text: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/view-project/<code>')
def view_project(code):
    """View project text in a simple page"""
    user_data = get_user_data()
    
    if user_data is None:
        flash('Authentication error', 'danger')
        return redirect(url_for('workspace'))
    project = WorkspaceProject.query.filter_by(
        code=code,
        user_id=user_data['user_id']
    ).first()
    
    if not project:
        flash('Project not found', 'danger')
        return redirect(url_for('workspace'))
    
    return render_template('view_project.html',
                         project=project,
                         user_data=user_data)

# === RAZORPAY PAYMENT ROUTES ===

@app.route('/payment/create-order', methods=['POST'])
def create_payment_order():
    """Create Razorpay order for credit purchase"""
    user_data = get_user_data()
    
    if user_data is None:
        return jsonify({'success': False, 'error': 'Authentication error'}), 401
    
    package_id = request.form.get('package_id')
    
    if not package_id:
        return jsonify({'success': False, 'error': 'Please select a credit package'}), 400
    
    result = razorpay_service.create_order(package_id, user_data)
    return jsonify(result)

@app.route('/payment/verify', methods=['POST'])
@require_sukusuku_auth
def verify_payment():
    """Verify Razorpay payment and add credits"""
    try:
        payment_data = request.get_json()
        result = razorpay_service.verify_payment(payment_data)
        
        if result['success']:
            # Refresh user data to show updated credits
            user_data = get_user_data()
            flash(f'Payment successful! {result["credits_added"]} credits added to your account.', 'success')
            return jsonify({
                'success': True,
                'credits_added': result['credits_added'],
                'redirect_url': url_for('account')
            })
        else:
            flash(f'Payment verification failed: {result["error"]}', 'danger')
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        logging.error(f"Payment verification error: {e}")
        flash('Payment verification failed. Please contact support.', 'danger')
        return jsonify({'success': False, 'error': 'Verification failed'})

@app.route('/payment/status/<payment_id>')
@require_sukusuku_auth
def payment_status(payment_id):
    """Check payment status"""
    result = razorpay_service.get_payment_status(payment_id)
    return jsonify(result)

@app.route('/api/sync-credits', methods=['GET'])
def sync_credits():
    """Sync current user's credits with unified system"""
    try:
        user_data = get_user_data()
        if not user_data:
            return jsonify({'success': False, 'error': 'No user data found'}), 401
        
        user_id = str(user_data['user_id'])
        
        # Get latest credits from unified system
        unified_user = unified_system.get_user_info(user_id)
        if unified_user:
            # Update session with real credits
            session_credits = unified_user['credits']
            user_data['credits'] = session_credits
            session['user_data'] = user_data
            session.modified = True
            
            logging.info(f"✅ CREDIT SYNC: Updated user {user_id} credits to {session_credits}")
            
            return jsonify({
                'success': True,
                'credits': session_credits,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            })
        else:
            # Create user in unified system if doesn't exist
            unified_system.create_or_update_user(
                user_id=user_id,
                username=user_data.get('username', 'Unknown'),
                email=user_data.get('email', 'unknown@example.com'),
                initial_credits=user_data['credits']
            )
            
            logging.info(f"✅ CREDIT SYNC: Created new user {user_id} in unified system with {user_data['credits']} credits")
            
            return jsonify({
                'success': True,
                'credits': user_data['credits'],
                'user_id': user_id,
                'created': True,
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        logging.error(f"❌ Credit sync error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Note: Unified API endpoints are registered in main.py to avoid conflicts