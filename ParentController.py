from flask import request, jsonify
from db import db
from models.EdhiModel import EdhiModel
from models.ParentModel import ParentModel
from models.RequestModel import RequestModel
from models.UserModel import UserModel
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename

from services.LocationService import LocationService


class ParentController:

    @staticmethod
    def create_parent_profile():
        try:
            data = request.form
            files = request.files
            user_id = data.get("user_id")
            cnic_number = data.get("cnic_number")
            full_name = data.get("full_name")  # ✅ Ye line add karo

            print(f"📝 Creating/updating parent profile for user_id: {user_id}")
            print(f"📝 CNIC: {cnic_number}")
            print(f"📝 Full Name: {full_name}")

            # Handle file uploads
            def save_file(file_field):
                if file_field in files and files[file_field]:
                    file = files[file_field]
                    os.makedirs("uploads/documents", exist_ok=True)
                    ext = os.path.splitext(file.filename)[1]
                    filename = secure_filename(str(uuid.uuid4()) + ext)
                    file.save(os.path.join("uploads/documents", filename))
                    return filename
                return ""

            # Check if parent exists
            parent = ParentModel.query.filter_by(user_id=user_id).first()

            if parent:
                # Update existing parent
                print(f"🔄 Updating existing parent profile (ID: {parent.id})")

                if "cnic_file" in files and files["cnic_file"]:
                    parent.cnic_file = save_file("cnic_file")
                if "frc_file" in files and files["frc_file"]:
                    parent.frc_file_path = save_file("frc_file")
                if "police_certificate" in files and files["police_certificate"]:
                    parent.police_certificate_path = save_file("police_certificate")

                parent.cnic_number = data.get("cnic_number", parent.cnic_number)
                parent.full_name = data.get("full_name", parent.full_name)  # ✅ Update full_name
                parent.marital_status = data.get("marital_status", parent.marital_status)
                parent.husband_age = data.get("husband_age") if data.get("husband_age") else parent.husband_age
                parent.wife_age = data.get("wife_age") if data.get("wife_age") else parent.wife_age
                parent.occupation = data.get("occupation", parent.occupation)
                parent.income = data.get("income", parent.income)
                parent.boys_count = data.get("boys_count", parent.boys_count)
                parent.girls_count = data.get("girls_count", parent.girls_count)
                parent.ethnicity = data.get("ethnicity", parent.ethnicity)
                parent.address = data.get("address", parent.address)
                parent.phone_no = data.get("phone_no", parent.phone_no)
                parent.religion = data.get("religion", parent.religion)

                message = "Parent profile updated successfully"
            else:
                # Check for duplicate CNIC
                existing_cnic = ParentModel.query.filter_by(cnic_number=cnic_number).first()
                if existing_cnic:
                    return jsonify({
                        "success": False,
                        "message": f"This CNIC number is already registered to another user."
                    }), 400

                # Create new parent profile
                print(f"✨ Creating new parent profile")

                parent = ParentModel(
                    user_id=user_id,
                    cnic_file=save_file("cnic_file"),
                    cnic_number=cnic_number,
                    full_name=full_name,  # ✅ Ye line add karo
                    marital_status=data.get("marital_status"),
                    husband_age=data.get("husband_age") if data.get("husband_age") else None,
                    wife_age=data.get("wife_age") if data.get("wife_age") else None,
                    occupation=data.get("occupation"),
                    income=data.get("income"),
                    boys_count=data.get("boys_count", 0),
                    girls_count=data.get("girls_count", 0),
                    ethnicity=data.get("ethnicity"),
                    address=data.get("address"),
                    frc_file_path=save_file("frc_file"),
                    phone_no=data.get("phone_no"),
                    police_certificate_path=save_file("police_certificate"),
                    religion=data.get("religion")
                )
                db.session.add(parent)
                message = "Parent profile created successfully"

            db.session.commit()
            print(f"✅ {message} - Parent ID: {parent.id}, User ID: {parent.user_id}, Name: {parent.full_name}")

            return jsonify({
                "success": True,
                "message": message,
                "data": {
                    "parent_id": parent.id,
                    "user_id": parent.user_id,
                    "full_name": parent.full_name
                }
            }), 201

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def submit_request():
        """Submit either adoption or foster request with location data and auto-assign nearest Edhi center"""
        try:
            data = request.get_json()
            print(f"📥 Received request data: {data}")

            user_id = data.get("user_id")
            request_type = data.get("request_type")

            # Validate required fields
            if not user_id:
                return jsonify({"success": False, "message": "User ID required"}), 400

            if not request_type or request_type not in ['adoption', 'foster']:
                return jsonify({"success": False, "message": "Valid request type (adoption/foster) required"}), 400

            # Get parent profile
            parent = ParentModel.query.filter_by(user_id=user_id).first()
            if not parent:
                return jsonify({"success": False, "message": "Please complete parent profile first"}), 400

            print(f"👤 Parent found: {parent.full_name} (ID: {parent.id})")

            # Check for existing pending request of same type
            existing_request = RequestModel.query.filter_by(
                parent_id=parent.id,
                request_type=request_type,
                status="Pending"
            ).first()

            if existing_request:
                return jsonify({
                    "success": False,
                    "message": f"You already have a pending {request_type} request (ID: {existing_request.id})"
                }), 400

            # Get location from request
            parent_lat = data.get("latitude")
            parent_lng = data.get("longitude")
            parent_address = data.get("address")

            # AUTO-ASSIGN NEAREST EDHI CENTER
            assigned_edhi_id = None
            edhi_center_info = None

            if parent_lat and parent_lng:
                assigned_edhi_id = LocationService.get_nearest_edhi_center(parent_lat, parent_lng)
            elif parent_address:
                assigned_edhi_id = LocationService.get_edhi_center_from_location(parent_address)

            if not assigned_edhi_id:
                default_edhi = EdhiModel.query.first()
                if default_edhi:
                    assigned_edhi_id = default_edhi.id
                    print(f"⚠️ Using default Edhi center: {default_edhi.name}")
                else:
                    return jsonify({"success": False, "message": "No Edhi centers available"}), 400

            edhi_center = EdhiModel.query.get(assigned_edhi_id)
            if edhi_center:
                edhi_center_info = {
                    "id": edhi_center.id,
                    "name": edhi_center.name,
                    "address": edhi_center.address,
                    "contact": edhi_center.contact
                }
                print(f"✅ Assigned to Edhi center: {edhi_center.name} (ID: {edhi_center.id})")

            # Create request
            new_request = RequestModel(
                parent_id=parent.id,
                edhi_id=assigned_edhi_id,
                request_type=request_type,
                child_gender_preference=data.get("child_gender_preference"),
                child_age_preference=data.get("child_age_preference"),
                reason=data.get("reason"),
                child_ethnicity=data.get("child_ethnicity") if request_type == "adoption" else None,
                child_religion=data.get("child_religion") if request_type == "adoption" else None,
                address=parent_address,
                latitude=parent_lat,
                longitude=parent_lng,
                status="Pending",
                request_date=datetime.now()
            )

            db.session.add(new_request)
            db.session.commit()

            print(f"✅ Request created with ID: {new_request.id}")

            # ✅ CREATE NOTIFICATION FOR EDHI CENTER
            try:
                from controllers.NotificationController import NotificationController

                notification_type = 'adoption_request' if request_type == 'adoption' else 'foster_request'
                title = 'New Adoption Request' if request_type == 'adoption' else 'New Foster Request'
                message = f"New {request_type} request received from {parent.full_name}. Preferred gender: {data.get('child_gender_preference', 'Any')}"
                extra_data = {
                    'request_id': new_request.id,
                    'parent_name': parent.full_name,
                    'parent_phone': parent.phone_no,
                    'preferred_gender': data.get('child_gender_preference'),
                    'request_date': new_request.request_date.isoformat()
                }

                NotificationController.create_notification_for_edhi(
                    edhi_id=assigned_edhi_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    extra_data=extra_data
                )
            except Exception as e:
                print(f"⚠️ Failed to create notification: {str(e)}")

            return jsonify({
                "success": True,
                "message": f"{request_type.title()} request submitted successfully",
                "data": {
                    "request_id": new_request.id,
                    "request_type": new_request.request_type,
                    "status": new_request.status,
                    "assigned_edhi": edhi_center_info
                }
            }), 201

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in submit_request: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_parent_requests(user_id):
        """Get all requests for a parent"""
        try:
            parent = ParentModel.query.filter_by(user_id=user_id).first()
            if not parent:
                return jsonify({"success": False, "message": "Parent profile not found"}), 404

            requests = RequestModel.query.filter_by(parent_id=parent.id).order_by(
                RequestModel.request_date.desc()).all()

            requests_data = []
            for req in requests:
                # ✅ Get parent image from cnic_file
                parent_image = parent.cnic_file if parent.cnic_file else None

                requests_data.append({
                    "id": req.id,
                    "parent_id": parent.id,
                    "parent_name": parent.full_name,
                    "parent_cnic": parent.cnic_number,
                    "parent_image": parent_image,  # ✅ This will send the CNIC image
                    "parent_phone": parent.phone_no,
                    "request_type": req.request_type,
                    "child_gender_preference": req.child_gender_preference,
                    "reason": req.reason,
                    "child_ethnicity": req.child_ethnicity,
                    "child_religion": req.child_religion,
                    "status": req.status,
                    "request_date": req.request_date.isoformat() if req.request_date else None,
                    "edhi_id": req.edhi_id,
                    "address": req.address,
                    "latitude": float(req.latitude) if req.latitude else None,
                    "longitude": float(req.longitude) if req.longitude else None
                })

            return jsonify({
                "success": True,
                "data": requests_data,
                "count": len(requests_data)
            }), 200

        except Exception as e:
            print(f"❌ Error in get_parent_requests: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500
    @staticmethod
    def find_nearest_edhi():
        try:
            data = request.get_json()
            lat = data.get('lat')
            lng = data.get('lng')

            from services.LocationService import LocationService
            nearest_id = LocationService.get_nearest_edhi_center(lat, lng)

            if nearest_id:
                edhi = EdhiModel.query.get(nearest_id)
                return jsonify({
                    'success': True,
                    'data': {
                        'id': edhi.id,
                        'name': edhi.name,
                        'address': edhi.address,
                        'contact': edhi.contact,
                        'latitude': float(edhi.latitude),
                        'longitude': float(edhi.longitude)
                    }
                }), 200
            else:
                return jsonify({'success': False, 'message': 'No Edhi center found'}), 404
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_parent_profile(user_id):
        """Get parent profile by user_id"""
        try:
            parent = ParentModel.query.filter_by(user_id=user_id).first()
            if not parent:
                return jsonify({"success": False, "message": "Parent profile not found"}), 404

            return jsonify({
                "success": True,
                "data": {
                    "id": parent.id,
                    "full_name": parent.full_name,
                    "cnic_number": parent.cnic_number,
                    "marital_status": parent.marital_status,
                    "husband_age": parent.husband_age,
                    "wife_age": parent.wife_age,
                    "occupation": parent.occupation,
                    "income": parent.income,
                    "boys_count": parent.boys_count,
                    "girls_count": parent.girls_count,
                    "ethnicity": parent.ethnicity,
                    "address": parent.address,
                    "phone_no": parent.phone_no,
                    "religion": parent.religion,
                    "has_frc": bool(parent.frc_file_path),
                    "has_police_cert": bool(parent.police_certificate_path)
                }
            }), 200

        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def delete_parent_profile(user_id):
        """Delete parent profile (optional - for admin use)"""
        try:
            parent = ParentModel.query.filter_by(user_id=user_id).first()
            if not parent:
                return jsonify({"success": False, "message": "Parent profile not found"}), 404

            # Check if there are any pending requests
            pending_requests = RequestModel.query.filter_by(
                parent_id=parent.id,
                status="Pending"
            ).count()

            if pending_requests > 0:
                return jsonify({
                    "success": False,
                    "message": f"Cannot delete profile. You have {pending_requests} pending request(s)."
                }), 400

            # Delete the profile
            db.session.delete(parent)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Parent profile deleted successfully"
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500