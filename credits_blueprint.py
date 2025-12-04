from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from app import db
from models import CreditPackage, Transaction
from sukusuku_integration import get_current_sukusuku_user
import logging
import os

credits_bp = Blueprint('credits', __name__, url_prefix='/credits')

@credits_bp.route('/')
def index():
    """Display credit packages for purchase - NO LOGIN REQUIRED"""
    user_data = get_current_sukusuku_user()
    
    # Ku coin packages with monthly and yearly plans
    packages = [
        # Monthly Plans
        {
            'id': 'lite_monthly',
            'name': 'Lite Monthly',
            'ku_coins': 500,
            'price': 20.0,
            'type': 'monthly',
            'description': '~250,000 words + ~250 images',
            'features': ['1 MB Storage', 'Standard Support', 'New writers & casual users']
        },
        {
            'id': 'pro_monthly',
            'name': 'Pro Monthly',
            'ku_coins': 1500,
            'price': 50.0,
            'type': 'monthly',
            'popular': True,
            'description': '~750,000 words + ~750 images',
            'features': ['1 MB Storage', 'Priority Support', 'Consistent creators']
        },
        {
            'id': 'studio_monthly',
            'name': 'Studio Monthly',
            'ku_coins': 5000,
            'price': 150.0,
            'type': 'monthly',
            'description': '~2,500,000 words + ~2,500 images',
            'features': ['1 MB Storage', 'Priority+ Support', 'Teams & publishing workflows']
        },
        # Yearly Plans (50% off)
        {
            'id': 'lite_yearly',
            'name': 'Lite Yearly',
            'ku_coins': 3000,  # 250 per month * 12
            'price': 120.0,  # 50% off
            'type': 'yearly',
            'effective_monthly': 10.0,
            'description': '~125,000 words/mo + ~125 images/mo',
            'features': ['1 MB Storage', 'Standard Support', 'Long-term casual usage']
        },
        {
            'id': 'pro_yearly',
            'name': 'Pro Yearly',
            'ku_coins': 9000,  # 750 per month * 12
            'price': 300.0,  # 50% off
            'type': 'yearly',
            'effective_monthly': 25.0,
            'best_value': True,
            'description': '~375,000 words/mo + ~375 images/mo',
            'features': ['1 MB Storage', 'Priority Support', 'Consistent creators']
        },
        {
            'id': 'studio_yearly',
            'name': 'Studio Yearly',
            'ku_coins': 30000,  # 2500 per month * 12
            'price': 900.0,  # 50% off
            'type': 'yearly',
            'effective_monthly': 75.0,
            'description': '~1,250,000 words/mo + ~1,250 images/mo',
            'features': ['1 MB Storage', 'Priority+ Support', 'Power users & teams']
        }
    ]
    
    # Top-up packages for small purchases
    topup_packages = [
        {
            'id': 'topup_10',
            'name': '10 Ku Coins',
            'ku_coins': 10,
            'price': 1.0,
            'type': 'topup',
            'description': '~5,000 words + ~5 images',
            'features': ['Perfect for quick content', 'Instant delivery', 'Try our AI models']
        },
        {
            'id': 'topup_25',
            'name': '25 Ku Coins',
            'ku_coins': 25,
            'price': 3.0,
            'type': 'topup',
            'popular': True,
            'description': '~12,500 words + ~12 images',
            'features': ['Great for small projects', 'Multiple articles', 'Best value for testing']
        },
        {
            'id': 'topup_50',
            'name': '50 Ku Coins',
            'ku_coins': 50,
            'price': 5.0,
            'type': 'topup',
            'description': '~25,000 words + ~25 images',
            'features': ['Full project content', 'Multiple chapters', 'Extended creative work']
        }
    ]
    
    return render_template('pricing.html', 
                         user_data=user_data,
                         credits=user_data['credits'],
                         packages=packages,
                         topup_packages=topup_packages,
                         razorpay_enabled=True)

@credits_bp.route('/purchase', methods=['POST'])
def purchase():
    """Initiate credit purchase via sukusuku integration - NO LOGIN REQUIRED"""
    try:
        user_data = get_current_sukusuku_user()
        package_id = request.form.get('package_id')
        
        # Updated Ku coin package definitions including top-up packages
        packages_map = {
            'lite_monthly': {'name': 'Lite Monthly', 'ku_coins': 500, 'price': 20.0},
            'pro_monthly': {'name': 'Pro Monthly', 'ku_coins': 1500, 'price': 50.0},
            'studio_monthly': {'name': 'Studio Monthly', 'ku_coins': 5000, 'price': 150.0},
            'lite_yearly': {'name': 'Lite Yearly', 'ku_coins': 3000, 'price': 120.0},
            'pro_yearly': {'name': 'Pro Yearly', 'ku_coins': 9000, 'price': 300.0},
            'studio_yearly': {'name': 'Studio Yearly', 'ku_coins': 30000, 'price': 900.0},
            # Top-up packages
            'topup_10': {'name': '10 Ku Coins', 'ku_coins': 10, 'price': 1.0},
            'topup_25': {'name': '25 Ku Coins', 'ku_coins': 25, 'price': 3.0},
            'topup_50': {'name': '50 Ku Coins', 'ku_coins': 50, 'price': 5.0}
        }
        
        if package_id not in packages_map:
            flash('Invalid package selected', 'danger')
            return redirect(url_for('credits.index'))
            
        package = packages_map[package_id]
        
        # Create Razorpay order for the new Ku coin package
        from razorpay_service import create_order
        
        try:
            # Convert price from dollars to paisa (100 paisa = 1 rupee, assume 1 USD = 83 INR)
            amount_inr = int(package['price'] * 83 * 100)  # Convert to paisa
            
            # Create shorter receipt ID (max 40 chars for Razorpay)
            import time
            short_receipt = f"ku_{package_id[:4]}_{int(time.time())}"
            
            order_data = create_order(
                amount=amount_inr,
                currency='INR',
                receipt=short_receipt
            )
            
            if order_data:
                return jsonify({
                    'success': True,
                    'order_id': order_data['id'],
                    'amount': order_data['amount'],
                    'currency': order_data['currency'],
                    'key_id': order_data.get('key_id', ''),
                    'package_id': package_id,
                    'package_name': package['name'],
                    'ku_coins': package['ku_coins']
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to create payment order'}), 500
                
        except Exception as e:
            logging.error(f"Payment creation error: {e}")
            print(f"Payment creation error: {e}")
            return jsonify({'success': False, 'error': f'Payment order creation failed: {str(e)}'}), 500
            
    except Exception as e:
        logging.error(f"Credit purchase error: {str(e)}")
        flash('An error occurred while processing your purchase. Please try again.', 'danger')
        return redirect(url_for('credits.index'))

@credits_bp.route('/payment/verify', methods=['POST'])
def verify_payment():
    """Verify Razorpay payment and add Ku coins to user account"""
    try:
        user_data = get_current_sukusuku_user()
        
        # Get payment details from request
        payment_id = request.json.get('razorpay_payment_id')
        order_id = request.json.get('razorpay_order_id')
        signature = request.json.get('razorpay_signature')
        package_id = request.json.get('package_id')
        
        # Verify payment with Razorpay
        from razorpay_service import verify_payment as rp_verify
        
        if rp_verify(payment_id, order_id, signature):
            # Payment verified successfully, add Ku coins
            packages_map = {
                'lite_monthly': {'name': 'Lite Monthly', 'ku_coins': 500, 'price': 20.0},
                'pro_monthly': {'name': 'Pro Monthly', 'ku_coins': 1500, 'price': 50.0},
                'studio_monthly': {'name': 'Studio Monthly', 'ku_coins': 5000, 'price': 150.0},
                'lite_yearly': {'name': 'Lite Yearly', 'ku_coins': 3000, 'price': 120.0},
                'pro_yearly': {'name': 'Pro Yearly', 'ku_coins': 9000, 'price': 300.0},
                'studio_yearly': {'name': 'Studio Yearly', 'ku_coins': 30000, 'price': 900.0},
                # Top-up packages - CRITICAL: These were missing!
                'topup_10': {'name': '10 Ku Coins', 'ku_coins': 10, 'price': 1.0},
                'topup_25': {'name': '25 Ku Coins', 'ku_coins': 25, 'price': 3.0},
                'topup_50': {'name': '50 Ku Coins', 'ku_coins': 50, 'price': 5.0}
            }
            
            package = packages_map.get(package_id)
            if package:
                from sukusuku_integration import add_credits
                
                if add_credits(user_data['user_id'], package['ku_coins'], f'Purchased {package["name"]} - Payment: {payment_id}'):
                    return jsonify({
                        'success': True,
                        'credits_added': package['ku_coins'],
                        'redirect_url': url_for('index')
                    })
                else:
                    return jsonify({'success': False, 'error': 'Failed to add Ku coins to account'}), 500
            else:
                return jsonify({'success': False, 'error': 'Invalid package'}), 400
        else:
            return jsonify({'success': False, 'error': 'Payment verification failed'}), 400
            
    except Exception as e:
        logging.error(f"Payment verification error: {str(e)}")
        return jsonify({'success': False, 'error': 'Payment verification error'}), 500