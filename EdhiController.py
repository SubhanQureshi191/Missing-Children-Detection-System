from flask import jsonify, request
from models.EdhiModel import EdhiModel
from models.UserModel import UserModel
from db import db


class EdhiController:

    @staticmethod
    def create_edhi_center():
        """Create a new Edhi center"""
        try:
            data = request.get_json()

            # Validate required fields
            if not data.get("name"):
                return jsonify({"success": False, "message": "Name is required"}), 400

            if not data.get("user_id"):
                return jsonify({"success": False, "message": "User ID is required"}), 400

            # Check if user exists and is Edhi
            user = UserModel.query.get(data.get("user_id"))
            if not user:
                return jsonify({"success": False, "message": "User not found"}), 404

            # ✅ FIX: Check for both "6" and "edhi"
            if user.role not in ["6", "edhi"]:
                return jsonify({"success": False, "message": "User is not an Edhi center"}), 400

            # Check if Edhi center already exists for this user
            existing = EdhiModel.query.filter_by(user_id=data.get("user_id")).first()
            if existing:
                return jsonify({"success": False, "message": "Edhi center already exists for this user"}), 400

            # Create new Edhi center
            edhi = EdhiModel(
                user_id=data.get("user_id"),
                name=data.get("name"),
                contact=data.get("contact"),
                address=data.get("address"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude")
            )

            db.session.add(edhi)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Edhi center created successfully",
                "data": edhi.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_edhi_center(user_id):
        """Get Edhi center info by user_id"""
        try:
            print(f"🔍 Fetching Edhi center for user_id: {user_id}")

            # Convert to int
            try:
                user_id = int(user_id)
            except:
                pass

            # First find user
            user = UserModel.query.get(user_id)
            if not user:
                print(f"❌ User {user_id} not found")
                return jsonify({"success": False, "message": "User not found"}), 404

            # ✅ FIX: Check for both "6" and "edhi"
            if user.role not in ["6", "edhi"]:
                print(f"❌ User {user_id} role is {user.role}, not edhi")
                return jsonify({"success": False, "message": "This user is not an Edhi center"}), 400

            # Find Edhi center by user_id
            edhi = EdhiModel.query.filter_by(user_id=user_id).first()

            # If not found by user_id, try by name
            if not edhi:
                edhi = EdhiModel.query.filter_by(name=user.name).first()

            if not edhi:
                print(f"❌ No Edhi center found for user {user_id}")
                return jsonify({"success": False, "message": "Edhi center not found"}), 404

            print(f"✅ Edhi center found: {edhi.name} (ID: {edhi.id})")

            return jsonify({
                "success": True,
                "data": edhi.to_dict()
            }), 200

        except Exception as e:
            print(f"❌ Error in get_edhi_center: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_edhi_by_id(edhi_id):
        """Get Edhi center by ID"""
        try:
            edhi = EdhiModel.query.get(edhi_id)

            if not edhi:
                return jsonify({"success": False, "message": "Edhi center not found"}), 404

            return jsonify({
                "success": True,
                "data": edhi.to_dict()
            }), 200

        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_all_edhi_centers():
        """Get all Edhi centers"""
        try:
            edhi_centers = EdhiModel.query.all()

            result = [edhi.to_dict() for edhi in edhi_centers]

            return jsonify({
                "success": True,
                "data": result,
                "count": len(result)
            }), 200

        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def update_edhi_center(edhi_id):
        """Update Edhi center information"""
        try:
            edhi = EdhiModel.query.get(edhi_id)
            if not edhi:
                return jsonify({"success": False, "message": "Edhi center not found"}), 404

            data = request.get_json()

            # Update fields if provided
            if data.get("name"):
                edhi.name = data.get("name")
            if data.get("contact"):
                edhi.contact = data.get("contact")
            if data.get("address"):
                edhi.address = data.get("address")
            if data.get("latitude"):
                edhi.latitude = data.get("latitude")
            if data.get("longitude"):
                edhi.longitude = data.get("longitude")

            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Edhi center updated successfully",
                "data": edhi.to_dict()
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def delete_edhi_center(edhi_id):
        """Delete Edhi center"""
        try:
            edhi = EdhiModel.query.get(edhi_id)
            if not edhi:
                return jsonify({"success": False, "message": "Edhi center not found"}), 404

            db.session.delete(edhi)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Edhi center deleted successfully"
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500