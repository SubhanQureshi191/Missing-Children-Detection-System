from datetime import datetime, timedelta
from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
from db import db, init_db

# Import Controllers
from controllers.UserController import UserController
from controllers.ChildController import ChildController
from controllers.ParentController import ParentController
from controllers.UploadController import UploadController
from controllers.ReportsController import ReportsController
from controllers.PoliceController import PoliceController
from controllers.EdhiController import EdhiController
from controllers.MatchController import MatchController
from controllers.RequestController import RequestController
from controllers.NotificationController import NotificationController
from controllers.ChildAdmissionController import ChildAdmissionController
from controllers.ChildAllocationController import ChildAllocationController

# Import Models
from models.UserModel import UserModel
from models.ChildModel import ChildModel
from models.ChildImagesModel import ChildImageModel
from models.ReportsModel import ReportsModel
from models.ParentModel import ParentModel
from models.RequestModel import RequestModel
from models.EdhiModel import EdhiModel
from models.PoliceModel import PoliceModel
from models.GrantsCustodyModel import GrantsCustodyModel
from models.NotificationModel import NotificationModel
from models.ChildAdmissionModel import ChildAdmissionModel
from models.ChildAllocationModel import ChildAllocationModel

app = Flask(__name__)
CORS(app)
init_db(app)

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return "Missing Children API Running"

# ==================== USER ROUTES ====================
@app.route('/sign_up', methods=['POST'])
def sign_up():
    return UserController.sign_up()


@app.route('/login', methods=['POST'])
def login():
    return UserController.login()


@app.route("/user/me", methods=["GET"])
def get_current_user():
    return UserController.get_current_user(request)


# ==================== CHILD ROUTES ====================
@app.route('/child/create', methods=['POST'])
def create_child():
    return ChildController.create_child()


@app.route('/child/<int:child_id>/images', methods=['GET'])
def get_child_images(child_id):
    return ChildController.get_child_images(child_id)


@app.route('/child/<int:child_id>', methods=['GET'])
def get_child_by_id(child_id):
    return ChildController.get_child_by_id(child_id)


# ==================== REPORT ROUTES ====================
@app.route('/report/create', methods=['POST'])
def create_report():
    return ReportsController.create_report()


@app.route('/report/user/<int:user_id>', methods=['GET'])
def get_user_reports(user_id):
    return ReportsController.get_user_reports(user_id)


@app.route('/report/<int:report_id>', methods=['GET'])
def get_report_by_id(report_id):
    return ReportsController.get_report_by_id(report_id)


@app.route('/report/finder/<int:user_id>', methods=['GET'])
def get_finder_reports(user_id):
    return ReportsController.get_finder_reports(user_id)


# ==================== PARENT ROUTES ====================
@app.route('/parent/create_profile', methods=['POST'])
def create_parent_profile():
    return ParentController.create_parent_profile()


@app.route('/parent/profile/<int:user_id>', methods=['GET'])
def get_parent_profile(user_id):
    return ParentController.get_parent_profile(user_id)


@app.route('/parent/requests/<int:user_id>', methods=['GET'])
def get_parent_requests_by_user(user_id):
    return ParentController.get_parent_requests(user_id)


@app.route('/request/submit', methods=['POST'])
def submit_request():
    return ParentController.submit_request()


# ==================== UPLOAD ROUTES ====================
@app.route('/upload/image', methods=['POST'])
def upload_image():
    return UploadController.upload_image()


@app.route('/upload/document', methods=['POST'])
def upload_document():
    return UploadController.upload_document()


@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory('uploads', filename)


# ==================== POLICE ROUTES ====================
@app.route('/police/station/<int:station_id>/all', methods=['GET'])
def get_station_all_reports(station_id):
    return PoliceController.get_station_all_reports(station_id)


@app.route('/police/station/<int:station_id>/missing', methods=['GET'])
def get_station_missing_reports(station_id):
    return PoliceController.get_station_missing_reports(station_id)


@app.route('/police/station/<int:station_id>/found', methods=['GET'])
def get_station_found_reports(station_id):
    return PoliceController.get_station_found_reports(station_id)


@app.route('/police/station/<int:station_id>', methods=['GET'])
def get_station_details(station_id):
    return PoliceController.get_station_details(station_id)


@app.route('/police/officer/<int:user_id>/reports', methods=['GET'])
def get_officer_reports(user_id):
    return PoliceController.get_officer_reports(user_id)


@app.route('/police/officer/<int:user_id>/missing', methods=['GET'])
def get_officer_missing_reports(user_id):
    return PoliceController.get_officer_missing_reports(user_id)


@app.route('/police/officer/<int:user_id>/found', methods=['GET'])
def get_officer_found_reports(user_id):
    return PoliceController.get_officer_found_reports(user_id)


@app.route('/police/stations', methods=['GET'])
def get_all_stations():
    return PoliceController.get_all_stations()


@app.route('/police/station/<int:station_id>/search', methods=['GET'])
def search_station_reports(station_id):
    return PoliceController.search_station_reports(station_id)


# ==================== EDHI ROUTES ====================
@app.route('/edhi/create', methods=['POST'])
def create_edhi_center():
    return EdhiController.create_edhi_center()


@app.route('/edhi/center/user/<int:user_id>', methods=['GET'])
def get_edhi_center_by_user(user_id):
    return EdhiController.get_edhi_center(user_id)


@app.route('/edhi/center/<int:edhi_id>', methods=['GET'])
def get_edhi_center_by_id(edhi_id):
    return EdhiController.get_edhi_by_id(edhi_id)


@app.route('/edhi/all', methods=['GET'])
def get_all_edhi():
    return EdhiController.get_all_edhi_centers()


@app.route('/edhi/<int:edhi_id>', methods=['PUT'])
def update_edhi_center(edhi_id):
    return EdhiController.update_edhi_center(edhi_id)


@app.route('/edhi/<int:edhi_id>', methods=['DELETE'])
def delete_edhi_center(edhi_id):
    return EdhiController.delete_edhi_center(edhi_id)

@app.route('/edhi/nearest', methods=['POST'])
def find_nearest_edhi():
    return ParentController.find_nearest_edhi()

# ==================== EDHI ADMISSION ROUTES ====================
@app.route('/edhi/admit-child', methods=['POST'])
def admit_child_to_edhi_route():
    return ReportsController.admit_child_to_edhi()


@app.route('/edhi/user/by-center/<int:center_id>', methods=['GET'])
def get_edhi_user_by_center_route(center_id):
    return ReportsController.get_edhi_user_by_center(center_id)


@app.route('/police/station/<int:station_id>/found', methods=['GET'])
def get_station_found_reports_route(station_id):
    return ReportsController.get_found_reports_for_station(station_id)

# ==================== MATCH ROUTES ====================
@app.route('/matches/report/<int:report_id>', methods=['GET'])
def get_matches_for_report(report_id):
    return MatchController.get_matches_for_report(report_id)


@app.route('/matches/pending', methods=['GET'])
def get_pending_matches():
    return MatchController.get_pending_matches()


@app.route('/matches/<int:match_id>/verify', methods=['PUT'])
def verify_match(match_id):
    return MatchController.verify_match(match_id)


@app.route('/matches/<int:match_id>/reject', methods=['PUT'])
def reject_match(match_id):
    return MatchController.reject_match(match_id)


# ==================== MATCHED CHILD ROUTES ====================
@app.route('/child/<int:child_id>/alert-parent', methods=['POST'])
def alert_parent(child_id):
    return MatchController.alert_parent(child_id)


@app.route('/child/<int:child_id>/send-to-edhi', methods=['POST'])
def send_to_edhi(child_id):
    return MatchController.send_to_edhi(child_id)


@app.route('/reports/child/<int:child_id>', methods=['GET'])
def get_reports_by_child(child_id):
    return MatchController.get_reports_by_child(child_id)


@app.route('/matched-children', methods=['GET'])
def get_matched_children():
    return MatchController.get_matched_children()

@app.route('/matches/send-child', methods=['POST'])
def send_child():
    return MatchController.send_child()

@app.route('/matched-child/<int:child_id>', methods=['GET'])
def get_matched_child_details(child_id):
    return MatchController.get_matched_child_details(child_id)


@app.route('/children/available', methods=['GET'])
def get_available_children():
    """Get available children based on filters"""
    return ChildController.get_available_children()

# ==================== REQUEST ROUTES ====================
@app.route('/requests/edhi/<int:edhi_id>', methods=['GET'])
def get_edhi_requests(edhi_id):
    return RequestController.get_edhi_requests(edhi_id)


@app.route('/requests/parent/<int:user_id>', methods=['GET'])
def get_parent_requests_by_user_id(user_id):
    return RequestController.get_parent_requests(user_id)


@app.route('/requests/<int:request_id>/status', methods=['PUT'])
def update_request_status_route(request_id):
    """Update request status"""
    return RequestController.update_request_status(request_id)


@app.route('/requests/<int:request_id>', methods=['GET'])
def get_request_by_id_route(request_id):
    """Get a single request by ID"""
    return RequestController.get_request_by_id(request_id)


@app.route('/request/create', methods=['POST'])
def create_request_route():
    """Create a new adoption/foster request"""
    return RequestController.create_request()


@app.route('/requests/parent-id/<int:parent_id>', methods=['GET'])
def get_requests_by_parent_route(parent_id):
    """Get all requests for a specific parent by parent_id"""
    return RequestController.get_request_by_parent(parent_id)


@app.route('/requests/edhi/<int:edhi_id>/matched', methods=['GET'])
def get_matched_requests_route(edhi_id):
    """Get all matched requests for an Edhi center"""
    return RequestController.get_matched_requests(edhi_id)


@app.route('/request/<int:request_id>', methods=['DELETE'])
def delete_request_route(request_id):
    """Delete a request"""
    return RequestController.delete_request(request_id)


# ==================== CHILD ROUTES (Edhi specific) ====================
@app.route('/children/edhi/<int:edhi_id>', methods=['GET'])
def get_edhi_children(edhi_id):
    return ChildController.get_edhi_children(edhi_id)


# ==================== NOTIFICATION ROUTES ====================
@app.route('/notifications/edhi/<int:edhi_id>', methods=['GET'])
def get_edhi_notifications(edhi_id):
    """Get all notifications for an Edhi center"""
    return NotificationController.get_edhi_notifications(edhi_id)


@app.route('/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    return NotificationController.mark_notification_read(notification_id)


@app.route('/notifications/edhi/<int:edhi_id>/mark-all-read', methods=['PUT'])
def mark_all_notifications_read(edhi_id):
    """Mark all notifications as read for an Edhi center"""
    return NotificationController.mark_all_read(edhi_id)


@app.route('/notifications/create', methods=['POST'])
def create_notification_api():
    """Create a new notification via API"""
    return NotificationController.create_notification_api()


@app.route('/notifications/user/<int:user_id>', methods=['GET'])
def get_user_notifications(user_id):
    """Get all notifications for a specific user"""
    return NotificationController.get_user_notifications(user_id)


@app.route('/notifications/parent/<int:parent_id>', methods=['GET'])
def get_parent_notifications(parent_id):
    """Get all notifications for a parent"""
    return NotificationController.get_parent_notifications(parent_id)


@app.route('/notifications/<int:notification_id>/read/<int:user_id>', methods=['PUT'])
def mark_notification_read_by_user(notification_id, user_id):
    """Mark a notification as read (with user verification)"""
    return NotificationController.mark_notification_read_by_user(notification_id, user_id)


@app.route('/notifications/unread/<int:user_id>', methods=['GET'])
def get_unread_notifications_count(user_id):
    """Get count of unread notifications for a user"""
    return NotificationController.get_unread_notifications_count(user_id)


@app.route('/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Delete a notification"""
    return NotificationController.delete_notification(notification_id)

# ==================== NOTIFICATION ENDPOINTS (ADDED) ====================

@app.route('/notifications/request-approved', methods=['POST'])
def request_approved_notification():
    """Send notification to parent when request is approved"""
    return NotificationController.request_approved_notification()


@app.route('/notifications/request-rejected', methods=['POST'])
def request_rejected_notification():
    """Send notification to parent when request is rejected"""
    return NotificationController.request_rejected_notification()


@app.route('/notifications/parent-response', methods=['POST'])
def parent_response_notification():
    """Handle parent's response and notify Edhi center"""
    return NotificationController.parent_response_notification()


@app.route('/notifications/child-match', methods=['POST'])
def child_match_notification():
    """Create child match notification for parent"""
    return NotificationController.child_match_api()


@app.route('/notifications/found-child', methods=['POST'])
def found_child_notification():
    """Create notification when child is found"""
    return NotificationController.create_found_child_notification_api()


@app.route('/notifications/<int:notification_id>', methods=['GET'])
def get_notification_by_id(notification_id):
    """Get a single notification by ID"""
    try:
        notification = NotificationModel.query.get(notification_id)
        if not notification:
            return jsonify({"success": False, "message": "Notification not found"}), 404
        return jsonify({"success": True, "data": notification.to_dict()}), 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


# ==================== CHILD ADMISSION ROUTES ====================
@app.route('/child/transfer-to-edhi', methods=['POST'])
def transfer_child_to_edhi():
    """Transfer a child from police station to Edhi center"""
    return ChildAdmissionController.transfer_child_to_edhi()


@app.route('/child/admissions/edhi/<int:edhi_id>', methods=['GET'])
def get_edhi_admitted_children(edhi_id):
    """Get all children admitted to an Edhi center"""
    return ChildAdmissionController.get_edhi_admitted_children(edhi_id)


@app.route('/child/admissions/edhi/<int:edhi_id>/allocated', methods=['GET'])
def get_edhi_allocated_children(edhi_id):
    """Get all children allocated from an Edhi center"""
    return ChildAdmissionController.get_edhi_allocated_children(edhi_id)


@app.route('/child/admissions/<int:admission_id>/allocate', methods=['PUT'])
def allocate_child_to_parent(admission_id):
    """Allocate child to a parent (adoption/foster)"""
    return ChildAdmissionController.allocate_child_to_parent(admission_id)


@app.route('/child/admissions/<int:admission_id>/return', methods=['PUT'])
def return_child_to_parent(admission_id):
    """Return child to parents"""
    return ChildAdmissionController.return_child_to_parent(admission_id)


@app.route('/child/admissions/all', methods=['GET'])
def get_all_admissions():
    """Get all child admissions (admin)"""
    return ChildAdmissionController.get_all_admissions()


@app.route('/child/admissions/police/<int:police_station_id>', methods=['GET'])
def get_police_station_transfers(police_station_id):
    """Get all transfers from a police station"""
    return ChildAdmissionController.get_police_station_transfers(police_station_id)

# ==================== CHILD ALLOCATION ROUTES ====================
@app.route('/child/allocate', methods=['POST'])
def allocate_child():
    """Allocate a child to a parent (adoption/foster)"""
    return ChildAllocationController.allocate_child_to_parent()


@app.route('/child/allocate-direct', methods=['POST'])
def allocate_child_direct():
    """Direct allocation of child to parent"""
    return ChildAllocationController.allocate_child_to_parent()


@app.route('/child/allocate-from-request', methods=['POST'])
def allocate_child_from_request():
    """Allocate child to parent from approved request"""
    return ChildAdmissionController.allocate_child_from_request()


@app.route('/child/allocations/edhi/<int:edhi_id>', methods=['GET'])
def get_edhi_allocations(edhi_id):
    """Get all allocations from a specific Edhi center"""
    return ChildAllocationController.get_edhi_allocated_children(edhi_id)


@app.route('/child/allocations/parent/<int:parent_id>', methods=['GET'])
def get_parent_allocations(parent_id):
    """Get all allocations for a specific parent"""
    return ChildAllocationController.get_parent_allocated_children(parent_id)


@app.route('/child/allocation/<int:allocation_id>', methods=['GET'])
def get_allocation_details(allocation_id):
    """Get detailed information about a specific allocation"""
    return ChildAllocationController.get_child_allocation_details(allocation_id)


@app.route('/child/allocation/<int:allocation_id>/status', methods=['PUT'])
def update_allocation_status(allocation_id):
    """Update allocation status (complete, terminate, etc.)"""
    return ChildAllocationController.update_allocation_status(allocation_id)


@app.route('/child/allocations/all', methods=['GET'])
def get_all_allocations():
    """Get all allocations with filters (admin only)"""
    return ChildAllocationController.get_all_allocations()

@app.route('/child/foster/reviews', methods=['GET'])
def get_foster_reviews():
    """Get foster care cases that need review"""
    return ChildAllocationController.get_foster_care_reviews()

# ==================== FACE MATCH ROUTE ====================
@app.route('/api/face-match', methods=['POST'])
def face_match():
    try:
        data = request.get_json()
        img1_path = data.get('image1')
        img2_path = data.get('image2')

        from services.FaceMatchService import FaceMatchService
        result = FaceMatchService.verify_faces_direct(img1_path, img2_path)

        if result:
            clean_result = {
                'is_match': bool(result.get('is_match', False)),
                'similarity': float(result.get('similarity', 0)),
                'distance': float(result.get('distance', 0))
            }
        else:
            clean_result = None

        return jsonify({
            "success": True,
            "data": clean_result
        }), 200

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ==================== CUSTOM JSON ENCODER ====================
import json
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super(NumpyEncoder, self).default(obj)


if __name__ == '__main__':
    app.run(debug=True)