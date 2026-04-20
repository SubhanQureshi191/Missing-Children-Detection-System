from db import db

# FIX: Class name sahi kiya - pehle EdhiModel likha tha
class GrantsCustodyModel(db.Model):
    __tablename__ = "GrantCustody"  # Table name bhi change kiya

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Add your fields here
    # request_id = db.Column(db.Integer, db.ForeignKey("Request.id"))
    # status = db.Column(db.String(50))
    # date = db.Column(db.String(20))