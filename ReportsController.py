from flask import request, jsonify
from models.ReportsModel import ReportsModel
from models.ChildModel import ChildModel
from db import db
from models.UserModel import UserModel
from services.LocationService import LocationService
from sqlalchemy import desc
from datetime import datetime


class ReportsController:

    @staticmethod
    def create_report():
        try:
            data = request.get_json() if request.is_json else request.form.to_dict()
            print("=" * 60)
            print("📥 REPORT DATA RECEIVED")
            print("=" * 60)
            print(data)

            police_station_id = None

            # 🔍 STEP 1: Coordinates-based assignment (MAIN METHOD)
            report_type = data.get("report_type")

            if report_type == "missing":
                # Missing report: last seen location se assign
                lat = data.get("last_seen_latitude")
                lng = data.get("last_seen_longitude")

                if lat and lng and str(lat).strip() and str(lng).strip():
                    try:
                        lat = float(lat)
                        lng = float(lng)
                        print(f"\n📍 Missing report - Processing coordinates: {lat}, {lng}")
                        police_station_id = LocationService.get_police_station_from_coordinates(lat, lng)
                    except (ValueError, TypeError) as e:
                        print(f"❌ Invalid coordinates: {e}")

            elif report_type == "found":
                # Found report: found location se assign
                lat = data.get("found_location_lat")
                lng = data.get("found_location_lng")

                if lat and lng and str(lat).strip() and str(lng).strip():
                    try:
                        lat = float(lat)
                        lng = float(lng)
                        print(f"\n📍 Found report - Processing coordinates: {lat}, {lng}")
                        police_station_id = LocationService.get_police_station_from_coordinates(lat, lng)
                    except (ValueError, TypeError) as e:
                        print(f"❌ Invalid coordinates: {e}")

            # 🔍 STEP 2: Fallback to text-based assignment
            if not police_station_id:
                print("\n⚠️ No coordinates or no match, trying text-based assignment...")
                for loc_field in ['last_seen_location', 'current_location', 'found_location']:
                    if data.get(loc_field):
                        police_station_id = LocationService.get_police_station_from_location(data[loc_field])
                        if police_station_id:
                            break

            last_seen_lat = float(data.get("last_seen_latitude")) if data.get("last_seen_latitude") else None
            last_seen_lng = float(data.get("last_seen_longitude")) if data.get("last_seen_longitude") else None

            # Create new report with coordinates
            new_report = ReportsModel(
                user_id=data.get("user_id"),
                child_id=data.get("child_id"),
                status=data.get("status"),
                date=data.get("date"),
                report_type=data.get("report_type"),
                last_seen_location=data.get("last_seen_location"),
                last_seen_latitude=float(data.get("last_seen_latitude")) if data.get("last_seen_latitude") else None,
                last_seen_longitude=float(data.get("last_seen_longitude")) if data.get("last_seen_longitude") else None,

                found_location=data.get("found_location"),
                found_location_lat=float(data.get("found_location_lat")) if data.get("found_location_lat") and str(
                    data.get("found_location_lat")).strip() else None,
                found_location_lng=float(data.get("found_location_lng")) if data.get("found_location_lng") and str(
                    data.get("found_location_lng")).strip() else None,
                current_location=data.get("current_location"),
                assigned_police_station_id=police_station_id,
                assignment_status='assigned' if police_station_id else 'pending'
            )

            db.session.add(new_report)
            db.session.commit()

            print(f"\n✅ Report created - ID: {new_report.id}, Police Station: {police_station_id}")

            # ============= 🔥 AUTO-TRIGGER FACE MATCHING =============
            try:
                from services.FaceMatchService import FaceMatchService
                print("\n🔥 Auto-triggering face matching...")
                matches = FaceMatchService.find_matches_for_report(new_report.id)
                print(f"✅ Face matching complete. Found {len(matches)} matches")

                if matches:
                    print("📊 Match details:")
                    for match in matches:
                        print(f"   - Report ID: {match.get('matched_with_report_id')}, "
                              f"Confidence: {match.get('match_score')}%, "
                              f"Child: {match.get('matched_child_name')}")
            except Exception as e:
                print(f"⚠️ Face matching error: {str(e)}")
                import traceback
                traceback.print_exc()
            # =========================================================

            return jsonify({
                "success": True,
                "message": "Report created successfully",
                "data": {
                    "report_id": new_report.id,
                    "assigned_police_station": police_station_id
                }
            }), 201

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_user_reports(user_id):
        """Get all reports submitted by a specific user (LATEST FIRST - BY ID)"""
        try:
            print(f"🔍 Fetching reports for user ID: {user_id}")

            # ✅ Sort by ID in DESCENDING order (latest first)
            reports = ReportsModel.query.filter_by(
                user_id=user_id
            ).order_by(
                desc(ReportsModel.id)
            ).all()

            print(f"📊 Found {len(reports)} reports for user {user_id}")
            print(f"📊 Report IDs (latest first): {[r.id for r in reports]}")

            output = []
            for report in reports:
                # Get child details
                child = ChildModel.query.get(report.child_id)

                # Get all images for this child
                child_images = []
                if child:
                    # Add main image first
                    if child.image_path:
                        child_images.append({
                            "id": 0,
                            "path": child.image_path,
                            "is_main": True
                        })

                    # Add additional images from ChildImageModel
                    from models.ChildImagesModel import ChildImageModel
                    additional_images = ChildImageModel.query.filter_by(child_id=child.id).all()
                    for img in additional_images:
                        child_images.append({
                            "id": img.id,
                            "path": img.image_path,
                            "is_main": False
                        })

                # Get police station name if assigned
                police_station_name = None
                if report.assigned_police_station_id:
                    from models.PoliceModel import PoliceModel
                    station = PoliceModel.query.get(report.assigned_police_station_id)
                    if station:
                        police_station_name = station.pname

                report_data = {
                    "id": report.id,
                    "report_id": f"REP-{report.id:04d}",
                    "child_id": report.child_id,
                    "child_name": child.name if child else "Unknown",
                    "child_age": child.age if child else None,
                    "child_gender": child.gender if child else None,
                    "child_image": child.image_path if child else None,
                    "child_images": child_images,
                    "status": report.status or "pending",
                    "assignment_status": report.assignment_status or "pending",
                    "report_type": report.report_type,
                    "date": report.date,
                    "last_seen_location": report.last_seen_location,
                    "current_location": report.current_location,
                    "found_location": report.found_location,
                    "assigned_police_station_id": report.assigned_police_station_id,
                    "assigned_police_station_name": police_station_name,
                    "created_at": report.date
                }
                output.append(report_data)

            return jsonify({
                "success": True,
                "data": output,
                "count": len(output),
                "user_id": user_id
            }), 200

        except Exception as e:
            print(f"❌ Error in get_user_reports: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_finder_reports(user_id):
        """Get all found reports submitted by a specific finder (LATEST FIRST)"""
        try:
            print(f"🔍 Fetching found reports for finder ID: {user_id}")

            # ✅ Sort by ID in DESCENDING order (latest first)
            reports = ReportsModel.query.filter_by(
                user_id=user_id,
                report_type='found'
            ).order_by(
                desc(ReportsModel.id)
            ).all()

            print(f"📊 Found {len(reports)} found reports for finder {user_id}")
            print(f"📊 Report IDs (latest first): {[r.id for r in reports]}")

            output = []
            for report in reports:
                # Get child details
                child = ChildModel.query.get(report.child_id)

                # Get ALL images for this child
                child_images = []
                if child:
                    # Add main image if exists
                    if child.image_path and child.image_path.strip():
                        child_images.append({
                            "id": 0,
                            "path": child.image_path,
                            "is_main": True
                        })

                    # Add additional images from ChildImageModel
                    try:
                        from models.ChildImagesModel import ChildImageModel
                        additional_images = ChildImageModel.query.filter_by(child_id=child.id).all()
                        for img in additional_images:
                            if img.image_path != child.image_path:
                                child_images.append({
                                    "id": img.id,
                                    "path": img.image_path,
                                    "is_main": False
                                })
                    except Exception as e:
                        print(f"⚠️ Error fetching additional images: {str(e)}")

                # Get police station name if assigned
                police_station_name = None
                if report.assigned_police_station_id:
                    from models.PoliceModel import PoliceModel
                    station = PoliceModel.query.get(report.assigned_police_station_id)
                    if station:
                        police_station_name = station.pname

                report_data = {
                    "id": report.id,
                    "report_id": f"FND-{report.id:04d}",
                    "child_id": report.child_id,
                    "child_name": child.name if child else "Unknown",
                    "child_age": child.age if child else None,
                    "child_gender": child.gender if child else None,
                    "child_image": child.image_path if child else None,
                    "child_images": child_images,
                    "status": report.status or "pending",
                    "assignment_status": report.assignment_status or "pending",
                    "report_type": report.report_type,
                    "date": report.date,
                    "last_seen_location": report.last_seen_location,
                    "current_location": report.current_location,
                    "found_location": report.found_location,
                    "assigned_police_station_id": report.assigned_police_station_id,
                    "assigned_police_station_name": police_station_name,
                    "created_at": report.date
                }
                output.append(report_data)

            return jsonify({
                "success": True,
                "data": output,
                "count": len(output),
                "user_id": user_id
            }), 200

        except Exception as e:
            print(f"❌ Error in get_finder_reports: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_report_by_id(report_id):
        """Get single report by ID with full details including face matches from MatchAlertModel"""
        try:
            print(f"🔍 Fetching report ID: {report_id}")

            report = ReportsModel.query.get(report_id)

            if not report:
                return jsonify({
                    "success": False,
                    "message": "Report not found"
                }), 404

            # Get child details
            child = ChildModel.query.get(report.child_id)

            # Get reporter details
            from models.UserModel import UserModel
            reporter = UserModel.query.get(report.user_id)

            # Get police station
            police_station_name = None
            if report.assigned_police_station_id:
                from models.PoliceModel import PoliceModel
                station = PoliceModel.query.get(report.assigned_police_station_id)
                if station:
                    police_station_name = station.pname

            # ============= GET FACE MATCHES FROM MatchAlertModel =============
            from models.MatchAlertModel import MatchAlertModel
            from sqlalchemy import desc

            face_matches = []

            print(f"📋 Current report type: {report.report_type}")

            if report.report_type == 'missing':
                # Missing report: Find matches with FOUND reports
                matches = MatchAlertModel.query.filter_by(
                    missing_report_id=report_id,
                    match_status='pending'
                ).order_by(desc(MatchAlertModel.match_score)).all()

                print(f"📊 Found {len(matches)} FOUND reports matching this MISSING report")

                for match in matches:
                    # Get the FOUND report
                    found_report = ReportsModel.query.get(match.found_report_id)

                    if not found_report:
                        continue

                    # Get matched child
                    matched_child = ChildModel.query.get(found_report.child_id)

                    # Get police station for found report
                    found_station_name = None
                    if found_report.assigned_police_station_id:
                        station = PoliceModel.query.get(found_report.assigned_police_station_id)
                        if station:
                            found_station_name = station.pname

                    # Get child image
                    child_image = None
                    if matched_child and matched_child.image_path:
                        child_image = matched_child.image_path

                    print(
                        f"   ✅ Match with FOUND report ID: {found_report.id}, Child: {matched_child.name if matched_child else 'Unknown'}")

                    face_matches.append({
                        "match_id": match.id,
                        "match_score": match.match_score,
                        "match_status": match.match_status,
                        "created_at": match.created_at.isoformat() if match.created_at else None,
                        "matched_report_id": found_report.id,
                        "matched_report_type": "found",
                        "matched_report_date": found_report.date,
                        "matched_report_location": found_report.found_location or found_report.last_seen_location,
                        "matched_report_police_station": found_station_name,
                        "matched_child": {
                            "id": matched_child.id if matched_child else None,
                            "name": matched_child.name if matched_child else "Unknown",
                            "age": matched_child.age if matched_child else None,
                            "gender": matched_child.gender if matched_child else None,
                            "image": child_image
                        }
                    })
            else:
                # Found report: Find matches with MISSING reports
                matches = MatchAlertModel.query.filter_by(
                    found_report_id=report_id,
                    match_status='pending'
                ).order_by(desc(MatchAlertModel.match_score)).all()

                print(f"📊 Found {len(matches)} MISSING reports matching this FOUND report")

                for match in matches:
                    # Get the MISSING report
                    missing_report = ReportsModel.query.get(match.missing_report_id)

                    if not missing_report:
                        continue

                    # Get matched child
                    matched_child = ChildModel.query.get(missing_report.child_id)

                    # Get police station for missing report
                    missing_station_name = None
                    if missing_report.assigned_police_station_id:
                        station = PoliceModel.query.get(missing_report.assigned_police_station_id)
                        if station:
                            missing_station_name = station.pname

                    # Get child image
                    child_image = None
                    if matched_child and matched_child.image_path:
                        child_image = matched_child.image_path

                    print(
                        f"   ✅ Match with MISSING report ID: {missing_report.id}, Child: {matched_child.name if matched_child else 'Unknown'}")

                    face_matches.append({
                        "match_id": match.id,
                        "match_score": match.match_score,
                        "match_status": match.match_status,
                        "created_at": match.created_at.isoformat() if match.created_at else None,
                        "matched_report_id": missing_report.id,
                        "matched_report_type": "missing",
                        "matched_report_date": missing_report.date,
                        "matched_report_location": missing_report.last_seen_location or missing_report.found_location,
                        "matched_report_police_station": missing_station_name,
                        "matched_child": {
                            "id": matched_child.id if matched_child else None,
                            "name": matched_child.name if matched_child else "Unknown",
                            "age": matched_child.age if matched_child else None,
                            "gender": matched_child.gender if matched_child else None,
                            "image": child_image
                        }
                    })

            report_data = {
                "id": report.id,
                "user_id": report.user_id,
                "child_id": report.child_id,
                "status": report.status,
                "date": report.date,
                "report_type": report.report_type,
                "last_seen_location": report.last_seen_location,
                "last_seen_latitude": report.last_seen_latitude,
                "last_seen_longitude": report.last_seen_longitude,
                "found_location": report.found_location,
                "found_location_lat": report.found_location_lat,
                "found_location_lng": report.found_location_lng,
                "current_location": report.current_location,
                "assigned_police_station_id": report.assigned_police_station_id,
                "assigned_police_station_name": police_station_name,
                "assignment_status": report.assignment_status,
                "face_matches": face_matches,
                "child": {
                    "id": child.id if child else None,
                    "name": child.name if child else "Unknown",
                    "age": child.age if child else None,
                    "gender": child.gender if child else None,
                    "address": child.address if child else None,
                    "identification_mark": child.identification_mark if child else None,
                    "clothes": child.clothes if child else None,
                    "disability": child.disability if child else None,
                    "religion": child.religion if child else None,
                    "last_seen_location": child.last_seen_location if child else None,
                    "last_seen_latitude": child.last_seen_latitude if child else None,
                    "last_seen_longitude": child.last_seen_longitude if child else None,
                } if child else None,
                "reporter": {
                    "id": reporter.id if reporter else None,
                    "name": reporter.name if reporter else "Unknown",
                    "phone": reporter.phone if reporter else None,
                    "cnic": reporter.cnic if reporter else None
                } if reporter else None
            }

            print(f"✅ Returning report with {len(face_matches)} face matches")

            return jsonify({
                "success": True,
                "data": report_data
            }), 200

        except Exception as e:
            print(f"❌ Error in get_report_by_id: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    # ✅ NEW: Get found reports for police station
    @staticmethod
    def get_found_reports_for_station(station_id):
        try:
            # Get found reports for this police station
            reports = ReportsModel.query.filter_by(
                assigned_police_station_id=station_id,
                report_type='found'
            ).all()

            result = []
            for report in reports:
                child = ChildModel.query.get(report.child_id)
                result.append({
                    'id': report.id,
                    'child_id': report.child_id,
                    'child_name': child.name if child else None,
                    'child_age': child.age if child else None,
                    'child_gender': child.gender if child else None,
                    'child_image': child.image_path if child else None,
                    'location': report.current_location or report.found_location,
                    'date': report.date.strftime('%Y-%m-%d') if report.date else None,
                    'status': report.status
                })

            return jsonify({'success': True, 'data': result})
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    # ✅ NEW: Admit child to Edhi center (called from police)
    # ✅ FIXED: Admit child to Edhi center - Using correct field names
    @staticmethod
    def admit_child_to_edhi():
        try:
            data = request.get_json()
            print("=" * 60)
            print("🏥 ADMIT CHILD TO EDHI CENTER")
            print("=" * 60)
            print(data)

            edhi_id = data.get('edhi_center_id')
            child_id = data.get('child_id')
            report_id = data.get('source_report_id')
            police_station_id = data.get('police_station_id')
            child_name = data.get('child_name')
            child_age = data.get('child_age')
            child_gender = data.get('child_gender')
            child_image = data.get('child_image')
            found_location = data.get('found_location')
            reporter_name = data.get('reporter_name')
            reporter_phone = data.get('reporter_phone')
            transferred_by_user_id = data.get('user_id') or data.get('transferred_by_user_id')

            # Validate required fields
            if not edhi_id:
                return jsonify({'success': False, 'message': 'Edhi center ID is required'}), 400
            if not child_id:
                return jsonify({'success': False, 'message': 'Child ID is required'}), 400
            if not report_id:
                return jsonify({'success': False, 'message': 'Report ID is required'}), 400
            if not police_station_id:
                return jsonify({'success': False, 'message': 'Police station ID is required'}), 400

            # Check if user exists
            if transferred_by_user_id:
                user_exists = UserModel.query.get(transferred_by_user_id)
                if not user_exists:
                    print(f"⚠️ User {transferred_by_user_id} not found, setting to NULL")
                    transferred_by_user_id = None

            # Get the Edhi center name
            from models.EdhiModel import EdhiModel
            edhi_center = EdhiModel.query.get(edhi_id)
            edhi_center_name = edhi_center.name if edhi_center else "Edhi Center"

            # Create admitted child record
            from models.ChildAdmissionModel import ChildAdmissionModel

            admitted_child = ChildAdmissionModel(
                child_id=child_id,
                report_id=report_id,
                police_station_id=police_station_id,
                edhi_id=edhi_id,
                admission_date=datetime.utcnow(),
                admission_remarks=f"Child found at: {found_location}. Reported by: {reporter_name}, Phone: {reporter_phone}",
                status='admitted',
                transferred_by_user_id=transferred_by_user_id
            )

            db.session.add(admitted_child)

            # Update the report status
            if report_id:
                report = ReportsModel.query.get(report_id)
                if report:
                    report.status = 'admitted_to_edhi'

            db.session.commit()

            print(f"✅ Child admitted to {edhi_center_name} (Admission ID: {admitted_child.id})")

            # ✅ CREATE NOTIFICATION FOR EDHI CENTER
            try:
                from controllers.NotificationController import NotificationController

                notification_type = 'child_admitted'
                title = 'New Child Admitted'
                message = f"Child {child_name} has been admitted to your center from police station."
                extra_data = {
                    'admission_id': admitted_child.id,
                    'child_id': child_id,
                    'child_name': child_name,
                    'child_age': child_age,
                    'child_gender': child_gender,
                    'found_location': found_location,
                    'police_station_id': police_station_id
                }

                NotificationController.create_notification_for_edhi(
                    edhi_id=edhi_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    extra_data=extra_data
                )
            except Exception as e:
                print(f"⚠️ Failed to create notification: {str(e)}")

            return jsonify({
                'success': True,
                'message': f'Child admitted to {edhi_center_name} successfully',
                'data': {
                    'id': admitted_child.id,
                    'edhi_id': edhi_id,
                    'edhi_name': edhi_center_name,
                    'admission_date': admitted_child.admission_date.isoformat() if admitted_child.admission_date else None
                }
            }), 201

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)}), 500
    @staticmethod
    def get_edhi_user_by_center(center_id):
        try:
            edhi_user = UserModel.query.filter_by(
                edhi_center_id=center_id,
                role=6  # Edhi role
            ).first()

            if edhi_user:
                return jsonify({
                    'success': True,
                    'data': {'id': edhi_user.id, 'name': edhi_user.name}
                })
            else:
                return jsonify({'success': False, 'message': 'No Edhi user found for this center'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500