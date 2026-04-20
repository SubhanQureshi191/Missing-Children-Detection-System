from db import db


class ChildModel(db.Model):
    __tablename__ = "Child"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    image_path = db.Column(db.String(500))
    religion = db.Column(db.String(100))
    identification_mark = db.Column(db.String(255))
    address = db.Column(db.String(500))
    clothes = db.Column(db.String(255))
    disability = db.Column(db.String(255))
    ethnicity = db.Column(db.String(50))  # For ethnicity preference

    # Location fields
    last_seen_latitude = db.Column(db.Float, nullable=True)
    last_seen_longitude = db.Column(db.Float, nullable=True)
    last_seen_location = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(50), default="Reported")
    # ✅ Relationship with ChildImageModel
    images = db.relationship("ChildImageModel", back_populates="child", cascade="all, delete-orphan")

    # Existing relationships
    reports = db.relationship("ReportsModel", back_populates="child", lazy=True)