import json
from flask import jsonify, request
from db import db
from models.ChildAdmissionModel import ChildAdmissionModel
from models.ChildAllocationModel import ChildAllocationModel
from models.ChildModel import ChildModel
from models.NotificationModel import NotificationModel
from models.ReportsModel import ReportsModel
from models.PoliceModel import PoliceModel
from models.EdhiModel import EdhiModel
from models.RequestModel import RequestModel
from models.UserModel import UserModel
from models.ParentModel import ParentModel
from services.LocationService import LocationService
from datetime import datetime, timedelta
from controllers.NotificationController import NotificationController


class ChildAdmissionController:

    @staticmethod
    def transfer_child_to_edhi():
        """
        Police station se child ko Edhi center mein transfer karne ke liye
        - Nearest Edhi center automatically find karega based on child's found location
        """
        try:
            data = request.get_json()

            # Required fields
            child_id = data.get("child_id")
            report_id = data.get("report_id")
            police_station_id = data.get("police_station_id")
            user_id = data.get("user_id")
            remarks = data.get("remarks", "")

            if not all([child_id, report_id, police_station_id, user_id]):
                return jsonify({
                    "success": False,
                    "message": "Missing required fields: child_id, report_id, police_station_id, user_id"
                }), 400

            # Verify child exists
            child = ChildModel.query.get(child_id)
            if not child:
                return jsonify({"success": False, "message": "Child not found"}), 404

            # Verify report exists
            report = ReportsModel.query.get(report_id)
            if not report:
                return jsonify({"success": False, "message": "Report not found"}), 404

            # Get child's location from report
            lat = None
            lng = None

            if report.report_type == 'found':
                lat = report.found_location_lat
                lng = report.found_location_lng
            else:
                lat = report.last_seen_latitude
                lng = report.last_seen_longitude

            # Find nearest Edhi center based on coordinates
            nearest_edhi_id = None
            if lat and lng:
                nearest_edhi_id = LocationService.get_nearest_edhi_center(lat, lng)
                print(f"📍 Nearest Edhi center found: {nearest_edhi_id}")

            if not nearest_edhi_id:
                default_edhi = EdhiModel.query.first()
                if default_edhi:
                    nearest_edhi_id = default_edhi.id
                    print(f"⚠️ Using default Edhi center: {default_edhi.name}")
                else:
                    return jsonify({"success": False, "message": "No Edhi centers available"}), 400

            # Check if child already admitted
            existing_admission = ChildAdmissionModel.query.filter_by(
                child_id=child_id,
                status="admitted"
            ).first()

            if existing_admission:
                return jsonify({
                    "success": False,
                    "message": f"Child already admitted to {existing_admission.edhi_center.name}",
                    "data": existing_admission.to_dict()
                }), 400

            # Create admission record
            new_admission = ChildAdmissionModel(
                child_id=child_id,
                report_id=report_id,
                police_station_id=police_station_id,
                edhi_id=nearest_edhi_id,
                admission_remarks=remarks,
                status="admitted",
                transferred_by_user_id=user_id,
                admission_date=datetime.now()
            )

            db.session.add(new_admission)

            # Update child status
            child.status = "in_edhi_care"

            db.session.commit()

            # Get Edhi center details
            edhi_center = EdhiModel.query.get(nearest_edhi_id)

            return jsonify({
                "success": True,
                "message": f"Child {child.name} successfully transferred to {edhi_center.name}",
                "data": {
                    "admission_id": new_admission.id,
                    "child_id": child_id,
                    "child_name": child.name,
                    "edhi_center": {
                        "id": edhi_center.id,
                        "name": edhi_center.name,
                        "address": edhi_center.address,
                        "contact": edhi_center.contact,
                        "latitude": float(edhi_center.latitude) if edhi_center.latitude else None,
                        "longitude": float(edhi_center.longitude) if edhi_center.longitude else None
                    },
                    "admission_date": new_admission.admission_date.isoformat(),
                    "status": new_admission.status
                }
            }), 201

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in transfer_child_to_edhi: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_edhi_admitted_children(edhi_id):
        """Get all children admitted to a specific Edhi center"""
        try:
            admissions = ChildAdmissionModel.query.filter_by(
                edhi_id=edhi_id,
                status="admitted"
            ).order_by(ChildAdmissionModel.admission_date.desc()).all()

            result = []
            for admission in admissions:
                child = ChildModel.query.get(admission.child_id)
                result.append({
                    "admission_id": admission.id,
                    "child_id": admission.child_id,
                    "child_name": child.name if child else "Unknown",
                    "child_age": child.age if child else None,
                    "child_gender": child.gender if child else None,
                    "child_image": child.image_path if child else None,
                    "admission_date": admission.admission_date.isoformat() if admission.admission_date else None,
                    "admission_remarks": admission.admission_remarks,
                    "police_station_name": admission.police_station.pname if admission.police_station else None,
                    "status": admission.status
                })

            return jsonify({
                "success": True,
                "data": result,
                "count": len(result)
            }), 200

        except Exception as e:
            print(f"❌ Error in get_edhi_admitted_children: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_edhi_allocated_children(edhi_id):
        """Get all children allocated to parents from an Edhi center"""
        try:
            admissions = ChildAdmissionModel.query.filter_by(
                edhi_id=edhi_id,
                status="allocated"
            ).order_by(ChildAdmissionModel.allocation_date.desc()).all()

            result = []
            for admission in admissions:
                child = ChildModel.query.get(admission.child_id)
                parent = ParentModel.query.get(
                    admission.allocated_to_parent_id) if admission.allocated_to_parent_id else None

                result.append({
                    "admission_id": admission.id,
                    "child_id": admission.child_id,
                    "child_name": child.name if child else "Unknown",
                    "child_age": child.age if child else None,
                    "child_gender": child.gender if child else None,
                    "allocation_date": admission.allocation_date.isoformat() if admission.allocation_date else None,
                    "allocation_type": admission.allocation_type,
                    "parent_name": parent.full_name if parent else None,
                    "parent_phone": parent.phone_no if parent else None,
                    "status": admission.status
                })

            return jsonify({
                "success": True,
                "data": result,
                "count": len(result)
            }), 200

        except Exception as e:
            print(f"❌ Error in get_edhi_allocated_children: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def allocate_child_to_parent(admission_id):
        """
        Edhi center se child ko parent ko allocate karna (Adoption/Foster)
        """
        try:
            data = request.get_json()

            parent_id = data.get("parent_id")
            allocation_type = data.get("allocation_type")
            remarks = data.get("remarks", "")

            if not all([parent_id, allocation_type]):
                return jsonify({
                    "success": False,
                    "message": "Missing required fields: parent_id, allocation_type"
                }), 400

            if allocation_type not in ["adoption", "foster"]:
                return jsonify({
                    "success": False,
                    "message": "Invalid allocation_type. Must be 'adoption' or 'foster'"
                }), 400

            admission = ChildAdmissionModel.query.get(admission_id)
            if not admission:
                return jsonify({"success": False, "message": "Admission record not found"}), 404

            if admission.status != "admitted":
                return jsonify({
                    "success": False,
                    "message": f"Cannot allocate child. Current status is {admission.status}"
                }), 400

            parent = ParentModel.query.get(parent_id)
            if not parent:
                return jsonify({"success": False, "message": "Parent not found"}), 404

            admission.status = "allocated"
            admission.allocated_to_parent_id = parent_id
            admission.allocation_date = datetime.now()
            admission.allocation_type = allocation_type
            admission.admission_remarks = remarks

            child = ChildModel.query.get(admission.child_id)
            if child:
                child.status = f"allocated_for_{allocation_type}"

            db.session.commit()

            return jsonify({
                "success": True,
                "message": f"Child successfully allocated to {parent.full_name} for {allocation_type}",
                "data": admission.to_dict()
            }), 200

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in allocate_child_to_parent: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def return_child_to_parent(admission_id):
        """
        Child ko parents ko wapas karna (when parents reclaim the child)
        """
        try:
            data = request.get_json()
            remarks = data.get("remarks", "")

            admission = ChildAdmissionModel.query.get(admission_id)
            if not admission:
                return jsonify({"success": False, "message": "Admission record not found"}), 404

            if admission.status != "allocated":
                return jsonify({
                    "success": False,
                    "message": f"Cannot return child. Current status is {admission.status}"
                }), 400

            admission.status = "returned_to_parent"
            admission.return_date = datetime.now()
            admission.return_remarks = remarks

            child = ChildModel.query.get(admission.child_id)
            if child:
                child.status = "returned_to_parent"

            db.session.commit()

            return jsonify({
                "success": True,
                "message": f"Child successfully returned to parents",
                "data": admission.to_dict()
            }), 200

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in return_child_to_parent: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_all_admissions():
        """Get all child admissions (for admin)"""
        try:
            admissions = ChildAdmissionModel.query.order_by(
                ChildAdmissionModel.admission_date.desc()
            ).all()

            result = [admission.to_dict() for admission in admissions]

            return jsonify({
                "success": True,
                "data": result,
                "count": len(result)
            }), 200

        except Exception as e:
            print(f"❌ Error in get_all_admissions: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_police_station_transfers(police_station_id):
        """Get all transfers from a specific police station"""
        try:
            admissions = ChildAdmissionModel.query.filter_by(
                police_station_id=police_station_id
            ).order_by(ChildAdmissionModel.admission_date.desc()).all()

            result = []
            for admission in admissions:
                child = ChildModel.query.get(admission.child_id)
                result.append({
                    "admission_id": admission.id,
                    "child_id": admission.child_id,
                    "child_name": child.name if child else "Unknown",
                    "admission_date": admission.admission_date.isoformat() if admission.admission_date else None,
                    "edhi_name": admission.edhi_center.name if admission.edhi_center else None,
                    "status": admission.status
                })

            return jsonify({
                "success": True,
                "data": result,
                "count": len(result)
            }), 200

        except Exception as e:
            print(f"❌ Error in get_police_station_transfers: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def request_child_return(child_id):
        """Police station requesting Edhi center to return child"""
        try:
            print("=" * 60)
            print("📥 RECEIVED RETURN REQUEST")
            print("=" * 60)
            print(f"Child ID from URL: {child_id}")

            data = request.get_json()
            print(f"Request body: {data}")

            police_station_id = data.get("police_station_id")
            user_id = data.get("user_id")
            remarks = data.get("remarks", "")

            if not police_station_id or not user_id:
                return jsonify({
                    "success": False,
                    "message": "Missing required fields: police_station_id, user_id"
                }), 400

            child = ChildModel.query.get(child_id)
            if not child:
                return jsonify({"success": False, "message": "Child not found"}), 404

            print(f"✅ Child found: {child.name} (ID: {child.id})")

            admission = ChildAdmissionModel.query.filter_by(
                child_id=child_id,
                status="admitted"
            ).first()

            if not admission:
                return jsonify({
                    "success": False,
                    "message": "Child not currently admitted to any Edhi center"
                }), 404

            print(f"✅ Admission found - Edhi ID: {admission.edhi_id}")

            police_station = PoliceModel.query.get(police_station_id)
            police_station_name = police_station.pname if police_station else "Police Station"

            try:
                extra_data_json = json.dumps({
                    "child_id": child_id,
                    "child_name": child.name,
                    "child_age": child.age,
                    "child_gender": child.gender,
                    "police_station_id": police_station_id,
                    "police_station_name": police_station_name,
                    "admission_id": admission.id,
                    "remarks": remarks,
                    "requested_by_user_id": user_id
                })

                print(f"📝 Creating notification with extra_data: {extra_data_json}")

                notification = NotificationModel(
                    edhi_id=admission.edhi_id,
                    user_id=user_id,
                    type="return_request",
                    title="⚠️ Child Return Request",
                    message=f"Police Station '{police_station_name}' has requested to return child {child.name} (ID: {child_id}). Please prepare for handover.",
                    priority="high",
                    is_read=False,
                    extra_data=extra_data_json,
                    created_at=datetime.utcnow()
                )

                db.session.add(notification)
                db.session.commit()

                print(f"✅ Notification created! ID: {notification.id}")
                print("=" * 60)

                return jsonify({
                    "success": True,
                    "message": f"Return request sent to Edhi center for child {child.name}",
                    "data": {
                        "notification_id": notification.id,
                        "child_id": child_id,
                        "child_name": child.name,
                        "edhi_id": admission.edhi_id,
                        "police_station_name": police_station_name
                    }
                }), 200

            except Exception as e:
                db.session.rollback()
                print(f"❌ Failed to create notification: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    "success": False,
                    "message": f"Failed to create notification: {str(e)}"
                }), 500

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in request_child_return: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def allocate_child_from_request():
        """Allocate child to parent from approved request"""
        try:
            data = request.get_json()
            print("=" * 60)
            print("📥 ALLOCATE CHILD FROM REQUEST")
            print("=" * 60)
            print(data)

            request_id = data.get('request_id')
            child_id = data.get('child_id')
            parent_id = data.get('parent_id')
            edhi_id = data.get('edhi_id')
            allocation_type = data.get('allocation_type', 'adoption')

            if not request_id or not child_id or not parent_id or not edhi_id:
                return jsonify({'success': False, 'message': 'Missing required fields'}), 400

            child = ChildModel.query.get(child_id)
            if not child:
                return jsonify({'success': False, 'message': 'Child not found'}), 404

            parent = ParentModel.query.get(parent_id)
            if not parent:
                return jsonify({'success': False, 'message': 'Parent not found'}), 404

            admission = ChildAdmissionModel.query.filter_by(
                child_id=child_id,
                edhi_id=edhi_id,
                status='admitted'
            ).first()

            if not admission:
                admission = ChildAdmissionModel.query.filter_by(
                    child_id=child_id,
                    status='admitted'
                ).first()
                if admission:
                    print(f"✅ Found admission without edhi_id filter: {admission.id}")
                else:
                    return jsonify({'success': False, 'message': 'Child admission record not found'}), 404

            print(f"👶 Child: {child.name}")
            print(f"👤 Parent: {parent.full_name}")
            print(f"🏥 Edhi ID: {edhi_id}")
            print(f"📋 Request ID: {request_id}")
            print(f"📌 Admission ID: {admission.id}")

            existing_allocation = ChildAllocationModel.query.filter_by(
                child_id=child_id,
                status='active'
            ).first()

            if existing_allocation:
                return jsonify({'success': False, 'message': 'Child is already allocated to another parent'}), 400

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

            db.session.add(allocation)

            admission.allocated_to_parent_id = parent_id
            admission.allocation_date = datetime.utcnow()
            admission.allocation_type = allocation_type
            admission.status = 'allocated'

            request_obj = RequestModel.query.get(request_id)
            if request_obj:
                request_obj.status = 'Completed'

            child.status = 'allocated'

            db.session.commit()

            print(f"✅ Allocation created with ID: {allocation.id}")

            try:
                NotificationController.create_notification(
                    edhi_id=edhi_id,
                    user_id=parent.user_id,
                    notification_type='allocation_complete',
                    title='🎉 Child Allocated Successfully!',
                    message=f'Congratulations! Child "{child.name}" has been officially allocated to you.',
                    priority='high',
                    extra_data={'child_id': child_id, 'allocation_id': allocation.id}
                )
            except Exception as e:
                print(f"⚠️ Notification error: {str(e)}")

            return jsonify({
                'success': True,
                'message': f'Child "{child.name}" allocated successfully',
                'data': {
                    'allocation_id': allocation.id,
                    'child_id': child_id,
                    'child_name': child.name,
                    'parent_id': parent_id,
                    'parent_name': parent.full_name
                }
            }), 201

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)}), 500