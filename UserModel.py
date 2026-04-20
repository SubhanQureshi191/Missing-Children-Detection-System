from db import db
class UserModel(db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    cnic = db.Column(db.String(15), unique=True)
    role = db.Column(db.String(15))  # 1=Reporter, 2=Finder, 3=Adopter, 4=Foster, 5=Police
    image_path = db.Column(db.String(200))
    phone = db.Column(db.String(11), unique=True)
    address = db.Column(db.String(300))
    password = db.Column(db.String(100))
    police_station_id = db.Column(db.Integer, db.ForeignKey("PoliceStations.id"), nullable=True)
    reports = db.relationship("ReportsModel", back_populates="user", lazy=True)
    parents = db.relationship("ParentModel", back_populates="user_rls", lazy=True)
    police_station = db.relationship("PoliceModel", back_populates="police_users", lazy=True)