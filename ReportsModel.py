from db import db


class ReportsModel(db.Model):
    __tablename__ = "Report"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id"))
    child_id = db.Column(db.Integer, db.ForeignKey("Child.id"))
    status = db.Column(db.String(100))
    date = db.Column(db.String(20))
    report_type = db.Column(db.String(20))
    last_seen_location = db.Column(db.String(200))

    # ✅ Missing report ke liye coordinates
    last_seen_latitude = db.Column(db.Float, nullable=True)
    last_seen_longitude = db.Column(db.Float, nullable=True)

    found_location = db.Column(db.String(200))
    found_location_lat = db.Column(db.Float, nullable=True)
    found_location_lng = db.Column(db.Float, nullable=True)
    current_location = db.Column(db.String(200))
    assigned_police_station_id = db.Column(db.Integer, db.ForeignKey("PoliceStations.id"), nullable=True)
    assignment_status = db.Column(db.String(50), default='pending')

    user = db.relationship("UserModel", back_populates="reports")
    child = db.relationship("ChildModel", back_populates="reports")
    police_station = db.relationship("PoliceModel", back_populates="assigned_reports")