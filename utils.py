from app import db
from models import Transaction
import logging

def deduct_credits(user, amount, description="Credit deduction"):
    """Deduct credits from user account and create transaction record"""
    try:
        if user.credits >= amount:
            user.credits -= amount
            
            # Create transaction record
            transaction = Transaction(
                user_id=user.id,
                transaction_type='deduction',
                amount=-amount,  # Negative for deductions
                description=description
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            logging.info(f"Deducted {amount} credits from user {user.id}. Remaining: {user.credits}")
            return True
        else:
            logging.warning(f"Insufficient credits for user {user.id}. Has {user.credits}, needs {amount}")
            return False
            
    except Exception as e:
        logging.error(f"Error deducting credits: {e}")
        db.session.rollback()
        return False

def can_generate(user):
    """Check if user has enough credits to generate content"""
    return user.credits >= 1

def add_credits(user, amount, description="Credit purchase"):
    """Add credits to user account and create transaction record"""
    try:
        user.credits += amount
        
        # Create transaction record
        transaction = Transaction(
            user_id=user.id,
            transaction_type='purchase',
            amount=amount,
            description=description
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        logging.info(f"Added {amount} credits to user {user.id}. Total: {user.credits}")
        return True
        
    except Exception as e:
        logging.error(f"Error adding credits: {e}")
        db.session.rollback()
        return False