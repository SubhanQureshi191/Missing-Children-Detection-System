from db import db

class ChildImageModel(db.Model):
    __tablename__ = "ChildImages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    child_id = db.Column(db.Integer, db.ForeignKey("Child.id"), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    child = db.relationship("ChildModel", back_populates="images")