# ChildAllocationController.py - COMPLETE UPDATED VERSION

from flask import request, jsonify
from db import db
from models.ChildAllocationModel import ChildAllocationModel
from models.ChildAdmissionModel import ChildAdmissionModel
from models.ChildModel import ChildModel
from models.ParentModel import ParentModel
from models.EdhiModel import EdhiModel
from models.RequestModel import RequestModel
from models.ReportsModel import ReportsModel
from datetime import datetime, timedelta
from controllers.NotificationController import NotificationController


class ChildAllocationController:

    @staticmethod
    def allocate_child_to_parent():
        try:
            data = request.get_json()
            print("=" * 60)
            print("📥 ALLOCATE CHILD TO PARENT")
            print("=" * 60)
            print(data)

            request_id = data.get('request_id')
            child_id = data.get('child_id')
            parent_id = data.get('parent_id')
            edhi_id = data.get('edhi_id')
            allocation_type = data.get('allocation_type', 'adoption')

            # Validate required fields
            if not all([request_id, child_id, parent_id, edhi_id]):
                return jsonify({
                    'success': False,
                    'message': 'Missing required fields: request_id, child_id, parent_id, edhi_id'
                }), 400

            # Get child details
            child = ChildModel.query.get(child_id)
            if not child:
                return jsonify({'success': False, 'message': 'Child not found'}), 404

            # Get parent details
            parent = ParentModel.query.get(parent_id)
            if not parent:
                return jsonify({'success': False, 'message': 'Parent not found'}), 404

            # Get admission record for the child
            admission = ChildAdmissionModel.query.filter_by(
                child_id=child_id,
                edhi_id=edhi_id,
                status='admitted'
            ).first()

            if not admission:
                return jsonify({'success': False, 'message': 'Child admission record not found'}), 404

            print(f"👶 Child: {child.name}")
            print(f"👤 Parent: {parent.full_name}")
            print(f"🏥 Edhi ID: {edhi_id}")
            print(f"📋 Request ID: {request_id}")
            print(f"📌 Admission ID: {admission.id}")

            # Check if child is already allocated
            existing_allocation = ChildAllocationModel.query.filter_by(
                child_id=child_id,
                status='active'
            ).first()

            if existing_allocation:
                return jsonify({'success': False, 'message': 'Child is already allocated to another parent'}), 400

            # Create allocation
            allocation = ChildAllocationModel(
                child_id=child_id,
                admission_id=admission.id,
                parent_id=parent_id,
                edhi_center_id=edhi_id,
                allocation_type=allocation_type,
                allocation_date=datetime.utcnow(),
                status='active',
                remarks=f'Allocated from request {request_id}'
            )

            if allocation_type == 'adoption':
                allocation.adoption_approval_date = datetime.utcnow()
                allocation.adoption_completion_date = datetime.utcnow() + timedelta(days=180)
            elif allocation_type == 'foster':
                allocation.review_date = datetime.utcnow() + timedelta(days=90)

            db.session.add(allocation)

            # Update admission record
            admission.allocated_to_parent_id = parent_id
            admission.allocation_date = datetime.utcnow()
            admission.allocation_type = allocation_type
            admission.status = 'allocated'

            # Update request status
            request_obj = RequestModel.query.get(request_id)
            if request_obj:
                request_obj.status = 'Completed'

            # Update child status
            child.status = 'allocated'

            db.session.commit()

            print(f"✅ Allocation created with ID: {allocation.id}")

            # ✅ Send notification to parent about allocation
            try:
                notification_data = {
                    'allocation_id': allocation.id,
                    'child_id': child_id,
                    'child_name': child.name,
                    'parent_id': parent_id,
                    'allocation_type': allocation_type
                }

                NotificationController.create_notification(
                    edhi_id=edhi_id,
                    user_id=parent.user_id,
                    notification_type='allocation_complete',
                    title='🎉 Child Allocated Successfully!',
                    message=f'Congratulations! Child "{child.name}" has been officially allocated to you. Please visit the Edhi center to complete the documentation.',
                    priority='high',
                    extra_data=notification_data
                )
                print("✅ Parent notification sent")
            except Exception as e:
                print(f"⚠️ Failed to send parent notification: {str(e)}")

            # ✅ Send notification to Edhi center
            try:
                NotificationController.create_notification_for_edhi(
                    edhi_id=edhi_id,
                    notification_type='child_allocated',
                    title='Child Allocated',
                    message=f'Child "{child.name}" has been allocated to {parent.full_name} for {allocation_type}.',
                    extra_data={
                        'allocation_id': allocation.id,
                        'child_id': child_id,
                        'child_name': child.name,
                        'parent_id': parent_id,
                        'parent_name': parent.full_name,
                        'allocation_type': allocation_type
                    }
                )
                print("✅ Edhi notification sent")
            except Exception as e:
                print(f"⚠️ Failed to send Edhi notification: {str(e)}")

            return jsonify({
                'success': True,
                'message': f'Child "{child.name}" allocated to {parent.full_name} successfully',
                'data': {
                    'allocation_id': allocation.id,
                    'child_id': child_id,
                    'child_name': child.name,
                    'parent_id': parent_id,
                    'parent_name': parent.full_name,
                    'allocation_type': allocation_type,
                    'allocation_date': allocation.allocation_date.isoformat() if allocation.allocation_date else None,
                    'status': allocation.status
                }
            }), 201

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in allocate_child_to_parent: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_edhi_allocated_children(edhi_id):
        """Get all children allocated from a specific Edhi center"""
        try:
            allocations = ChildAllocationModel.query.filter_by(
                edhi_center_id=edhi_id
            ).order_by(ChildAllocationModel.allocation_date.desc()).all()

            result = []
            for allocation in allocations:
                child = ChildModel.query.get(allocation.child_id)
                parent = ParentModel.query.get(allocation.parent_id)

                result.append({
                    'id': allocation.id,
                    'child_id': allocation.child_id,
                    'child_name': child.name if child else 'Unknown',
                    'child_age': child.age if child else None,
                    'child_gender': child.gender if child else None,
                    'child_image': child.image_path if child else None,
                    'parent_id': allocation.parent_id,
                    'parent_name': parent.full_name if parent else 'Unknown',
                    'parent_phone': parent.phone_no if parent else None,
                    'parent_address': parent.address if parent else None,
                    'parent_cnic': parent.cnic_number if parent else None,
                    'parent_occupation': parent.occupation if parent else None,
                    'parent_income': parent.income if parent else None,
                    'parent_marital_status': parent.marital_status if parent else None,
                    'parent_husband_age': parent.husband_age if parent else None,
                    'parent_wife_age': parent.wife_age if parent else None,
                    'parent_boys_count': parent.boys_count if parent else 0,
                    'parent_girls_count': parent.girls_count if parent else 0,
                    'parent_ethnicity': parent.ethnicity if parent else None,
                    'parent_religion': parent.religion if parent else None,
                    'allocation_type': allocation.allocation_type,
                    'allocation_date': allocation.allocation_date.isoformat() if allocation.allocation_date else None,
                    'status': allocation.status
                })

            return jsonify({
                'success': True,
                'data': result,
                'count': len(result)
            }), 200

        except Exception as e:
            print(f"❌ Error in get_edhi_allocated_children: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_parent_allocated_children(parent_id):
        """Get all children allocated to a specific parent"""
        try:
            allocations = ChildAllocationModel.query.filter_by(
                parent_id=parent_id
            ).order_by(ChildAllocationModel.allocation_date.desc()).all()

            result = []
            for allocation in allocations:
                child = ChildModel.query.get(allocation.child_id)
                parent = ParentModel.query.get(allocation.parent_id)

                result.append({
                    'id': allocation.id,
                    'child_id': allocation.child_id,
                    'child_name': child.name if child else 'Unknown',
                    'child_age': child.age if child else None,
                    'child_gender': child.gender if child else None,
                    'child_image': child.image_path if child else None,
                    'parent_id': allocation.parent_id,
                    'parent_name': parent.full_name if parent else 'Unknown',
                    'allocation_type': allocation.allocation_type,
                    'allocation_date': allocation.allocation_date.isoformat() if allocation.allocation_date else None,
                    'status': allocation.status
                })

            return jsonify({
                'success': True,
                'data': result,
                'count': len(result)
            }), 200

        except Exception as e:
            print(f"Error in get_parent_allocated_children: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_child_allocation_details(allocation_id):
        """Get detailed information about a specific allocation"""
        try:
            allocation = ChildAllocationModel.query.get(allocation_id)
            if not allocation:
                return jsonify({'success': False, 'message': 'Allocation not found'}), 404

            child = ChildModel.query.get(allocation.child_id)
            parent = ParentModel.query.get(allocation.parent_id)
            admission = ChildAdmissionModel.query.get(allocation.admission_id)

            result = {
                'id': allocation.id,
                'child_id': allocation.child_id,
                'child_name': child.name if child else 'Unknown',
                'child_age': child.age if child else None,
                'child_gender': child.gender if child else None,
                'child_image': child.image_path if child else None,
                'parent_id': allocation.parent_id,
                'parent_name': parent.full_name if parent else 'Unknown',
                'parent_phone': parent.phone_no if parent else None,
                'parent_address': parent.address if parent else None,
                'allocation_type': allocation.allocation_type,
                'allocation_date': allocation.allocation_date.isoformat() if allocation.allocation_date else None,
                'status': allocation.status,
                'admission_date': admission.admission_date.isoformat() if admission and admission.admission_date else None
            }

            return jsonify({
                'success': True,
                'data': result
            }), 200

        except Exception as e:
            print(f"Error in get_child_allocation_details: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def update_allocation_status(allocation_id):
        """Update allocation status (complete, terminate, etc.)"""
        try:
            data = request.get_json()
            new_status = data.get('status')
            remarks = data.get('remarks', '')

            if not new_status:
                return jsonify({'success': False, 'message': 'Status is required'}), 400

            allocation = ChildAllocationModel.query.get(allocation_id)
            if not allocation:
                return jsonify({'success': False, 'message': 'Allocation not found'}), 404

            old_status = allocation.status
            allocation.status = new_status

            if remarks:
                allocation.remarks = remarks

            if new_status in ['completed', 'terminated']:
                if allocation.admission:
                    allocation.admission.status = 'returned_to_parent'
                    allocation.admission.return_date = datetime.utcnow()
                    allocation.admission.return_remarks = f"Allocation {new_status}: {remarks}"
                if allocation.child:
                    allocation.child.status = 'available'

            db.session.commit()

            return jsonify({
                'success': True,
                'message': f'Allocation status updated from {old_status} to {new_status}',
                'data': {'id': allocation.id, 'status': allocation.status}
            }), 200

        except Exception as e:
            db.session.rollback()
            print(f"Error in update_allocation_status: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_all_allocations():
        """Get all allocations with filters (admin view)"""
        try:
            allocation_type = request.args.get('type')
            status = request.args.get('status')
            edhi_id = request.args.get('edhi_id')

            query = ChildAllocationModel.query

            if allocation_type:
                query = query.filter_by(allocation_type=allocation_type)
            if status:
                query = query.filter_by(status=status)
            if edhi_id:
                query = query.filter_by(edhi_center_id=edhi_id)

            allocations = query.order_by(ChildAllocationModel.allocation_date.desc()).all()

            result = []
            for allocation in allocations:
                child = ChildModel.query.get(allocation.child_id)
                parent = ParentModel.query.get(allocation.parent_id)
                result.append({
                    'id': allocation.id,
                    'child_id': allocation.child_id,
                    'child_name': child.name if child else 'Unknown',
                    'parent_name': parent.full_name if parent else 'Unknown',
                    'allocation_type': allocation.allocation_type,
                    'allocation_date': allocation.allocation_date.isoformat() if allocation.allocation_date else None,
                    'status': allocation.status
                })

            return jsonify({
                'success': True,
                'data': result,
                'count': len(result),
                'filters': {
                    'type': allocation_type,
                    'status': status,
                    'edhi_id': edhi_id
                }
            }), 200

        except Exception as e:
            print(f"Error in get_all_allocations: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_foster_care_reviews():
        """Get foster care cases that need review"""
        try:
            today = datetime.utcnow().date()
            upcoming_reviews = ChildAllocationModel.query.filter(
                ChildAllocationModel.allocation_type == 'foster',
                ChildAllocationModel.status == 'active'
            ).order_by(ChildAllocationModel.allocation_date).all()

            result = []
            for allocation in upcoming_reviews:
                child = ChildModel.query.get(allocation.child_id)
                parent = ParentModel.query.get(allocation.parent_id)
                review_date = allocation.allocation_date + timedelta(days=90) if allocation.allocation_date else None
                days_until_review = (review_date - datetime.utcnow()).days if review_date else None

                result.append({
                    'id': allocation.id,
                    'child_name': child.name if child else 'Unknown',
                    'child_age': child.age if child else None,
                    'parent_name': parent.full_name if parent else 'Unknown',
                    'allocation_date': allocation.allocation_date.isoformat() if allocation.allocation_date else None,
                    'review_date': review_date.isoformat() if review_date else None,
                    'days_until_review': days_until_review,
                    'review_status': 'overdue' if days_until_review and days_until_review < 0 else 'upcoming'
                })

            return jsonify({
                'success': True,
                'data': result,
                'count': len(result)
            }), 200

        except Exception as e:
            print(f"Error in get_foster_care_reviews: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)}), 500