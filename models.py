from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import func, Text, Boolean
import secrets
import string

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=True)  # Made nullable for Google OAuth
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=True)  # Full name for sukusuku.ai integration
    # ensure password hash field has length of at least 256
    password_hash = db.Column(db.String(256), nullable=True)  # Made nullable for Google OAuth
    google_id = db.Column(db.String(100), unique=True, nullable=True)  # Google OAuth ID
    credits = db.Column(db.Integer, default=10, nullable=False)  # Start with 10 free credits
    total_credits = db.Column(db.Integer, default=10, nullable=False)  # Original credits allocated
    memory_used = db.Column(db.Float, default=0.0, nullable=False)  # Memory used in MB
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    generations = db.relationship('Generation', backref='user', lazy=True)
    
    def deduct_credits(self, amount):
        """Deduct credits from user account if sufficient balance exists"""
        if self.credits >= amount:
            self.credits -= amount
            return True
        return False
    
    def add_credits(self, amount):
        """Add credits to user account"""
        self.credits += amount
    
    def get_storage_used(self):
        """Calculate total storage used by user's workspace projects in MB"""
        # Import here to avoid circular import
        from models import WorkspaceProject
        total_storage = db.session.query(func.sum(WorkspaceProject.storage_size)).filter(
            WorkspaceProject.user_id == self.id,
            WorkspaceProject.is_deleted == False
        ).scalar()
        return round((total_storage or 0) / (1024 * 1024), 2)  # Convert bytes to MB
    
    def get_storage_remaining(self):
        """Get remaining storage in MB (1MB default limit)"""
        return max(0, 1.0 - self.get_storage_used())

class CreditPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Integer, default=0)  # Percentage discount
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CreditPackage {self.name}: {self.credits} credits for ${self.price}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'purchase', 'deduction'
    amount = db.Column(db.Integer, nullable=False)  # Credits amount
    description = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # For purchases
    package_id = db.Column(db.Integer, db.ForeignKey('credit_package.id'), nullable=True)
    price_paid = db.Column(db.Float, nullable=True)
    


class Generation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    generation_type = db.Column(db.String(20), nullable=False)  # 'single', 'story', 'file_upload'
    prompt = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    credits_used = db.Column(db.Integer, nullable=False)
    model_used = db.Column(db.String(100), nullable=True)  # AI model used
    output_length = db.Column(db.String(20), default='medium')  # short, medium, long
    word_count = db.Column(db.Integer, nullable=True)  # Word count of generated content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # For story generations
    chapter_count = db.Column(db.Integer, nullable=True)
    title = db.Column(db.String(200), nullable=True)
    
    def get_preview(self, length=150):
        """Get a preview of the generated content"""
        if len(self.content) <= length:
            return self.content
        return self.content[:length] + "..."


class WorkspaceProject(db.Model):
    """Model for user's workspace projects - saves all generations with full CRUD functionality"""
    __tablename__ = 'workspace_project'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)  # No foreign key constraint for SSO compatibility
    project_title = db.Column(db.String(200), nullable=False)
    generation_text = db.Column(Text, nullable=False)
    code = db.Column(db.String(6), nullable=False, unique=True)  # 6-digit alphanumeric code
    storage_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    is_deleted = db.Column(Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.code:
            self.code = self.generate_unique_code()
        self.calculate_storage_size()
    
    @staticmethod
    def generate_unique_code():
        """Generate a unique 6-digit alphanumeric code"""
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            if not WorkspaceProject.query.filter_by(code=code).first():
                return code
    
    def calculate_storage_size(self):
        """Calculate storage size in bytes"""
        if self.project_title and self.generation_text:
            # Calculate size of title + text + metadata
            text_size = len(self.project_title.encode('utf-8')) + len(self.generation_text.encode('utf-8'))
            # Add some overhead for metadata
            self.storage_size = text_size + 1024  # 1KB overhead
    
    def update_content(self, title, text):
        """Update project content and recalculate storage"""
        self.project_title = title
        self.generation_text = text
        self.calculate_storage_size()
        self.updated_at = datetime.utcnow()
    
    def get_storage_mb(self):
        """Get storage size in MB"""
        return round(self.storage_size / (1024 * 1024), 3)
    
    def soft_delete(self):
        """Soft delete the project"""
        self.is_deleted = True
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<WorkspaceProject {self.code}: {self.project_title[:30]}...>'


class Workspace(db.Model):
    """Enhanced Workspace table as per checklist requirements"""
    __tablename__ = 'workspace'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    text = db.Column(Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    model_used = db.Column(db.String(100), nullable=True)  # Which AI model was used
    one_time_code = db.Column(db.String(8), nullable=False, unique=True)  # Unique access code
    size = db.Column(db.Float, nullable=False, default=0.0)  # Size in MB
    output_length = db.Column(db.String(20), default='medium')  # short, medium, long
    is_deleted = db.Column(Boolean, default=False, nullable=False)
    credits_used = db.Column(db.Integer, default=1, nullable=False)  # Credits used for this generation
    regeneration_count = db.Column(db.Integer, default=0, nullable=False)  # How many times regenerated
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.one_time_code:
            self.one_time_code = self.generate_unique_code()
        self.calculate_size()
    
    @staticmethod
    def generate_unique_code():
        """Generate a unique 8-character alphanumeric code"""
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if not Workspace.query.filter_by(one_time_code=code).first():
                return code
    
    def calculate_size(self):
        """Calculate size in MB"""
        if self.title and self.text:
            text_size = len(self.title.encode('utf-8')) + len(self.text.encode('utf-8'))
            self.size = round(text_size / (1024 * 1024), 4)  # Convert to MB
    
    def update_content(self, title, text):
        """Update workspace content and recalculate size"""
        self.title = title
        self.text = text
        self.calculate_size()
        self.timestamp = datetime.utcnow()
    
    def soft_delete(self):
        """Soft delete the workspace item"""
        self.is_deleted = True
    
    def get_preview(self, length=100):
        """Get a preview of the text content"""
        if len(self.text) <= length:
            return self.text
        return self.text[:length] + "..."
    
    def __repr__(self):
        return f'<Workspace {self.one_time_code}: {self.title[:30]}...>'
