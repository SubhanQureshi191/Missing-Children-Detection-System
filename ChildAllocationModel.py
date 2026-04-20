# models/ChildAllocationModel.py

from db import db
from datetime import datetime


class ChildAllocationModel(db.Model):
    """Model to track child allocations to parents (adoption/foster care)"""
    __tablename__ = "ChildAllocation"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    child_id = db.Column(db.Integer, db.ForeignKey("Child.id"), nullable=False)
    admission_id = db.Column(db.Integer, db.ForeignKey("ChildAdmission.id"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("Parent.id"), nullable=False)
    edhi_center_id = db.Column(db.Integer, db.ForeignKey("Edhi.id"), nullable=False)

    # Allocation details
    allocation_type = db.Column(db.String(20), nullable=False)  # 'adoption' or 'foster'
    allocation_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # 'active', 'completed', 'terminated'

    # Foster care specific fields
    foster_start_date = db.Column(db.DateTime, nullable=True)
    foster_end_date = db.Column(db.DateTime, nullable=True)
    foster_duration_months = db.Column(db.Integer, nullable=True)
    review_date = db.Column(db.DateTime, nullable=True)

    # Adoption specific fields
    adoption_approval_date = db.Column(db.DateTime, nullable=True)
    adoption_completion_date = db.Column(db.DateTime, nullable=True)

    # General fields
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    child = db.relationship("ChildModel", backref="allocations", foreign_keys=[child_id])
    admission = db.relationship("ChildAdmissionModel", backref="allocation", foreign_keys=[admission_id])
    parent = db.relationship("ParentModel", backref="allocations", foreign_keys=[parent_id])
    edhi_center = db.relationship("EdhiModel", backref="allocations", foreign_keys=[edhi_center_id])

    def to_dict(self):
        """Basic dictionary representation"""
        return {
            'id': self.id,
            'child_id': self.child_id,
            'admission_id': self.admission_id,
            'parent_id': self.parent_id,
            'edhi_center_id': self.edhi_center_id,
            'allocation_type': self.allocation_type,
            'allocation_date': self.allocation_date.isoformat() if self.allocation_date else None,
            'status': self.status,
            'foster_start_date': self.foster_start_date.isoformat() if self.foster_start_date else None,
            'foster_end_date': self.foster_end_date.isoformat() if self.foster_end_date else None,
            'foster_duration_months': self.foster_duration_months,
            'review_date': self.review_date.isoformat() if self.review_date else None,
            'adoption_approval_date': self.adoption_approval_date.isoformat() if self.adoption_approval_date else None,
            'adoption_completion_date': self.adoption_completion_date.isoformat() if self.adoption_completion_date else None,
            'remarks': self.remarks,
            'child_name': self.child.name if self.child else None,
            'parent_name': self.parent.full_name if self.parent else None,
            'edhi_center_name': self.edhi_center.name if self.edhi_center else None
        }

    def to_dict_detailed(self):
        """Detailed dictionary with full child and parent info"""
        data = self.to_dict()

        # Add detailed child info
        if self.child:
            child_images = []
            if hasattr(self.child, 'images') and self.child.images:
                child_images = [img.image_path for img in self.child.images]

            data['child_details'] = {
                'id': self.child.id,
                'name': self.child.name,
                'age': self.child.age,
                'gender': self.child.gender,
                'images': child_images
            }

        # Add detailed parent info
        if self.parent:
            data['parent_details'] = {
                'id': self.parent.id,
                'full_name': self.parent.full_name,
                'cnic_number': self.parent.cnic_number,
                'phone_no': self.parent.phone_no,
                'address': self.parent.address,
                'occupation': self.parent.occupation,
                'marital_status': self.parent.marital_status
            }

        # Add admission info
        if self.admission:
            data['admission_details'] = {
                'id': self.admission.id,
                'admission_date': self.admission.admission_date.isoformat() if self.admission.admission_date else None,
                'police_station_name': self.admission.police_station.pname if self.admission.police_station else None,
                'status': self.admission.status
            }

        return data