from datetime import datetime

from flask import request, jsonify
from sqlalchemy import or_

from db import db
from models.ParentModel import ParentModel
from models.RequestModel import RequestModel
from models.UserModel import UserModel
from models.ReportsModel import ReportsModel
from models.ChildModel import ChildModel
from models.PoliceModel import PoliceModel


class PoliceController:
    # CORRECT POLICE STATIONS MAPPING
    POLICE_STATIONS = {
        2: {
            "id": 1,
            "pid": "PS-SAD-001",
            "name": "Police Station Saddar",
            "location": "Saddar Cantt"
        },
        1: {
            "id": 2,
            "pid": "PS-NTW-002",
            "name": "Police Station New Town",
            "location": "Satellite Town"
        },
        3: {
            "id": 3,
            "pid": "PS-SAN-003",
            "name": "Sadiqabd Police Station ",
            "location": "Sadiqabad"
        },
        4: {
            "id": 4,
            "pid": "PS-KOH-004",
            "name": "Waris Khan Police Station",
            "location": "Waris Khan"
        },
        5: {
            "id": 5,
            "pid": "PS-DSD-005",
            "name": "City Police Station",
            "location": "Raja bazar"
        }
    }

    @staticmethod
    def get_station_missing_reports(station_id):
        """Get only missing reports for a station"""
        try:
            print(f"🔍 Fetching missing reports for station: {station_id}")
            print(f"🔍 Station ID type: {type(station_id)}")

            try:
                station_id = int(station_id)
            except:
                pass

            if station_id not in PoliceController.POLICE_STATIONS:
                print(f"❌ Station {station_id} not found in mapping!")
                return jsonify({"success": False, "message": "Station not found"}), 404

            station_info = PoliceController.POLICE_STATIONS[station_id]
            print(f"✅ Station found: {station_info['name']}")

            reports = ReportsModel.query.filter(
                ReportsModel.assigned_police_station_id == station_id,
                ReportsModel.report_type.ilike('missing')
            ).order_by(ReportsModel.date.desc()).all()

            print(f"📊 Found {len(reports)} missing reports")

            output = []
            for r in reports:
                child = ChildModel.query.get(r.child_id)

                # ✅ Get child image path
                child_image = None
                if child:
                    if child.image_path:
                        child_image = child.image_path
                    elif child.images and len(child.images) > 0:
                        child_image = child.images[0]

                report_data = {
                    "id": r.id,
                    "child_id": r.child_id,
                    "child_name": child.name if child else "Unknown",
                    "child_age": child.age if child else None,
                    "child_gender": child.gender if child else None,
                    "child_image": child_image,  # ✅ ADDED
                    "date": r.date,
                    "last_seen_location": r.last_seen_location,
                    "location": r.last_seen_location or r.current_location,
                    "status": r.status,
                    "assignment_status": r.assignment_status,
                    "report_type": r.report_type,
                    "station_id": station_id,
                    "station_name": station_info['name'],
                    "station_pid": station_info['pid']
                }
                output.append(report_data)

            return jsonify({
                "success": True,
                "data": output,
                "count": len(output),
                "station_id": station_id,
                "station_name": station_info['name'],
                "station_pid": station_info['pid']
            }), 200

        except Exception as e:
            print(f"❌ Error in get_station_missing_reports: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_station_found_reports(station_id):
        """Get only found reports for a station"""
        try:
            print(f"🔍 Fetching found reports for station: {station_id}")

            try:
                station_id = int(station_id)
            except:
                pass

            if station_id not in PoliceController.POLICE_STATIONS:
                print(f"❌ Station {station_id} not found in mapping!")
                return jsonify({"success": False, "message": "Station not found"}), 404

            station_info = PoliceController.POLICE_STATIONS[station_id]
            print(f"✅ Station found: {station_info['name']}")

            reports = ReportsModel.query.filter(
                ReportsModel.assigned_police_station_id == station_id,
                ReportsModel.report_type.ilike('found')
            ).order_by(ReportsModel.date.desc()).all()

            print(f"📊 Found {len(reports)} found reports")

            output = []
            for r in reports:
                child = ChildModel.query.get(r.child_id)

                # ✅ Get child image path
                child_image = None
                if child:
                    if child.image_path:
                        child_image = child.image_path
                    elif child.images and len(child.images) > 0:
                        child_image = child.images[0]

                report_data = {
                    "id": r.id,
                    "child_id": r.child_id,
                    "child_name": child.name if child else "Unknown",
                    "child_age": child.age if child else None,
                    "child_gender": child.gender if child else None,
                    "child_image": child_image,  # ✅ ADDED
                    "date": r.date,
                    "found_location": r.found_location,
                    "location": r.found_location or r.current_location,
                    "status": r.status,
                    "assignment_status": r.assignment_status,
                    "report_type": r.report_type,
                    "station_id": station_id,
                    "station_name": station_info['name'],
                    "station_pid": station_info['pid']
                }
                output.append(report_data)

            return jsonify({
                "success": True,
                "data": output,
                "count": len(output),
                "station_id": station_id,
                "station_name": station_info['name'],
                "station_pid": station_info['pid']
            }), 200

        except Exception as e:
            print(f"❌ Error in get_station_found_reports: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_station_all_reports(station_id):
        """Get all reports assigned to a specific police station"""
        try:
            print(f"🔍 get_station_all_reports called for station: {station_id}")

            try:
                station_id = int(station_id)
            except:
                pass

            if station_id not in PoliceController.POLICE_STATIONS:
                print(f"❌ Station {station_id} not found!")
                return jsonify({"success": False, "message": "Station not found"}), 404

            station_info = PoliceController.POLICE_STATIONS[station_id]

            reports = ReportsModel.query.filter_by(
                assigned_police_station_id=station_id
            ).order_by(ReportsModel.date.desc()).all()

            print(f"📊 Found {len(reports)} total reports")

            output = []
            for r in reports:
                child = ChildModel.query.get(r.child_id)

                # ✅ Get child image path
                child_image = None
                if child:
                    if child.image_path:
                        child_image = child.image_path
                    elif child.images and len(child.images) > 0:
                        child_image = child.images[0]

                report_data = {
                    "id": r.id,
                    "child_id": r.child_id,
                    "child_name": child.name if child else "Unknown",
                    "child_age": child.age if child else None,
                    "child_gender": child.gender if child else None,
                    "child_image": child_image,  # ✅ ADDED
                    "status": r.status,
                    "report_type": r.report_type,
                    "date": r.date,
                    "last_seen_location": r.last_seen_location,
                    "current_location": r.current_location,
                    "found_location": r.found_location,
                    "location": r.last_seen_location or r.current_location or r.found_location,
                    "assignment_status": r.assignment_status,
                    "station_name": station_info['name'],
                    "station_pid": station_info['pid']
                }
                output.append(report_data)

            return jsonify({
                "success": True,
                "data": output,
                "count": len(output),
                "station_name": station_info['name'],
                "station_pid": station_info['pid']
            }), 200

        except Exception as e:
            print(f"❌ Error in get_station_all_reports: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_officer_reports(user_id):
        """Get reports for a specific police officer"""
        try:
            officer = UserModel.query.get(user_id)
            if not officer:
                return jsonify({"success": False, "message": "Officer not found"}), 404

            if officer.role != "6":
                return jsonify({"success": False, "message": "Not authorized"}), 403

            if not officer.police_station_id:
                return jsonify({"success": False, "message": "No station assigned"}), 404

            return PoliceController.get_station_all_reports(officer.police_station_id)

        except Exception as e:
            print(f"❌ Error in get_officer_reports: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_officer_missing_reports(user_id):
        """Get missing reports for a police officer"""
        try:
            officer = UserModel.query.get(user_id)
            if not officer or officer.role != "6":
                return jsonify({"success": False, "message": "Not authorized"}), 403

            if not officer.police_station_id:
                return jsonify({"success": False, "message": "No station assigned"}), 404

            return PoliceController.get_station_missing_reports(officer.police_station_id)
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_officer_found_reports(user_id):
        """Get found reports for a police officer"""
        try:
            officer = UserModel.query.get(user_id)
            if not officer or officer.role != "6":
                return jsonify({"success": False, "message": "Not authorized"}), 403

            if not officer.police_station_id:
                return jsonify({"success": False, "message": "No station assigned"}), 404

            return PoliceController.get_station_found_reports(officer.police_station_id)
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_all_stations():
        """Get all police stations"""
        try:
            stations = PoliceModel.query.all()
            output = [
                {
                    "id": s.id,
                    "pid": s.pid,
                    "pname": s.pname,
                    "contact": s.contact_no,
                    "location": s.location,
                    "address": s.address
                } for s in stations
            ]
            return jsonify({"success": True, "data": output, "count": len(output)}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_station_details(station_id):
        """Get single police station details"""
        try:
            station = PoliceModel.query.get(station_id)
            if not station:
                return jsonify({"success": False, "message": "Station not found"}), 404

            return jsonify({
                "success": True,
                "data": {
                    "id": station.id,
                    "pid": station.pid,
                    "pname": station.pname,
                    "contact": station.contact_no,
                    "location": station.location,
                    "address": station.address
                }
            }), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def search_station_reports(station_id):
        """Search reports in a police station with optional filters"""
        try:
            try:
                station_id = int(station_id)
            except:
                pass

            if station_id not in PoliceController.POLICE_STATIONS:
                return jsonify({"success": False, "message": "Station not found"}), 404

            station_info = PoliceController.POLICE_STATIONS[station_id]

            child_id = request.args.get("childId", type=int)
            child_name = request.args.get("childName", "").strip().lower()
            location = request.args.get("location", "").strip().lower()
            date = request.args.get("date", "").strip()

            print(f"🔎 Searching reports at station {station_id} | Filters => "
                  f"childId: {child_id}, childName: {child_name}, location: {location}, date: {date}")

            reports = ReportsModel.query.filter_by(assigned_police_station_id=station_id).all()
            print(f"📊 Total reports for station {station_id}: {len(reports)}")

            if child_id:
                reports = [r for r in reports if r.child_id == child_id]

            if child_name:
                filtered = []
                for r in reports:
                    child = ChildModel.query.get(r.child_id)
                    if child and child.name and child_name in child.name.lower():
                        filtered.append(r)
                reports = filtered

            if location:
                filtered = []
                for r in reports:
                    loc_text = f"{r.last_seen_location or ''} {r.current_location or ''} {r.found_location or ''}".lower()
                    if location in loc_text:
                        filtered.append(r)
                reports = filtered

            if date:
                reports = [r for r in reports if r.date and date in r.date]

            output = []
            for r in reports:
                child = ChildModel.query.get(r.child_id)

                # ✅ Get child image path
                child_image = None
                if child:
                    if child.image_path:
                        child_image = child.image_path
                    elif child.images and len(child.images) > 0:
                        child_image = child.images[0]

                output.append({
                    "report_id": r.id,
                    "child_id": r.child_id,
                    "child_name": child.name if child else "Unknown",
                    "child_age": child.age if child else None,
                    "child_gender": child.gender if child else None,
                    "child_image": child_image,  # ✅ ADDED
                    "report_type": r.report_type,
                    "status": r.status,
                    "assignment_status": r.assignment_status,
                    "date": r.date,
                    "last_seen_location": r.last_seen_location,
                    "current_location": r.current_location,
                    "found_location": r.found_location,
                    "location": r.last_seen_location or r.current_location or r.found_location,
                    "station_name": station_info['name'],
                    "station_pid": station_info['pid']
                })

            return jsonify({
                "success": True,
                "data": output,
                "count": len(output),
                "station_name": station_info['name'],
                "station_pid": station_info['pid'],
                "filters_applied": {
                    "childId": child_id,
                    "childName": child_name,
                    "location": location,
                    "date": date
                }
            }), 200

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def debug_station_data(station_id):
        """Debug endpoint to check station data"""
        try:
            try:
                station_id = int(station_id)
            except:
                pass

            if station_id not in PoliceController.POLICE_STATIONS:
                return jsonify({
                    "success": False,
                    "message": f"Station {station_id} not found in mapping"
                }), 404

            station_info = PoliceController.POLICE_STATIONS[station_id]

            reports = ReportsModel.query.filter_by(
                assigned_police_station_id=station_id
            ).all()

            missing = []
            found = []
            for r in reports:
                if r.report_type and 'missing' in r.report_type.lower():
                    missing.append({
                        "id": r.id,
                        "report_type": r.report_type,
                        "child_id": r.child_id
                    })
                elif r.report_type and 'found' in r.report_type.lower():
                    found.append({
                        "id": r.id,
                        "report_type": r.report_type,
                        "child_id": r.child_id
                    })

            return jsonify({
                "success": True,
                "station": station_info,
                "reports": {
                    "total": len(reports),
                    "missing": len(missing),
                    "found": len(found),
                    "missing_details": missing,
                    "found_details": found
                }
            }), 200

        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def submit_request():
        """Submit either adoption or foster request"""
        try:
            data = request.get_json()

            if not data.get("user_id"):
                return jsonify({"success": False, "message": "User ID required"}), 400

            if not data.get("request_type") or data.get("request_type") not in ['adoption', 'foster']:
                return jsonify({"success": False, "message": "Valid request type (adoption/foster) required"}), 400

            parent = ParentModel.query.filter_by(user_id=data.get("user_id")).first()
            if not parent:
                return jsonify({"success": False, "message": "Please complete parent profile first"}), 400

            existing_request = RequestModel.query.filter_by(
                parent_id=parent.id,
                request_type=data.get("request_type"),
                status="Pending"
            ).first()

            if existing_request:
                return jsonify({
                    "success": False,
                    "message": f"You already have a pending {data.get('request_type')} request"
                }), 400

            new_request = RequestModel(
                parent_id=parent.id,
                edhi_id=data.get("edhi_id"),
                request_type=data.get("request_type"),
                child_gender_preference=data.get("child_gender_preference"),
                reason=data.get("reason"),
                child_ethnicity=data.get("child_ethnicity") if data.get("request_type") == "adoption" else None,
                child_religion=data.get("child_religion") if data.get("request_type") == "adoption" else None,
                address=data.get("address"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                status="Pending",
                request_date=datetime.now()
            )

            db.session.add(new_request)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": f"{data.get('request_type').title()} request submitted successfully",
                "data": {
                    "request_id": new_request.id,
                    "request_type": new_request.request_type,
                    "status": new_request.status,
                    "address": new_request.address,
                    "latitude": float(new_request.latitude) if new_request.latitude else None,
                    "longitude": float(new_request.longitude) if new_request.longitude else None
                }
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500