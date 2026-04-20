# controllers/MatchController.py

from flask import jsonify, request

from controllers.NotificationController import NotificationController
from models.MatchAlertModel import MatchAlertModel
from models.ChildModel import ChildModel
from models.ReportsModel import ReportsModel
from models.PoliceModel import PoliceModel  # 👈 IMPORTANT: Add this
from models.RequestModel import RequestModel
from models.UserModel import UserModel
from db import db
from datetime import datetime
from sqlalchemy import desc


class MatchController:

    @staticmethod
    def get_pending_matches():
        """Get all pending matches"""
        try:
            matches = MatchAlertModel.query.filter_by(
                match_status='pending'
            ).order_by(desc(MatchAlertModel.created_at)).all()

            result = []
            for m in matches:
                child = ChildModel.query.get(m.child_id)
                missing = ReportsModel.query.get(m.missing_report_id)
                found = ReportsModel.query.get(m.found_report_id)

                # Get police station names
                missing_station_name = None
                if missing and missing.assigned_police_station_id:
                    station = PoliceModel.query.get(missing.assigned_police_station_id)
                    if station:
                        missing_station_name = station.pname

                found_station_name = None
                if found and found.assigned_police_station_id:
                    station = PoliceModel.query.get(found.assigned_police_station_id)
                    if station:
                        found_station_name = station.pname

                # Get child images
                from models.ChildImagesModel import ChildImageModel
                images = []
                if child and child.image_path:
                    images.append(child.image_path)
                if child:
                    additional = ChildImageModel.query.filter_by(child_id=child.id).all()
                    for img in additional:
                        images.append(img.image_path)

                result.append({
                    'id': m.id,
                    'match_score': m.match_score,
                    'match_status': m.match_status,
                    'created_at': m.created_at.isoformat() if m.created_at else None,
                    'child': {
                        'id': child.id if child else None,
                        'name': child.name if child else 'Unknown',
                        'age': child.age if child else None,
                        'gender': child.gender if child else None,
                        'images': images[:1]  # Send only first image
                    },
                    'missing_report': {
                        'id': missing.id if missing else None,
                        'date': missing.date if missing else None,
                        'location': missing.last_seen_location if missing else None,
                        'police_station_name': missing_station_name  # 👈 ADD THIS
                    },
                    'found_report': {
                        'id': found.id if found else None,
                        'date': found.date if found else None,
                        'location': found.found_location if found else None,
                        'police_station_name': found_station_name  # 👈 ADD THIS
                    }
                })

            return jsonify({"success": True, "data": result}), 200

        except Exception as e:
            print(f"❌ Error in get_pending_matches: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_matches_for_report(report_id):
        """Get matches for a specific report - ensures opposite types are shown"""
        try:
            # Direct database query instead of FaceMatchService
            report = ReportsModel.query.get(report_id)
            if not report:
                return jsonify({"success": False, "message": "Report not found"}), 404

            # Find matches where this report is either missing or found
            # This ensures we only get matches with opposite report types
            if report.report_type == 'missing':
                # Missing report should match with found reports
                matches = MatchAlertModel.query.filter_by(
                    missing_report_id=report_id,
                    match_status='pending'
                ).order_by(desc(MatchAlertModel.match_score)).all()
                print(f"📊 Missing report {report_id}: Found {len(matches)} matches with found reports")
            else:
                # Found report should match with missing reports
                matches = MatchAlertModel.query.filter_by(
                    found_report_id=report_id,
                    match_status='pending'
                ).order_by(desc(MatchAlertModel.match_score)).all()
                print(f"📊 Found report {report_id}: Found {len(matches)} matches with missing reports")

            result = []
            for m in matches:
                # Get the other report (opposite type)
                if report.report_type == 'missing':
                    other_report = ReportsModel.query.get(m.found_report_id)
                else:
                    other_report = ReportsModel.query.get(m.missing_report_id)

                # Get child info
                child = ChildModel.query.get(m.child_id)

                # 👇👇👇 IMPORTANT: Get police station name for the matched report
                police_station_name = None
                if other_report and other_report.assigned_police_station_id:
                    station = PoliceModel.query.get(other_report.assigned_police_station_id)
                    if station:
                        police_station_name = station.pname

                result.append({
                    'match_id': m.id,
                    'match_score': m.match_score,
                    'match_status': m.match_status,
                    'created_at': m.created_at.isoformat() if m.created_at else None,
                    'matched_report': {
                        'id': other_report.id if other_report else None,
                        'report_type': other_report.report_type if other_report else None,
                        'date': other_report.date if other_report else None,
                        'location': other_report.last_seen_location or other_report.found_location if other_report else None,
                        'police_station_name': police_station_name  # 👈 ADD THIS
                    },
                    'matched_child': {
                        'id': child.id if child else None,
                        'name': child.name if child else 'Unknown',
                        'age': child.age if child else None,
                        'gender': child.gender if child else None
                    }
                })

            return jsonify({
                "success": True,
                "data": result,
                "count": len(result)
            }), 200

        except Exception as e:
            print(f"❌ Error in get_matches_for_report: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def verify_match(match_id):
        """Verify a match"""
        try:
            match = MatchAlertModel.query.get(match_id)
            if not match:
                return jsonify({"success": False, "message": "Match not found"}), 404

            # Update status only - verified_at and verified_by removed
            match.match_status = 'verified'
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Match verified successfully"
            }), 200

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in verify_match: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def reject_match(match_id):
        """Reject a match"""
        try:
            match = MatchAlertModel.query.get(match_id)
            if not match:
                return jsonify({"success": False, "message": "Match not found"}), 404

            match.match_status = 'rejected'
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Match rejected successfully"
            }), 200

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in reject_match: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_matched_children():
        """Get all matched children with their details"""
        try:
            # Get all verified matches
            verified_matches = MatchAlertModel.query.filter_by(
                match_status='verified'
            ).order_by(desc(MatchAlertModel.created_at)).all()

            result = []
            for match in verified_matches:
                child = ChildModel.query.get(match.child_id)
                if child:
                    # Get associated reports
                    missing_report = ReportsModel.query.get(match.missing_report_id)
                    found_report = ReportsModel.query.get(match.found_report_id)

                    # Get parent info if available
                    parent_contact = None
                    parent_name = None
                    if missing_report and missing_report.parent_contact:
                        parent_contact = missing_report.parent_contact
                        parent_name = missing_report.parent_name

                    # Get police station info
                    police_station = None
                    if missing_report and missing_report.assigned_police_station_id:
                        station = PoliceModel.query.get(missing_report.assigned_police_station_id)
                        if station:
                            police_station = station.pname

                    # Get child images
                    from models.ChildImagesModel import ChildImageModel
                    images = []
                    if child.image_path:
                        images.append(child.image_path)
                    additional_images = ChildImageModel.query.filter_by(child_id=child.id).all()
                    for img in additional_images:
                        images.append(img.image_path)

                    result.append({
                        'id': child.id,
                        'name': child.name,
                        'age': child.age,
                        'gender': child.gender,
                        'current_location': missing_report.last_seen_location if missing_report else None,
                        'found_location': found_report.found_location if found_report else None,
                        'parent_name': parent_name,
                        'parent_contact': parent_contact,
                        'match_confidence': match.match_score,
                        'match_date': match.created_at.isoformat() if match.created_at else None,
                        'match_status': match.match_status,
                        'police_station': police_station,
                        'images': images[:1]  # First image only
                    })

            return jsonify({
                "success": True,
                "data": result,
                "count": len(result)
            }), 200

        except Exception as e:
            print(f"❌ Error in get_matched_children: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_matched_child_details(child_id):
        """Get detailed information for a specific matched child"""
        try:
            child = ChildModel.query.get(child_id)
            if not child:
                return jsonify({"success": False, "message": "Child not found"}), 404

            # Find the verified match for this child
            match = MatchAlertModel.query.filter_by(
                child_id=child_id,
                match_status='verified'
            ).first()

            if not match:
                return jsonify({"success": False, "message": "No verified match found for this child"}), 404

            # Get associated reports
            missing_report = ReportsModel.query.get(match.missing_report_id)
            found_report = ReportsModel.query.get(match.found_report_id)

            # Get parent info
            parent_contact = None
            parent_name = None
            if missing_report:
                parent_contact = missing_report.parent_contact
                parent_name = missing_report.parent_name

            # Get police station info
            police_station = None
            if missing_report and missing_report.assigned_police_station_id:
                station = PoliceModel.query.get(missing_report.assigned_police_station_id)
                if station:
                    police_station = station.pname

            # Get child images
            from models.ChildImagesModel import ChildImageModel
            images = []
            if child.image_path:
                images.append(child.image_path)
            additional_images = ChildImageModel.query.filter_by(child_id=child.id).all()
            for img in additional_images:
                images.append(img.image_path)

            # Get all matches related to this child (for history)
            all_matches = MatchAlertModel.query.filter_by(
                child_id=child_id
            ).order_by(desc(MatchAlertModel.created_at)).all()

            match_history = []
            for m in all_matches:
                match_history.append({
                    'match_id': m.id,
                    'match_score': m.match_score,
                    'match_status': m.match_status,
                    'created_at': m.created_at.isoformat() if m.created_at else None,
                    'report_type': 'missing' if m.missing_report_id else 'found'
                })

            result = {
                'id': child.id,
                'name': child.name,
                'age': child.age,
                'gender': child.gender,
                'address': child.address,
                'identification_mark': child.identification_mark,
                'current_location': missing_report.last_seen_location if missing_report else None,
                'found_location': found_report.found_location if found_report else None,
                'parent_name': parent_name,
                'parent_contact': parent_contact,
                'match_confidence': match.match_score,
                'match_date': match.created_at.isoformat() if match.created_at else None,
                'match_status': match.match_status,
                'police_station': police_station,
                'images': images,
                'match_history': match_history,
                'report_details': {
                    'missing_report': {
                        'id': missing_report.id if missing_report else None,
                        'date': missing_report.date.isoformat() if missing_report and missing_report.date else None,
                        'location': missing_report.last_seen_location if missing_report else None,
                        'status': missing_report.status if missing_report else None
                    } if missing_report else None,
                    'found_report': {
                        'id': found_report.id if found_report else None,
                        'date': found_report.date.isoformat() if found_report and found_report.date else None,
                        'location': found_report.found_location if found_report else None,
                        'status': found_report.status if found_report else None
                    } if found_report else None
                }
            }

            return jsonify({
                "success": True,
                "data": result
            }), 200

        except Exception as e:
            print(f"❌ Error in get_matched_child_details: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def alert_parent(child_id):
        """Send alert to parent about matched child"""
        try:
            child = ChildModel.query.get(child_id)
            if not child:
                return jsonify({"success": False, "message": "Child not found"}), 404

            # Find the verified match
            match = MatchAlertModel.query.filter_by(
                child_id=child_id,
                match_status='verified'
            ).first()

            if not match:
                return jsonify({"success": False, "message": "No verified match found"}), 404

            # Get parent contact from missing report
            missing_report = ReportsModel.query.get(match.missing_report_id)

            if missing_report and missing_report.parent_contact:
                parent_contact = missing_report.parent_contact
                parent_name = missing_report.parent_name or 'Parent'

                # Here you would integrate SMS/Email service
                # Example: send_sms(parent_contact, f"Your child {child.name} has been found!")
                # Example: send_email(parent_email, "Child Found", f"Your child {child.name} has been matched!")

                print(f"📱 Sending alert to {parent_name} at {parent_contact}")
                print(f"👶 Child: {child.name} (Age: {child.age})")
                print(f"📍 Found at: {match.found_report_id}")

                # Update match status to indicate alert sent
                match.alert_sent = True
                match.alert_sent_at = datetime.now()
                db.session.commit()

                return jsonify({
                    "success": True,
                    "message": f"Alert sent successfully to {parent_name}",
                    "parent_contact": parent_contact,
                    "parent_name": parent_name,
                    "alert_sent_at": datetime.now().isoformat()
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "message": "Parent contact information not found for this child"
                }), 404

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error sending alert: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def send_to_edhi(child_id):
        """Send child to Edhi center"""
        try:
            child = ChildModel.query.get(child_id)
            if not child:
                return jsonify({"success": False, "message": "Child not found"}), 404

            # Find the verified match
            match = MatchAlertModel.query.filter_by(
                child_id=child_id,
                match_status='verified'
            ).first()

            if not match:
                return jsonify({"success": False, "message": "No verified match found"}), 404

            # Get found report location for nearest Edhi center
            found_report = ReportsModel.query.get(match.found_report_id)

            # Find nearest Edhi center based on location
            edhi_center = None
            edhi_center_name = "Default Edhi Center"
            edhi_contact = "042-111-334-444"

            if found_report and found_report.found_location:
                # You can implement logic to find nearest Edhi center
                # For now, get first available Edhi center
                from models.EdhiModel import EdhiModel
                edhi = EdhiModel.query.first()
                if edhi:
                    edhi_center_name = edhi.center_name
                    edhi_contact = edhi.contact_number

            # Update child status
            child.status = 'sent_to_edhi'

            # Create record in Edhi model if needed
            from models.EdhiModel import EdhiModel
            existing_edhi_record = EdhiModel.query.filter_by(child_id=child_id).first()
            if not existing_edhi_record:
                new_edhi_record = EdhiModel(
                    child_id=child_id,
                    center_name=edhi_center_name,
                    status='pending',
                    assigned_date=datetime.now()
                )
                db.session.add(new_edhi_record)

            db.session.commit()

            print(f"🏥 Sending child {child.name} (ID: {child_id}) to {edhi_center_name}")

            return jsonify({
                "success": True,
                "message": f"Child sent to {edhi_center_name} successfully",
                "edhi_center": edhi_center_name,
                "edhi_contact": edhi_contact,
                "child_name": child.name,
                "child_age": child.age,
                "status": "sent_to_edhi"
            }), 200

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error sending to Edhi: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_reports_by_child(child_id):
        """Get all reports associated with a child"""
        try:
            child = ChildModel.query.get(child_id)
            if not child:
                return jsonify({"success": False, "message": "Child not found"}), 404

            # Get all reports for this child
            reports = ReportsModel.query.filter_by(child_id=child_id).all()

            result = []
            for report in reports:
                # Get police station name if assigned
                police_station_name = None
                if report.assigned_police_station_id:
                    station = PoliceModel.query.get(report.assigned_police_station_id)
                    if station:
                        police_station_name = station.pname

                result.append({
                    'id': report.id,
                    'report_type': report.report_type,
                    'date': report.date.isoformat() if report.date else None,
                    'location': report.last_seen_location or report.found_location,
                    'status': report.status,
                    'description': report.description,
                    'police_station': police_station_name,
                    'parent_contact': report.parent_contact,
                    'parent_name': report.parent_name
                })

            return jsonify({
                "success": True,
                "data": result,
                "count": len(result)
            }), 200

        except Exception as e:
            print(f"❌ Error fetching reports: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def send_child():
        try:
            data = request.get_json()

            request_id = data.get('request_id')
            parent_user_id = data.get('parent_user_id')
            child_id = data.get('child_id')

            if not all([request_id, parent_user_id, child_id]):
                return jsonify({
                    "success": False,
                    "message": "Missing required fields"
                }), 400

            child = ChildModel.query.get(child_id)
            req = RequestModel.query.get(request_id)

            if not child:
                return jsonify({"success": False, "message": "Child not found"}), 404

            if not req:
                return jsonify({"success": False, "message": "Request not found"}), 404

            # ===============================
            # ✅ FIXED IMAGE FETCH
            # ===============================
            from models.ChildImageModel import ChildImageModel

            child_image_path = None

            image_obj = ChildImageModel.query.filter_by(child_id=child.id).first()

            if image_obj:
                child_image_path = image_obj.image_path

            if not child_image_path and hasattr(child, 'image_path'):
                child_image_path = child.image_path

            print("📸 FINAL IMAGE:", child_image_path)

            # ===============================
            # CHILD DATA
            # ===============================
            child_dict = {
                'id': child.id,
                'name': child.name,
                'age': child.age,
                'gender': child.gender,
                'identification_mark': child.identification_mark,
                'description': child.description,
                'child_image': child_image_path,
                'image_path': child_image_path,
            }

            req_dict = {
                'id': req.id,
                'status': req.status
            }

            NotificationController.create_child_match_notification(
                parent_user_id,
                child_dict,
                req_dict
            )

            return jsonify({
                "success": True,
                "message": "Child sent successfully",
                "data": child_dict
            }), 200

        except Exception as e:
            print("❌ ERROR:", str(e))
            return jsonify({"success": False, "message": str(e)}), 500