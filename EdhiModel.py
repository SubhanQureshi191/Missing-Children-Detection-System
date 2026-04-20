from db import db

class EdhiModel(db.Model):
    __tablename__ = "Edhi"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id"), unique=True)
    name = db.Column(db.String(100))
    contact = db.Column(db.String(15))
    address = db.Column(db.String(200))  # ✅ Changed from location to address
    latitude = db.Column(db.DECIMAL(10, 8))
    longitude = db.Column(db.DECIMAL(11, 8))

    # Relationships
    requests = db.relationship("RequestModel", back_populates="edhi_rls", lazy="dynamic")
    user = db.relationship("UserModel", backref="edhi_center")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "contact": self.contact,
            "address": self.address,  # ✅ Changed from location to address
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None
        }