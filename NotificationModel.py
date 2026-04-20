# models/NotificationModel.py
from db import db
from datetime import datetime
import json


class NotificationModel(db.Model):
    __tablename__ = "Notifications"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    edhi_id = db.Column(db.Integer, db.ForeignKey("Edhi.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=True)
    type = db.Column(db.String(50))
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    priority = db.Column(db.String(20), default="medium")
    is_read = db.Column(db.Boolean, default=False)
    extra_data = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    edhi_center = db.relationship("EdhiModel", backref="notifications")
    user = db.relationship("UserModel", backref="notifications")

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "priority": self.priority,
            "is_read": self.is_read,
            "extra_data": json.loads(self.extra_data) if self.extra_data else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "time_ago": self.get_time_ago()
        }

    def get_time_ago(self):
        if not self.created_at:
            return "Just now"
        now = datetime.utcnow()
        diff = now - self.created_at
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"