from db import db
from datetime import datetime


class ChildAdmissionModel(db.Model):
    __tablename__ = "ChildAdmission"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Child Information
    child_id = db.Column(db.Integer, db.ForeignKey("Child.id"), nullable=False)

    # Report Information
    report_id = db.Column(db.Integer, db.ForeignKey("Report.id"), nullable=False)

    # Police Station Information (who sent the child)
    police_station_id = db.Column(db.Integer, db.ForeignKey("PoliceStations.id"), nullable=False)

    # Edhi Center Information (where child is admitted)
    edhi_id = db.Column(db.Integer, db.ForeignKey("Edhi.id"), nullable=False)

    # Admission Details
    admission_date = db.Column(db.DateTime, default=datetime.utcnow)
    admission_remarks = db.Column(db.Text, nullable=True)

    # Current Status
    status = db.Column(db.String(50), default="admitted")  # admitted, allocated, adopted, fostered, returned_to_parent

    # Transfer Details
    transferred_by_user_id = db.Column(db.Integer, db.ForeignKey("Users.id"), nullable=True)

    # Allocation Details (if child is allocated to a parent)
    allocated_to_parent_id = db.Column(db.Integer, db.ForeignKey("Parent.id"), nullable=True)
    allocation_date = db.Column(db.DateTime, nullable=True)
    allocation_type = db.Column(db.String(20), nullable=True)  # adoption, foster

    # Return Details (if returned to parents)
    return_date = db.Column(db.DateTime, nullable=True)
    return_remarks = db.Column(db.Text, nullable=True)

    # Tracking fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    child = db.relationship("ChildModel", backref="admissions")
    report = db.relationship("ReportsModel", backref="admissions")
    police_station = db.relationship("PoliceModel", backref="child_admissions")
    edhi_center = db.relationship("EdhiModel", backref="child_admissions")
    transferred_by = db.relationship("UserModel", backref="transferred_children")
    allocated_parent = db.relationship("ParentModel", backref="allocated_children")

    def to_dict(self):
        return {
            "id": self.id,
            "child_id": self.child_id,
            "child_name": self.child.name if self.child else None,
            "report_id": self.report_id,
            "police_station_id": self.police_station_id,
            "police_station_name": self.police_station.pname if self.police_station else None,
            "edhi_id": self.edhi_id,
            "edhi_name": self.edhi_center.name if self.edhi_center else None,
            "admission_date": self.admission_date.isoformat() if self.admission_date else None,
            "admission_remarks": self.admission_remarks,
            "status": self.status,
            "transferred_by_user_id": self.transferred_by_user_id,
            "allocated_to_parent_id": self.allocated_to_parent_id,
            "allocation_date": self.allocation_date.isoformat() if self.allocation_date else None,
            "allocation_type": self.allocation_type,
            "return_date": self.return_date.isoformat() if self.return_date else None,
            "return_remarks": self.return_remarks
        }