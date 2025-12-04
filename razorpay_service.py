"""
Razorpay Payment Integration for Credit Purchases
"""
import razorpay
import os
import logging
import sqlite3
from datetime import datetime
from sukusuku_integration import sukusuku_integration

logger = logging.getLogger(__name__)

class RazorpayService:
    def __init__(self):
        # Razorpay credentials (will be set via environment variables)
        self.key_id = os.environ.get('RAZORPAY_KEY_ID')
        self.key_secret = os.environ.get('RAZORPAY_KEY_SECRET')
        
        if self.key_id and self.key_secret:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
            self.enabled = True
            logger.info("Razorpay integration initialized successfully")
        else:
            self.client = None
            self.enabled = False
            logger.warning("Razorpay credentials not found. Payment system disabled.")
    
    def get_credit_packages(self):
        """Get available credit packages for purchase"""
        packages = [
            {
                'id': 'credits_100',
                'name': '100 Credits',
                'credits': 100,
                'price': 599,  # Price in paise (₹5.99)
                'currency': 'INR',
                'description': 'Perfect for casual writers',
                'popular': False
            },
            {
                'id': 'credits_250',
                'name': '250 Credits',
                'credits': 250,
                'price': 1299,  # Price in paise (₹12.99)
                'currency': 'INR',
                'description': 'Great value for regular users',
                'popular': True,
                'discount': 13  # 13% discount
            },
            {
                'id': 'credits_500',
                'name': '500 Credits',
                'credits': 500,
                'price': 2399,  # Price in paise (₹23.99)
                'currency': 'INR',
                'description': 'Best for power users',
                'popular': False,
                'discount': 20  # 20% discount
            },
            {
                'id': 'credits_1000',
                'name': '1000 Credits',
                'credits': 1000,
                'price': 4499,  # Price in paise (₹44.99)
                'currency': 'INR',
                'description': 'Maximum value for professionals',
                'popular': False,
                'discount': 25  # 25% discount
            }
        ]
        return packages
    
    def create_order(self, amount, currency='INR', receipt=None):
        """Create a new Razorpay order"""
        if not self.enabled:
            return None
            
        try:
            order_data = {
                "amount": amount,  # Amount in paisa
                "currency": currency,
                "receipt": receipt or f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            order = self.client.order.create(data=order_data)
            order['key_id'] = self.key_id  # Add key_id for frontend
            
            logger.info(f"Created Razorpay order: {order['id']}")
            return order
            
        except Exception as e:
            logger.error(f"Error creating Razorpay order: {e}")
            return None
    
    def verify_payment(self, payment_id, order_id, signature):
        """Verify Razorpay payment signature"""
        if not self.enabled:
            return False
            
        try:
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            self.client.utility.verify_payment_signature(params_dict)
            logger.info(f"Payment verification successful: {payment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Payment verification failed: {e}")
            return False

    def create_order_legacy(self, package_id, user_data):
        """Create Razorpay order for credit purchase (legacy method)"""
        if not self.enabled:
            return {'success': False, 'error': 'Payment system not configured'}
        
        try:
            packages = self.get_credit_packages()
            package = next((p for p in packages if p['id'] == package_id), None)
            
            if not package:
                return {'success': False, 'error': 'Invalid package selected'}
            
            # Create Razorpay order with 40-char limit receipt
            receipt_id = f"penora_{package_id}_{int(datetime.now().timestamp())}"[-40:]
            order_data = {
                'amount': package['price'],
                'currency': package['currency'],
                'receipt': receipt_id,
                'notes': {
                    'user_id': str(user_data['user_id']),
                    'username': user_data['username'],
                    'email': user_data['email'],
                    'package_id': package_id,
                    'credits': str(package['credits']),
                    'app': 'penora'
                }
            }
            
            order = self.client.order.create(order_data)
            
            return {
                'success': True,
                'order_id': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'package': package,
                'key_id': self.key_id
            }
            
        except Exception as e:
            logger.error(f"Error creating Razorpay order: {e}")
            return {'success': False, 'error': f'Order creation failed: {str(e)}'}
    
    def verify_payment(self, payment_data):
        """Verify Razorpay payment and add credits to user account"""
        if not self.enabled:
            return {'success': False, 'error': 'Payment system not configured'}
        
        try:
            # Extract payment details
            payment_id = payment_data.get('razorpay_payment_id')
            order_id = payment_data.get('razorpay_order_id')
            signature = payment_data.get('razorpay_signature')
            
            if not all([payment_id, order_id, signature]):
                return {'success': False, 'error': 'Missing payment verification data'}
            
            # Verify payment signature
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            try:
                self.client.utility.verify_payment_signature(params_dict)
            except razorpay.errors.SignatureVerificationError:
                # Get user email from order notes for notification
                try:
                    order = self.client.order.fetch(order_id)
                    user_email = order['notes'].get('email', 'user@sukusuku.ai')
                    self.send_payment_failure_notification(user_email, 'Payment verification failed', payment_id)
                except Exception as notify_error:
                    logger.error(f"Failed to send payment failure notification: {notify_error}")
                return {'success': False, 'error': 'Payment verification failed'}
            
            # Get order details
            order = self.client.order.fetch(order_id)
            payment = self.client.payment.fetch(payment_id)
            
            if payment['status'] != 'captured':
                # Send notification to user about payment not captured
                user_email = order['notes'].get('email', 'user@sukusuku.ai')
                self.send_payment_failure_notification(user_email, 'Payment not captured', payment_id)
                return {'success': False, 'error': 'Payment not captured'}
            
            # Extract user and package details from order notes - handle large user IDs
            try:
                user_id_str = order['notes']['user_id']
                # Convert to string if too large for integer, use original ID
                if len(user_id_str) > 15:  # Likely a large Google/SSO ID
                    user_id = user_id_str  # Keep as string for SSO users
                else:
                    user_id = int(user_id_str)  # Convert to int for regular users
                credits_to_add = int(order['notes']['credits'])
                package_id = order['notes']['package_id']
            except (ValueError, KeyError) as e:
                logger.error(f"Error parsing order notes: {e}")
                return {'success': False, 'error': 'Invalid order data'}
            
            # Add credits to user account and create transaction record
            success = self.add_credits_to_user(user_id, credits_to_add, package_id, payment_id, order_id)
            
            if success:
                return {
                    'success': True,
                    'credits_added': credits_to_add,
                    'payment_id': payment_id,
                    'order_id': order_id
                }
            else:
                # Send notification about credit addition failure
                user_email = order['notes'].get('email', 'user@sukusuku.ai')
                self.send_payment_failure_notification(user_email, 'Failed to add credits to account', payment_id)
                return {'success': False, 'error': 'Failed to add credits to account'}
            
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            # Try to get user email for notification even in case of error
            try:
                if order_id:
                    order = self.client.order.fetch(order_id)
                    user_email = order['notes'].get('email', 'user@sukusuku.ai')
                    self.send_payment_failure_notification(user_email, f'Payment verification error: {str(e)}', payment_id)
            except Exception as notify_error:
                logger.error(f"Failed to send error notification: {notify_error}")
            return {'success': False, 'error': f'Payment verification failed: {str(e)}'}
    
    def add_credits_to_user(self, user_id, credits, package_id, payment_id, order_id):
        """Add purchased credits to user account and log transaction"""
        try:
            # Use sukusuku_integration to add credits safely
            success = sukusuku_integration.add_credits(
                user_id, 
                credits, 
                f"Credit purchase - {package_id} package via Razorpay"
            )
            
            if success:
                logger.info(f"Added {credits} credits to user {user_id} via Razorpay payment {payment_id}")
                return True
            else:
                logger.error(f"Failed to add credits to user {user_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error adding credits to user {user_id}: {e}")
            return False
    
    def get_payment_status(self, payment_id):
        """Get payment status from Razorpay"""
        if not self.enabled:
            return {'success': False, 'error': 'Payment system not configured'}
        
        try:
            payment = self.client.payment.fetch(payment_id)
            return {
                'success': True,
                'status': payment['status'],
                'amount': payment['amount'],
                'currency': payment['currency'],
                'created_at': payment['created_at']
            }
        except Exception as e:
            logger.error(f"Error fetching payment status: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_payment_failure_notification(self, user_email, error_reason, payment_id):
        """Send email notification for payment failures to the specific user"""
        try:
            # Log the failure for the specific user email
            logger.error(f"Payment failure notification for {user_email}: {error_reason} (Payment: {payment_id})")
            
            # In a production environment, you would integrate with an email service like:
            # - SendGrid
            # - AWS SES
            # - Razorpay Webhooks
            # - SMTP server
            
            # For now, we log the notification details
            notification_details = {
                'to': user_email,
                'subject': 'Penora Payment Failed',
                'message': f'Your payment (ID: {payment_id}) failed due to: {error_reason}. Please try again or contact support.',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Payment failure notification prepared for {user_email}: {notification_details}")
            
            # Here you would actually send the email:
            # email_service.send_email(notification_details)
            
            return True
            
        except Exception as e:
            logger.error(f"Error preparing payment failure notification for {user_email}: {e}")
            return False
    
    def send_payment_success_notification(self, user_email, credits_added, payment_id):
        """Send email notification for successful payments to the specific user"""
        try:
            # Log successful payment for the specific user email
            logger.info(f"Payment success notification for {user_email}: {credits_added} credits added (Payment: {payment_id})")
            
            # Prepare success notification
            notification_details = {
                'to': user_email,
                'subject': 'Penora Credits Added Successfully',
                'message': f'Great news! {credits_added} credits have been added to your Penora account. Payment ID: {payment_id}',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Payment success notification prepared for {user_email}: {notification_details}")
            
            # Here you would actually send the email:
            # email_service.send_email(notification_details)
            
            return True
            
        except Exception as e:
            logger.error(f"Error preparing payment success notification for {user_email}: {e}")
            return False

# Global service instance
razorpay_service = RazorpayService()

# Global functions for easy access
def create_order(amount, currency='INR', receipt=None):
    """Global wrapper for creating Razorpay orders"""
    return razorpay_service.create_order(amount, currency, receipt)

def verify_payment(payment_id, order_id, signature):
    """Global wrapper for verifying Razorpay payments"""
    return razorpay_service.verify_payment(payment_id, order_id, signature)