from db import db


class PoliceModel(db.Model):
    __tablename__ = "PoliceStations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pid = db.Column(db.String(50), unique=True, nullable=False)
    pname = db.Column(db.String(100), nullable=False)
    contact_no = db.Column(db.String(20))
    location = db.Column(db.String(255))
    address = db.Column(db.String(255))

    # ✅ New columns for zone
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    assigned_reports = db.relationship("ReportsModel", back_populates="police_station", lazy=True)
    police_users = db.relationship("UserModel", back_populates="police_station", lazy=True)