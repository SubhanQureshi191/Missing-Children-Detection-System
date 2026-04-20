from db import db
from datetime import datetime


class MatchAlertModel(db.Model):
    __tablename__ = "MatchAlerts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Which two reports matched
    missing_report_id = db.Column(db.Integer, db.ForeignKey("Report.id"), nullable=False)
    found_report_id = db.Column(db.Integer, db.ForeignKey("Report.id"), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey("Child.id"), nullable=False)

    # Match details
    match_score = db.Column(db.Float, nullable=False)  # 0-100% similarity
    match_status = db.Column(db.String(50), default='pending')  # pending, verified, rejected

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships (optional but useful)
    missing_report = db.relationship("ReportsModel", foreign_keys=[missing_report_id])
    found_report = db.relationship("ReportsModel", foreign_keys=[found_report_id])
    child = db.relationship("ChildModel")