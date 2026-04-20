from flask import request, jsonify
from db import db
from models.ChildModel import ChildModel
from models.ChildImagesModel import ChildImageModel
import os
import uuid
from werkzeug.utils import secure_filename
from models.EdhiModel import EdhiModel


class ChildController:

    @staticmethod
    def create_child():
        try:
            # ✅ Accept BOTH JSON and FormData
            if request.is_json:
                data = request.get_json()
                print("📥 Received JSON data:", data)
                files = None
            else:
                data = request.form.to_dict()
                files = request.files
                print("📥 Received Form data:", data)

            print("=" * 60)
            print("📥 CHILD DATA RECEIVED:")
            print("=" * 60)
            for key, value in data.items():
                print(f"   {key}: {value}")

            # -------------------
            # 1️⃣ Handle main child image
            # -------------------
            image_filename = None

            # Check if image in files (FormData) or in data (JSON)
            if files and 'photo' in files:
                image = files.get('photo')
                if image:
                    os.makedirs("uploads/children", exist_ok=True)
                    ext = os.path.splitext(image.filename)[1]
                    image_filename = secure_filename(str(uuid.uuid4()) + ext)
                    image.save(os.path.join("uploads/children", image_filename))
                    print(f"✅ Main image saved: {image_filename}")
            elif data.get('image_path'):
                image_filename = data.get('image_path')
                print(f"✅ Using existing image path: {image_filename}")

            # -------------------
            # 2️⃣ Handle coordinates
            # -------------------
            last_seen_latitude = None
            last_seen_longitude = None

            # Try multiple possible field names
            lat_raw = data.get("last_seen_latitude") or data.get("last_seen_lat") or data.get("latitude")
            lng_raw = data.get("last_seen_longitude") or data.get("last_seen_lng") or data.get("longitude")

            print(f"\n📍 RAW COORDINATES: lat={lat_raw}, lng={lng_raw}")

            if lat_raw and str(lat_raw).strip() and str(lat_raw).lower() not in ['null', 'none', '']:
                try:
                    last_seen_latitude = float(lat_raw)
                    print(f"✅ Latitude converted: {last_seen_latitude}")
                except (ValueError, TypeError) as e:
                    print(f"❌ Latitude conversion failed: {e}")

            if lng_raw and str(lng_raw).strip() and str(lng_raw).lower() not in ['null', 'none', '']:
                try:
                    last_seen_longitude = float(lng_raw)
                    print(f"✅ Longitude converted: {last_seen_longitude}")
                except (ValueError, TypeError) as e:
                    print(f"❌ Longitude conversion failed: {e}")

            # -------------------
            # 3️⃣ Create child record
            # -------------------
            new_child = ChildModel(
                name=data.get('name'),
                age=int(data.get('age')) if data.get('age') else None,
                gender=data.get('gender'),
                identification_mark=data.get('identification_mark'),
                religion=data.get('religion'),
                address=data.get('address'),
                clothes=data.get('clothes'),
                disability=data.get('disability'),
                image_path=image_filename,
                last_seen_location=data.get('last_seen_location'),
                last_seen_latitude=last_seen_latitude,
                last_seen_longitude=last_seen_longitude
            )

            print("\n📦 CHILD OBJECT TO BE SAVED:")
            print(f"   name: {new_child.name}")
            print(f"   age: {new_child.age}")
            print(f"   gender: {new_child.gender}")
            print(f"   address: {new_child.address}")
            print(f"   last_seen_location: {new_child.last_seen_location}")
            print(f"   last_seen_latitude: {new_child.last_seen_latitude}")
            print(f"   last_seen_longitude: {new_child.last_seen_longitude}")

            db.session.add(new_child)
            db.session.flush()
            print(f"✅ Child created with ID: {new_child.id}")

            # -------------------
            # 4️⃣ Handle additional images
            # -------------------
            images_list = data.get('images', [])
            if isinstance(images_list, str):
                # If images is a string, try to parse as JSON
                import json
                try:
                    images_list = json.loads(images_list)
                except:
                    images_list = [images_list] if images_list else []

            print(f"\n📸 Additional images received: {len(images_list)}")

            for img_path in images_list:
                if img_path and str(img_path).strip():
                    child_image = ChildImageModel(
                        child_id=new_child.id,
                        image_path=str(img_path)
                    )
                    db.session.add(child_image)
                    print(f"   ✅ Added image: {img_path}")

            db.session.commit()
            print(f"\n✅ ALL DATA COMMITTED FOR CHILD ID: {new_child.id}")

            # -------------------
            # 5️⃣ Return response with ID
            # -------------------
            return jsonify({
                "success": True,
                "message": "Child saved successfully",
                "id": new_child.id,  # ✅ Direct ID for frontend
                "child_id": new_child.id,  # ✅ Alternative field
                "data": {
                    "id": new_child.id,
                    "child_id": new_child.id,
                    "name": new_child.name,
                    "age": new_child.age,
                    "gender": new_child.gender,
                    "address": new_child.address,
                    "last_seen_latitude": new_child.last_seen_latitude,
                    "last_seen_longitude": new_child.last_seen_longitude,
                    "last_seen_location": new_child.last_seen_location
                }
            }), 201

        except Exception as e:
            db.session.rollback()
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_child_images(child_id):
        """Get all images for a specific child"""
        try:
            print(f"🔍 Fetching images for child ID: {child_id}")

            child = ChildModel.query.get(child_id)
            if not child:
                return jsonify({"success": False, "message": "Child not found"}), 404

            images = ChildImageModel.query.filter_by(child_id=child_id).all()

            image_list = []
            for img in images:
                if img.image_path:
                    if img.image_path.startswith('/'):
                        image_list.append(img.image_path)
                    elif img.image_path.startswith('uploads/'):
                        image_list.append(f"/{img.image_path}")
                    else:
                        image_list.append(f"/uploads/{img.image_path}")

            if not image_list and child.image_path:
                if child.image_path.startswith('/'):
                    image_list.append(child.image_path)
                elif child.image_path.startswith('uploads/'):
                    image_list.append(f"/{child.image_path}")
                else:
                    image_list.append(f"/uploads/{child.image_path}")

            print(f"📸 Found {len(image_list)} images for child {child_id}")

            return jsonify({
                "success": True,
                "child_id": child_id,
                "images": image_list,
                "count": len(image_list)
            }), 200

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_child_by_id(child_id):
        """Get single child by ID"""
        try:
            child = ChildModel.query.get(child_id)

            if not child:
                return jsonify({"success": False, "message": "Child not found"}), 404

            child_data = {
                "id": child.id,
                "name": child.name,
                "age": child.age,
                "gender": child.gender,
                "address": child.address,
                "identification_mark": child.identification_mark,
                "clothes": child.clothes,
                "disability": child.disability,
                "religion": child.religion,
                "last_seen_location": child.last_seen_location,
                "last_seen_latitude": child.last_seen_latitude,
                "last_seen_longitude": child.last_seen_longitude,
                "image_path": child.image_path
            }

            return jsonify({"success": True, "data": child_data}), 200

        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_available_children():
        """Get available children based on preference filters"""
        try:
            gender = request.args.get('gender')
            age = request.args.get('age')
            religion = request.args.get('religion')

            query = ChildModel.query

            if gender and gender.lower() != 'any':
                query = query.filter(ChildModel.gender == gender)

            if religion and religion.lower() != 'any':
                query = query.filter(ChildModel.religion == religion)

            if age:
                try:
                    age_int = int(age)
                    if age_int > 0:
                        min_age = max(0, age_int - 2)
                        max_age = age_int + 2
                        query = query.filter(ChildModel.age.between(min_age, max_age))
                except (ValueError, TypeError):
                    pass

            children = query.all()

            children_data = []
            for child in children:
                images = []
                if child.image_path:
                    images.append(f"/uploads/children/{child.image_path}" if not child.image_path.startswith(
                        '/') else child.image_path)

                children_data.append({
                    "id": child.id,
                    "name": child.name,
                    "age": child.age,
                    "gender": child.gender,
                    "religion": child.religion,
                    "address": child.address,
                    "identification_mark": child.identification_mark,
                    "image_path": child.image_path,
                    "images": images
                })

            return jsonify({
                "success": True,
                "data": children_data,
                "count": len(children_data)
            }), 200

        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500