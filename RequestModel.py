# models/RequestModel.py
from db import db
from datetime import datetime

class RequestModel(db.Model):
    __tablename__ = "Request"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("Parent.id"))
    edhi_id = db.Column(db.Integer, db.ForeignKey("Edhi.id"))
    request_type = db.Column(db.String(50))
    child_age_preference = db.Column(db.Integer)  # Preferred age
    child_gender_preference = db.Column(db.String(20))
    reason = db.Column(db.Text)
    child_ethnicity = db.Column(db.String(100))
    child_religion = db.Column(db.String(100))
    address = db.Column(db.String(500))
    latitude = db.Column(db.DECIMAL(10, 8))
    longitude = db.Column(db.DECIMAL(11, 8))
    status = db.Column(db.String(50), default='Pending')
    request_date = db.Column(db.DateTime, default=datetime.now)
    remarks = db.Column(db.Text)

    # Relationships
    parent_rls = db.relationship("ParentModel", back_populates="requests")
    edhi_rls = db.relationship("EdhiModel", back_populates="requests")

    def to_dict(self):
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "edhi_id": self.edhi_id,
            "request_type": self.request_type,
            "child_age_preference": self.child_age_preference,
            "child_gender_preference": self.child_gender_preference,
            "reason": self.reason,
            "child_ethnicity": self.child_ethnicity,
            "child_religion": self.child_religion,
            "address": self.address,
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
            "status": self.status,
            "request_date": self.request_date.isoformat() if self.request_date else None,
            "remarks": self.remarks,
            "parent": {
                "id": self.parent_rls.id if self.parent_rls else None,
                "name": self.parent_rls.full_name if self.parent_rls else None,
                "cnic": self.parent_rls.cnic_number if self.parent_rls else None,
                "occupation": self.parent_rls.occupation if self.parent_rls else None,
                "income": self.parent_rls.income if self.parent_rls else None,
                "address": self.parent_rls.address if self.parent_rls else None,
                "phone": self.parent_rls.phone_no if self.parent_rls else None
            } if self.parent_rls else None
        }