from db import db
from datetime import datetime

class ParentModel(db.Model):
    __tablename__ = "Parent"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id"), unique=True)
    cnic_file = db.Column(db.String(500))
    cnic_number = db.Column(db.String(50))
    full_name = db.Column(db.String(255))
    marital_status = db.Column(db.String(50))
    husband_age = db.Column(db.Integer)
    wife_age = db.Column(db.Integer)
    occupation = db.Column(db.String(255))
    income = db.Column(db.String(100))
    boys_count = db.Column(db.Integer, default=0)
    girls_count = db.Column(db.Integer, default=0)
    ethnicity = db.Column(db.String(100))
    address = db.Column(db.String(500))
    frc_file_path = db.Column(db.String(500))
    phone_no = db.Column(db.String(20))
    police_certificate_path = db.Column(db.String(500))
    religion = db.Column(db.String(100))

    # Relationships
    requests = db.relationship("RequestModel", back_populates="parent_rls", lazy=True)
    user_rls = db.relationship("UserModel", backref="parent_profile")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "cnic_number": self.cnic_number,
            "full_name": self.full_name,
            "marital_status": self.marital_status,
            "husband_age": self.husband_age,
            "wife_age": self.wife_age,
            "occupation": self.occupation,
            "income": self.income,
            "boys_count": self.boys_count,
            "girls_count": self.girls_count,
            "ethnicity": self.ethnicity,
            "address": self.address,
            "phone_no": self.phone_no,
            "religion": self.religion,
            "has_frc": bool(self.frc_file_path),
            "has_police_cert": bool(self.police_certificate_path)
        }