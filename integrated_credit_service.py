#!/usr/bin/env python3
"""
Credit service that integrates with main website
"""
from website_integration import website_integration, get_current_website_user
from flask import session, flash

class IntegratedCreditService:
    """Handle credits using main website's system"""
    
    def get_user_credits(self):
        """Get current user's credits from main website"""
        user_data = get_current_website_user()
        if not user_data:
            return 0
            
        user_id = user_data.get('user_id')
        if not user_id:
            return 0
            
        return website_integration.get_user_credits(user_id)
    
    def deduct_credits(self, amount, description="AI text generation"):
        """Deduct credits from user's account on main website"""
        user_data = get_current_website_user()
        if not user_data:
            return False
            
        user_id = user_data.get('user_id')
        if not user_id:
            return False
            
        result = website_integration.deduct_credits(user_id, amount, description)
        return result is not None
    
    def add_credits(self, amount, description="Credit purchase"):
        """Add credits to user's account on main website"""
        user_data = get_current_website_user()
        if not user_data:
            return False
            
        user_id = user_data.get('user_id')
        if not user_id:
            return False
            
        result = website_integration.add_credits(user_id, amount, description)
        return result is not None
    
    def has_sufficient_credits(self, required_amount):
        """Check if user has sufficient credits"""
        current_credits = self.get_user_credits()
        return current_credits >= required_amount

# Global service instance
integrated_credit_service = IntegratedCreditService()

def calculate_credits_needed(text_length):
    """Calculate credits needed based on text length (1 credit per ~100 words)"""
    words = len(text_length.split()) if isinstance(text_length, str) else text_length
    return max(1, (words + 99) // 100)  # Round up to nearest credit