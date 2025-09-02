from app import db
from datetime import datetime, timedelta
import secrets
import string

class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_code = db.Column(db.String(8), unique=True, nullable=False)
    quantum_key = db.Column(db.Text, nullable=True)
    key_generated_at = db.Column(db.DateTime, nullable=True)
    encryption_method = db.Column(db.String(20), default='xor')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    messages_count = db.Column(db.Integer, default=0)
    
    # Analytics fields
    total_messages = db.Column(db.Integer, default=0)
    key_refreshes = db.Column(db.Integer, default=0)
    security_events_count = db.Column(db.Integer, default=0)
    
    @staticmethod
    def generate_session_code():
        """Generate a unique 8-character session code"""
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if not ChatSession.query.filter_by(session_code=code).first():
                return code
    
    def is_key_expired(self):
        """Check if quantum key is expired (5 minutes)"""
        if not self.key_generated_at:
            return True
        return datetime.utcnow() > self.key_generated_at + timedelta(minutes=5)
    
    def key_time_remaining(self):
        """Get remaining time for key in seconds"""
        if not self.key_generated_at or self.is_key_expired():
            return 0
        expiry_time = self.key_generated_at + timedelta(minutes=5)
        remaining = expiry_time - datetime.utcnow()
        return max(0, int(remaining.total_seconds()))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    sender = db.Column(db.String(20), nullable=False)  # 'alice' or 'bob'
    original_message = db.Column(db.Text, nullable=False)
    encrypted_message = db.Column(db.Text, nullable=False)
    is_self_destruct = db.Column(db.Boolean, default=False)
    self_destruct_timer = db.Column(db.Integer, default=30)  # seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    is_destroyed = db.Column(db.Boolean, default=False)
    
    session = db.relationship('ChatSession', backref=db.backref('messages', lazy=True))
    
    def should_self_destruct(self):
        """Check if message should self-destruct"""
        if not self.is_self_destruct or self.is_destroyed:
            return False
        
        # Destruct after timer expires
        if datetime.utcnow() > self.created_at + timedelta(seconds=self.self_destruct_timer):
            return True
        
        # Destruct immediately when read (if timer is 0)
        if self.self_destruct_timer == 0 and self.read_at:
            return True
        
        return False
    
    def time_until_destruction(self):
        """Get time remaining until self-destruction in seconds"""
        if not self.is_self_destruct or self.is_destroyed:
            return None
        
        destruction_time = self.created_at + timedelta(seconds=self.self_destruct_timer)
        remaining = destruction_time - datetime.utcnow()
        return max(0, int(remaining.total_seconds()))

class SecurityEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # 'key_generation', 'message_sent', 'hacker_simulation', etc.
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    session = db.relationship('ChatSession', backref=db.backref('security_events', lazy=True))
