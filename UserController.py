from flask import request, jsonify
from db import db
from models.UserModel import UserModel
from models.EdhiModel import EdhiModel
from models.PoliceModel import PoliceModel
import os
import uuid
from werkzeug.utils import secure_filename


class UserController:

    @staticmethod
    def sign_up():
        try:
            data = request.form
            image = request.files.get("image_path")

            # Check if user already exists
            existing = UserModel.query.filter(
                (UserModel.phone == data.get("phone")) |
                (UserModel.cnic == data.get("cnic"))
            ).first()
            if existing:
                return jsonify({"success": False, "message": "User already exists"}), 400

            # Handle image upload
            image_filename = ""
            if image:
                os.makedirs("uploads", exist_ok=True)
                ext = os.path.splitext(image.filename)[1]
                image_filename = secure_filename(str(uuid.uuid4()) + ext)
                image.save(os.path.join("uploads", image_filename))

            new_user = UserModel(
                name=data.get("name"),
                cnic=data.get("cnic"),
                phone=data.get("phone"),
                address=data.get("address"),
                role=data.get("role"),
                password=data.get("password"),
                image_path=image_filename
            )

            db.session.add(new_user)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "User created successfully",
                "data": {
                    "id": new_user.id,
                    "name": new_user.name,
                    "role": new_user.role,
                    "image": image_filename
                }
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def login():
        try:
            data = request.get_json()

            # Get CNIC from frontend (with dashes)
            cnic_with_dashes = data.get("cnic", "").strip()
            password = data.get("password", "").strip()

            print("=" * 50)
            print("🔍 LOGIN DEBUG")
            print("=" * 50)
            print(f"Received - CNIC: '{cnic_with_dashes}'")
            print(f"Received - Password: '{password}'")

            if not cnic_with_dashes or not password:
                return jsonify({"success": False, "message": "CNIC and password required"}), 400

            # Direct match
            user = UserModel.query.filter(
                UserModel.cnic == cnic_with_dashes,
                UserModel.password == password
            ).first()

            if not user:
                print(f"\n❌ No user found with CNIC: '{cnic_with_dashes}'")
                return jsonify({"success": False, "message": "Invalid credentials"}), 401

            print(f"\n✅ User found: {user.name}")
            print(f"   Role from database: {user.role}")
            print(f"   User ID: {user.id}")
            print("=" * 50)

            # Base response
            response_data = {
                "success": True,
                "message": "Login successful",
                "data": {
                    "id": user.id,
                    "name": user.name,
                    "role": user.role,
                    "cnic": user.cnic,
                    "phone": user.phone,
                    "image": user.image_path
                }
            }

            # ==================== CNIC to Police Station Mapping ====================
            cnic_to_station = {
                "00000-0000000-0": 1,  # Police Station Saddar Beroni
                "11111-1111111-1": 2,  # Police Station New Town
                "22222-2222222-2": 3,  # Police Station Sangjani
                "33333-3333333-3": 4,  # Police Station Kohsar
                "44444-4444444-4": 5,  # Police Station Dhok Saydan
            }

            # Police Stations Details
            police_stations = {
                1: {
                    "id": 1,
                    "pid": "PS-SAD-001",
                    "name": "Police Station Saddar Beroni",
                    "location": "Saddar Market",
                    "address": "Near Cinepax Cinema, Police Station Road, Saddar, Rawalpindi",
                    "contact": "051-1234567"
                },
                2: {
                    "id": 2,
                    "pid": "PS-NTW-002",
                    "name": "Police Station New Town",
                    "location": "Satellite Town",
                    "address": "J3Q9+55M, 4th Rd, B-Block Block B Satellite Town, Rawalpindi",
                    "contact": "051-1234568"
                },
                3: {
                    "id": 3,
                    "pid": "PS-SAN-003",
                    "name": "Police Station Sangjani",
                    "location": "Sangjani",
                    "address": "Near 26 Number Chungi, Sangjani, Rawalpindi",
                    "contact": "051-2295122"
                },
                4: {
                    "id": 4,
                    "pid": "PS-KOH-004",
                    "name": "Police Station Kohsar",
                    "location": "F-7 Markaz",
                    "address": "F-7 Markaz, Islamabad",
                    "contact": "051-9102499"
                },
                5: {
                    "id": 5,
                    "pid": "PS-DSD-005",
                    "name": "Police Station Dhok Saydan",
                    "location": "Dhok Saydan",
                    "address": "Near 6th Road, Dhok Saydan, Rawalpindi",
                    "contact": "051-1234569"
                }
            }

            # ==================== CNIC to Edhi Center Mapping ====================
            cnic_to_edhi = {
                "55555555555556": 19,  # Edhi Center Raja Bazaar
                "55555555555557": 20,  # Edhi Center Saddar
                "55555555555558": 21,  # Edhi Center Tench Bhatta
                "55555555555560": 22,  # Edhi Center Satellite Town
            }

            # ==================== HANDLE POLICE USERS ====================
            if user.role == "police":
                station_id = None

                # METHOD 1: CNIC Mapping
                if user.cnic in cnic_to_station:
                    station_id = cnic_to_station[user.cnic]
                    print(f"📌 Got station ID from CNIC mapping: {station_id}")

                # METHOD 2: Fallback to user.police_station_id
                if not station_id and user.police_station_id is not None:
                    try:
                        station_id = int(user.police_station_id)
                        print(f"📌 Got station ID from user model: {station_id}")
                    except (ValueError, TypeError):
                        print(f"⚠️ Could not convert police_station_id to int: {user.police_station_id}")

                # If we have station_id, add to response
                if station_id and station_id in police_stations:
                    station = police_stations[station_id]
                    response_data["data"]["police_station_id"] = station["id"]
                    response_data["data"]["police_station_pid"] = station["pid"]
                    response_data["data"]["police_station_name"] = station["name"]
                    response_data["data"]["police_station_location"] = station["location"]
                    response_data["data"]["police_station_address"] = station["address"]
                    response_data["data"]["police_station_contact"] = station["contact"]
                    print(f"✅ Police station assigned: {station['name']} (ID: {station_id})")
                else:
                    print(f"❌ No station mapping found for CNIC: {user.cnic}")

            # ==================== HANDLE EDHI USERS ====================
            elif user.role == "edhi" or user.role == "6":
                edhi_id = None

                # METHOD 1: CNIC Mapping
                if user.cnic in cnic_to_edhi:
                    edhi_id = cnic_to_edhi[user.cnic]
                    print(f"📌 Got Edhi center ID from CNIC mapping: {edhi_id}")

                # METHOD 2: Fetch from Edhi table
                if not edhi_id:
                    edhi_center = EdhiModel.query.filter_by(user_id=user.id).first()
                    if edhi_center:
                        edhi_id = edhi_center.id
                        print(f"📌 Got Edhi center ID from Edhi table: {edhi_id}")

                if edhi_id:
                    edhi_center = EdhiModel.query.get(edhi_id)
                    response_data["data"]["edhi_center_id"] = edhi_id
                    response_data["data"]["edhi_center_name"] = edhi_center.name if edhi_center else "Edhi Center"
                    print(f"✅ Edhi center assigned: {edhi_center.name if edhi_center else 'Unknown'} (ID: {edhi_id})")
                else:
                    print(f"❌ No Edhi center mapping found for CNIC: {user.cnic}")

            print("\n📤 FINAL RESPONSE DATA:")
            print(response_data)
            print("=" * 50)

            return jsonify(response_data), 200

        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def debug_check_user():
        try:
            from models.UserModel import UserModel

            # Role "police" wale users
            police_users = UserModel.query.filter(UserModel.role == "police").all()

            result = []
            for user in police_users:
                result.append({
                    "id": user.id,
                    "name": user.name,
                    "cnic": user.cnic,
                    "role": user.role,
                    "police_station_id": user.police_station_id
                })

            return jsonify({
                "success": True,
                "police_users": result,
                "count": len(result)
            }), 200

        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_current_user(request):
        try:
            user_id = request.args.get('user_id')
            if not user_id:
                return jsonify({"success": False, "message": "User ID required"}), 400

            user = UserModel.query.get(user_id)
            if not user:
                return jsonify({"success": False, "message": "User not found"}), 404

            # Convert role for frontend
            frontend_role = user.role
            if user.role == "6":
                frontend_role = "police"
            elif user.role == "7":
                frontend_role = "edhi"

            response_data = {
                "success": True,
                "id": user.id,
                "name": user.name,
                "cnic": user.cnic,
                "phone": user.phone,
                "address": user.address,
                "role": frontend_role,
                "original_role": user.role,
                "image": user.image_path,
                "police_station_id": user.police_station_id if hasattr(user, 'police_station_id') else None
            }

            # Add police station details if available
            if hasattr(user, 'police_station_id') and user.police_station_id:
                police_stations = {
                    1: {"pid": "PS-SAD-001", "name": "Police Station Saddar Beroni"},
                    2: {"pid": "PS-NTW-002", "name": "Police Station New Town"},
                    3: {"pid": "PS-SAN-003", "name": "Police Station Sangjani"},
                    4: {"pid": "PS-KOH-004", "name": "Police Station Kohsar"},
                    5: {"pid": "PS-DSD-005", "name": "Police Station Dhok Saydan"},
                }
                if user.police_station_id in police_stations:
                    response_data["police_station_pid"] = police_stations[user.police_station_id]["pid"]
                    response_data["police_station_name"] = police_stations[user.police_station_id]["name"]

            # ✅ Add Edhi center details if available
            edhi_center = EdhiModel.query.filter_by(user_id=user.id).first()
            if edhi_center:
                response_data["edhi_center_id"] = edhi_center.id
                response_data["edhi_center_name"] = edhi_center.name

            return jsonify(response_data), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500