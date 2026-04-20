from flask import jsonify, request
from db import db
from models.RequestModel import RequestModel
from models.ParentModel import ParentModel
from models.UserModel import UserModel
from models.EdhiModel import EdhiModel
from models.ChildImagesModel import ChildImageModel
from datetime import datetime


class RequestController:

    @staticmethod
    def get_edhi_requests(edhi_id):
        """Get all requests for an Edhi center"""
        try:
            print(f"🔍 Fetching requests for Edhi center ID: {edhi_id}")

            try:
                edhi_id = int(edhi_id)
            except:
                pass

            edhi_center = EdhiModel.query.get(edhi_id)
            if not edhi_center:
                return jsonify({"success": False, "message": "Edhi center not found"}), 404

            requests = RequestModel.query.filter_by(
                edhi_id=edhi_id
            ).order_by(RequestModel.request_date.desc()).all()

            print(f"📊 Found {len(requests)} requests for Edhi center {edhi_id}")

            output = []
            for req in requests:
                parent = ParentModel.query.get(req.parent_id)
                parent_user = UserModel.query.get(parent.user_id) if parent else None

                parent_image = None
                if parent_user and parent_user.image_path:
                    parent_image = parent_user.image_path

                request_age = None
                if req.request_date:
                    days = (datetime.now() - req.request_date).days
                    if days < 1:
                        request_age = "Today"
                    elif days == 1:
                        request_age = "Yesterday"
                    else:
                        request_age = f"{days} days ago"

                request_data = {
                    "id": req.id,
                    "parent_id": req.parent_id,
                    "parent_user_id": parent_user.id if parent_user else None,
                    "parent_user_name": parent_user.name if parent_user else None,
                    "edhi_id": req.edhi_id,
                    "request_type": req.request_type,
                    "status": req.status,
                    "request_date": req.request_date.isoformat() if req.request_date else None,
                    "request_age": request_age,
                    "child_age_preference": req.child_age_preference,
                    "child_gender_preference": req.child_gender_preference,
                    "child_ethnicity": req.child_ethnicity,
                    "child_religion": req.child_religion,
                    "reason": req.reason,
                    "address": req.address,
                    "latitude": float(req.latitude) if req.latitude else None,
                    "longitude": float(req.longitude) if req.longitude else None,
                    "remarks": req.remarks,
                    "parent": {
                        "id": parent.id if parent else None,
                        "name": parent.full_name if parent else "Unknown",
                        "cnic": parent.cnic_number if parent else None,
                        "phone": parent.phone_no if parent else None,
                        "occupation": parent.occupation if parent else None,
                        "income": parent.income if parent else None,
                        "address": parent.address if parent else None,
                        "image": parent_image
                    } if parent else None,
                    "parent_user": {
                        "id": parent_user.id if parent_user else None,
                        "name": parent_user.name if parent_user else None,
                        "phone": parent_user.phone if parent_user else None,
                        "image": parent_user.image_path if parent_user else None
                    } if parent_user else None
                }
                output.append(request_data)

            return jsonify({
                "success": True,
                "data": output,
                "count": len(output),
                "edhi_center": {
                    "id": edhi_center.id,
                    "name": edhi_center.name,
                    "address": edhi_center.address,
                    "contact": edhi_center.contact
                }
            }), 200

        except Exception as e:
            print(f"❌ Error in get_edhi_requests: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_parent_requests(user_id):
        """Get all requests for a parent"""
        try:
            print(f"🔍 Fetching requests for parent user ID: {user_id}")

            parent = ParentModel.query.filter_by(user_id=user_id).first()
            if not parent:
                return jsonify({"success": False, "message": "Parent profile not found"}), 404

            requests = RequestModel.query.filter_by(
                parent_id=parent.id
            ).order_by(RequestModel.request_date.desc()).all()

            output = []
            for req in requests:
                edhi = EdhiModel.query.get(req.edhi_id) if req.edhi_id else None

                request_data = {
                    "id": req.id,
                    "parent_id": req.parent_id,
                    "edhi_id": req.edhi_id,
                    "request_type": req.request_type,
                    "status": req.status,
                    "request_date": req.request_date.isoformat() if req.request_date else None,
                    "child_age_preference": req.child_age_preference,
                    "child_gender_preference": req.child_gender_preference,
                    "child_ethnicity": req.child_ethnicity,
                    "child_religion": req.child_religion,
                    "reason": req.reason,
                    "address": req.address,
                    "latitude": float(req.latitude) if req.latitude else None,
                    "longitude": float(req.longitude) if req.longitude else None,
                    "remarks": req.remarks,
                    "edhi_center": {
                        "id": edhi.id if edhi else None,
                        "name": edhi.name if edhi else None,
                        "address": edhi.address if edhi else None,
                        "contact": edhi.contact if edhi else None
                    } if edhi else None
                }
                output.append(request_data)

            return jsonify({
                "success": True,
                "data": output,
                "count": len(output)
            }), 200

        except Exception as e:
            print(f"❌ Error in get_parent_requests: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def update_request_status(request_id):
        """Update request status (approve/reject)"""
        try:
            data = request.get_json()
            new_status = data.get("status")
            remarks = data.get("remarks")

            print(f"📝 Updating request {request_id} to status: {new_status}")

            if not new_status:
                return jsonify({"success": False, "message": "Status required"}), 400

            if new_status not in ["Pending", "Approved", "Rejected", "Completed", "Matched"]:
                return jsonify({"success": False, "message": "Invalid status"}), 400

            req = RequestModel.query.get(request_id)
            if not req:
                return jsonify({"success": False, "message": "Request not found"}), 404

            req.status = new_status
            if remarks:
                req.remarks = remarks

            db.session.commit()

            print(f"✅ Request {request_id} status updated to {new_status}")

            return jsonify({
                "success": True,
                "message": f"Request status updated to {new_status}",
                "data": {
                    "id": req.id,
                    "parent_id": req.parent_id,
                    "edhi_id": req.edhi_id,
                    "request_type": req.request_type,
                    "status": req.status,
                    "request_date": req.request_date.isoformat() if req.request_date else None,
                    "child_age_preference": req.child_age_preference,
                    "child_gender_preference": req.child_gender_preference,
                    "child_ethnicity": req.child_ethnicity,
                    "child_religion": req.child_religion,
                    "reason": req.reason,
                    "address": req.address,
                    "latitude": float(req.latitude) if req.latitude else None,
                    "longitude": float(req.longitude) if req.longitude else None,
                    "remarks": req.remarks
                }
            }), 200

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in update_request_status: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_request_by_id(request_id):
        """Get a single request by ID with all details"""
        try:
            print(f"🔍 Fetching request ID: {request_id}")

            req = RequestModel.query.get(request_id)
            if not req:
                return jsonify({"success": False, "message": "Request not found"}), 404

            parent = ParentModel.query.get(req.parent_id)
            parent_user = UserModel.query.get(parent.user_id) if parent else None

            parent_image = None
            if parent_user and parent_user.image_path:
                parent_image = parent_user.image_path

            request_age = None
            if req.request_date:
                days = (datetime.now() - req.request_date).days
                if days < 1:
                    request_age = "Today"
                elif days == 1:
                    request_age = "Yesterday"
                else:
                    request_age = f"{days} days ago"

            request_data = {
                "id": req.id,
                "parent_id": req.parent_id,
                "edhi_id": req.edhi_id,
                "request_type": req.request_type,
                "status": req.status,
                "request_date": req.request_date.isoformat() if req.request_date else None,
                "request_age": request_age,
                "child_age_preference": req.child_age_preference,
                "child_gender_preference": req.child_gender_preference,
                "child_ethnicity": req.child_ethnicity,
                "child_religion": req.child_religion,
                "reason": req.reason,
                "address": req.address,
                "latitude": float(req.latitude) if req.latitude else None,
                "longitude": float(req.longitude) if req.longitude else None,
                "remarks": req.remarks,
                "parent": {
                    "id": parent.id if parent else None,
                    "name": parent.full_name if parent else "Unknown",
                    "cnic": parent.cnic_number if parent else None,
                    "phone": parent.phone_no if parent else None,
                    "occupation": parent.occupation if parent else None,
                    "income": parent.income if parent else None,
                    "address": parent.address if parent else None,
                    "image": parent_image
                } if parent else None,
                "parent_user": {
                    "id": parent_user.id if parent_user else None,
                    "name": parent_user.name if parent_user else None,
                    "phone": parent_user.phone if parent_user else None,
                    "image": parent_user.image_path if parent_user else None
                } if parent_user else None
            }

            return jsonify({
                "success": True,
                "data": request_data
            }), 200

        except Exception as e:
            print(f"❌ Error in get_request_by_id: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    # ==================== NEW METHODS ====================

    @staticmethod
    def create_request():
        """Create a new adoption/foster request from parent"""
        try:
            data = request.get_json()

            parent_id = data.get('parent_id')
            edhi_id = data.get('edhi_id')
            request_type = data.get('request_type')

            if not parent_id:
                return jsonify({'success': False, 'message': 'Parent ID is required'}), 400

            if not edhi_id:
                return jsonify({'success': False, 'message': 'Edhi center ID is required'}), 400

            if not request_type or request_type not in ['adoption', 'foster']:
                return jsonify({'success': False, 'message': 'Valid request type (adoption/foster) is required'}), 400

            existing_request = RequestModel.query.filter_by(
                parent_id=parent_id,
                status='Pending'
            ).first()

            if existing_request:
                return jsonify({
                    'success': False,
                    'message': 'You already have a pending request. Please wait for it to be processed.'
                }), 400

            new_request = RequestModel(
                parent_id=parent_id,
                edhi_id=edhi_id,
                request_type=request_type,
                status='Pending',
                request_date=datetime.utcnow(),
                child_age_preference=data.get('child_age_preference'),
                child_gender_preference=data.get('child_gender_preference'),
                child_ethnicity=data.get('child_ethnicity'),
                child_religion=data.get('child_religion'),
                reason=data.get('reason'),
                address=data.get('address'),
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                remarks=data.get('remarks')
            )

            db.session.add(new_request)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Request submitted successfully',
                'data': new_request.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in create_request: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_request_by_parent(parent_id):
        """Get all requests for a specific parent by parent_id"""
        try:
            print(f"🔍 Fetching requests for parent ID: {parent_id}")

            requests = RequestModel.query.filter_by(
                parent_id=parent_id
            ).order_by(RequestModel.request_date.desc()).all()

            output = []
            for req in requests:
                edhi = EdhiModel.query.get(req.edhi_id) if req.edhi_id else None

                request_data = {
                    "id": req.id,
                    "parent_id": req.parent_id,
                    "edhi_id": req.edhi_id,
                    "request_type": req.request_type,
                    "status": req.status,
                    "request_date": req.request_date.isoformat() if req.request_date else None,
                    "child_age_preference": req.child_age_preference,
                    "child_gender_preference": req.child_gender_preference,
                    "child_ethnicity": req.child_ethnicity,
                    "child_religion": req.child_religion,
                    "reason": req.reason,
                    "address": req.address,
                    "latitude": float(req.latitude) if req.latitude else None,
                    "longitude": float(req.longitude) if req.longitude else None,
                    "remarks": req.remarks,
                    "edhi_center": {
                        "id": edhi.id if edhi else None,
                        "name": edhi.name if edhi else None,
                        "address": edhi.address if edhi else None,
                        "contact": edhi.contact if edhi else None
                    } if edhi else None
                }
                output.append(request_data)

            return jsonify({
                "success": True,
                "data": output,
                "count": len(output)
            }), 200

        except Exception as e:
            print(f"❌ Error in get_request_by_parent: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_matched_requests(edhi_id):
        """Get all matched requests for an Edhi center"""
        try:
            print(f"🔍 Fetching matched requests for Edhi center ID: {edhi_id}")

            try:
                edhi_id = int(edhi_id)
            except:
                pass

            requests = RequestModel.query.filter_by(
                edhi_id=edhi_id,
                status='Matched'
            ).order_by(RequestModel.request_date.desc()).all()

            output = []
            for req in requests:
                parent = ParentModel.query.get(req.parent_id)
                parent_user = UserModel.query.get(parent.user_id) if parent else None

                request_data = {
                    "id": req.id,
                    "parent_id": req.parent_id,
                    "edhi_id": req.edhi_id,
                    "request_type": req.request_type,
                    "status": req.status,
                    "request_date": req.request_date.isoformat() if req.request_date else None,
                    "child_age_preference": req.child_age_preference,
                    "child_gender_preference": req.child_gender_preference,
                    "child_ethnicity": req.child_ethnicity,
                    "child_religion": req.child_religion,
                    "reason": req.reason,
                    "address": req.address,
                    "remarks": req.remarks,
                    "parent": {
                        "id": parent.id if parent else None,
                        "name": parent.full_name if parent else "Unknown",
                        "cnic": parent.cnic_number if parent else None,
                        "phone": parent.phone_no if parent else None,
                        "address": parent.address if parent else None
                    } if parent else None
                }
                output.append(request_data)

            return jsonify({
                "success": True,
                "data": output,
                "count": len(output)
            }), 200

        except Exception as e:
            print(f"❌ Error in get_matched_requests: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def delete_request(request_id):
        """Delete a request (only if status is Pending)"""
        try:
            req = RequestModel.query.get(request_id)

            if not req:
                return jsonify({"success": False, "message": "Request not found"}), 404

            if req.status != "Pending":
                return jsonify({
                    "success": False,
                    "message": "Only pending requests can be deleted"
                }), 400

            db.session.delete(req)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Request deleted successfully"
            }), 200

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in delete_request: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500