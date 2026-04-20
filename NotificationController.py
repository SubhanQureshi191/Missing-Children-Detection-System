import json

from flask import jsonify, request
from db import db
from datetime import datetime

from models.NotificationModel import NotificationModel


class NotificationController:

    @staticmethod
    def get_edhi_notifications(edhi_id):
        """Get all notifications for an Edhi center"""
        try:
            print(f"🔍 Fetching notifications for Edhi center ID: {edhi_id}")

            try:
                edhi_id = int(edhi_id)
            except:
                pass

            notifications = NotificationModel.query.filter_by(
                edhi_id=edhi_id
            ).order_by(NotificationModel.created_at.desc()).all()

            unread_count = NotificationModel.query.filter_by(
                edhi_id=edhi_id,
                is_read=False
            ).count()

            result = [n.to_dict() for n in notifications]

            return jsonify({
                "success": True,
                "data": result,
                "count": len(result),
                "unread_count": unread_count,
                "edhi_id": edhi_id
            }), 200

        except Exception as e:
            print(f"❌ Error in get_edhi_notifications: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def mark_notification_read(notification_id):
        """Mark a single notification as read"""
        try:
            notification = NotificationModel.query.get(notification_id)
            if not notification:
                return jsonify({"success": False, "message": "Notification not found"}), 404

            notification.is_read = True
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Notification marked as read",
                "data": notification.to_dict()
            }), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def mark_all_read(edhi_id):
        """Mark all notifications as read for an Edhi center"""
        try:
            print(f"🔍 Marking all notifications as read for Edhi center: {edhi_id}")

            try:
                edhi_id = int(edhi_id)
            except:
                pass

            notifications = NotificationModel.query.filter_by(
                edhi_id=edhi_id,
                is_read=False
            ).all()

            count = len(notifications)
            for n in notifications:
                n.is_read = True

            db.session.commit()

            return jsonify({
                "success": True,
                "message": f"{count} notification{'s' if count != 1 else ''} marked as read",
                "count": count
            }), 200

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in mark_all_read: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def create_notification(edhi_id, user_id, notification_type, title, message, priority="medium", extra_data=None):
        """Create a new notification (utility method)"""
        try:
            print(f"📝 Creating notification for Edhi ID: {edhi_id}")
            print(f"   Type: {notification_type}")
            print(f"   Title: {title}")

            notification = NotificationModel(
                edhi_id=edhi_id,
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                priority=priority,
                is_read=False,
                extra_data=json.dumps(extra_data) if extra_data else None,
                created_at=datetime.utcnow()
            )

            db.session.add(notification)
            db.session.commit()

            print(f"✅ Notification created successfully! ID: {notification.id}")

            return notification

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating notification: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    # ✅ CRITICAL: Method to create notification for Edhi center
    @staticmethod
    def create_notification_for_edhi(edhi_id, notification_type, title, message, extra_data=None):
        """Create notification for Edhi center"""
        try:
            print(f"📝 Creating Edhi notification - Type: {notification_type}")
            print(f"   Edhi ID: {edhi_id}")
            print(f"   Title: {title}")
            print(f"   Message: {message[:100]}..." if len(message) > 100 else f"   Message: {message}")

            notification = NotificationModel(
                edhi_id=edhi_id,
                type=notification_type,
                title=title,
                message=message,
                priority='high',
                is_read=False,
                extra_data=json.dumps(extra_data) if extra_data else None,
                created_at=datetime.utcnow()
            )

            db.session.add(notification)
            db.session.commit()

            print(f"✅ Edhi notification created! ID: {notification.id}")
            return notification

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating Edhi notification: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    # ✅ CRITICAL: Method to handle parent response and notify Edhi
    @staticmethod
    def parent_response_notification():
        """Handle parent's response to child match and notify Edhi center"""
        try:
            data = request.get_json()
            print(f"📥 Parent Response Received: {data}")

            notification_id = data.get('notification_id')
            request_id = data.get('request_id')
            child_id = data.get('child_id')
            parent_id = data.get('parent_id')
            action = data.get('action')
            parent_user_id = data.get('parent_user_id')

            from models.RequestModel import RequestModel
            from models.ParentModel import ParentModel
            from models.ChildModel import ChildModel

            # Get request to find Edhi ID
            request_obj = RequestModel.query.get(request_id)
            child = ChildModel.query.get(child_id)
            parent = ParentModel.query.get(parent_id)

            # Mark notification as read
            notification = NotificationModel.query.get(notification_id)
            if notification:
                notification.is_read = True

            # Update request status based on action
            if request_obj:
                if action == 'accept':
                    request_obj.status = 'Approved'
                elif action == 'reject':
                    request_obj.status = 'Rejected'

            db.session.commit()

            # ✅ Create notification for Edhi center about parent's response
            if request_obj and request_obj.edhi_id:
                edhi_id = request_obj.edhi_id
                notification_type = 'parent_response'
                title = 'Parent Response Received'
                message = f"{parent.full_name if parent else 'A parent'} has {action}ed the child match for {child.name if child else 'child'}."
                extra_data = {
                    'request_id': request_id,
                    'child_id': child_id,
                    'child_name': child.name if child else 'Unknown',
                    'parent_name': parent.full_name if parent else 'Unknown',
                    'action': action,
                    'parent_id': parent_id
                }

                NotificationController.create_notification_for_edhi(
                    edhi_id=edhi_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    extra_data=extra_data
                )

                print(f"✅ Edhi notification created for parent {action}")

            return jsonify({"success": True, "message": f"Parent {action}ed the child match"}), 200

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in parent_response_notification: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def delete_old_notifications(days=30):
        """Delete notifications older than specified days (utility method)"""
        try:
            from datetime import timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            deleted = NotificationModel.query.filter(
                NotificationModel.created_at < cutoff_date
            ).delete()

            db.session.commit()

            return deleted

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error deleting old notifications: {str(e)}")
            return 0

    @staticmethod
    def create_notification_api():
        """Create a new notification via API endpoint (for frontend)"""
        try:
            data = request.get_json()

            user_id = data.get('user_id')
            notification_type = data.get('notification_type')
            title = data.get('title')
            message = data.get('message')

            if not user_id:
                return jsonify({'success': False, 'message': 'User ID is required'}), 400

            if not notification_type:
                return jsonify({'success': False, 'message': 'Notification type is required'}), 400

            if not title:
                return jsonify({'success': False, 'message': 'Title is required'}), 400

            if not message:
                return jsonify({'success': False, 'message': 'Message is required'}), 400

            edhi_id = data.get('edhi_id')
            if not edhi_id:
                from models.EdhiModel import EdhiModel
                edhi_center = EdhiModel.query.filter_by(user_id=user_id).first()
                if edhi_center:
                    edhi_id = edhi_center.id
                else:
                    edhi_id = None

            extra_data = data.get('data', {})

            notification = NotificationModel(
                edhi_id=edhi_id,
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                priority=data.get('priority', 'medium'),
                is_read=False,
                extra_data=json.dumps(extra_data) if extra_data else None,
                created_at=datetime.utcnow()
            )

            db.session.add(notification)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Notification created successfully',
                'data': notification.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in create_notification_api: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_user_notifications(user_id):
        """Get all notifications for a specific user"""
        try:
            print(f"🔍 Fetching notifications for user ID: {user_id}")

            try:
                user_id = int(user_id)
            except:
                pass

            notifications = NotificationModel.query.filter_by(
                user_id=user_id
            ).order_by(NotificationModel.created_at.desc()).all()

            unread_count = NotificationModel.query.filter_by(
                user_id=user_id,
                is_read=False
            ).count()

            result = [n.to_dict() for n in notifications]

            return jsonify({
                "success": True,
                "data": result,
                "count": len(result),
                "unread_count": unread_count,
                "user_id": user_id
            }), 200

        except Exception as e:
            print(f"❌ Error in get_user_notifications: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_parent_notifications(user_id):
        """Get all notifications for a parent"""
        try:
            notifications = NotificationModel.query.filter_by(
                user_id=user_id,
                type='child_match'
            ).order_by(NotificationModel.created_at.desc()).all()

            result = []
            for n in notifications:
                result.append({
                    "id": n.id,
                    "type": n.type,
                    "title": n.title,
                    "message": n.message,
                    "priority": n.priority,
                    "is_read": n.is_read,
                    "extra_data": n.extra_data,
                    "created_at": n.created_at.isoformat() if n.created_at else None
                })

            return jsonify({"success": True, "data": result}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def request_approved_notification():
        """Send notification to parent when request is approved"""
        try:
            data = request.get_json()
            parent_user_id = data.get('parent_user_id')
            request_data = data.get('request_data')
            message = data.get('message')

            notification = NotificationModel(
                user_id=parent_user_id,
                type='request_approved',
                title='✅ Adoption Request Approved!',
                message=message or f'Your adoption request has been approved by Edhi center! They will now match you with a suitable child.',
                priority='high',
                is_read=False,
                extra_data=json.dumps(request_data) if request_data else None,
                created_at=datetime.utcnow()
            )

            db.session.add(notification)
            db.session.commit()

            return jsonify({"success": True, "message": "Notification sent"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def request_rejected_notification():
        """Send notification to parent when request is rejected"""
        try:
            data = request.get_json()
            parent_user_id = data.get('parent_user_id')
            request_data = data.get('request_data')
            message = data.get('message')

            notification = NotificationModel(
                user_id=parent_user_id,
                type='request_rejected',
                title='❌ Adoption Request Rejected',
                message=message or f'Your adoption request has been rejected by Edhi center. Please contact them for more information.',
                priority='high',
                is_read=False,
                extra_data=json.dumps(request_data) if request_data else None,
                created_at=datetime.utcnow()
            )

            db.session.add(notification)
            db.session.commit()

            return jsonify({"success": True, "message": "Notification sent"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def mark_notification_read_by_user(notification_id, user_id):
        """Mark a notification as read (with user verification)"""
        try:
            notification = NotificationModel.query.get(notification_id)

            if not notification:
                return jsonify({"success": False, "message": "Notification not found"}), 404

            if notification.user_id != user_id:
                return jsonify({"success": False, "message": "Unauthorized"}), 403

            notification.is_read = True
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Notification marked as read",
                "data": notification.to_dict()
            }), 200

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in mark_notification_read_by_user: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def get_unread_notifications_count(user_id):
        """Get count of unread notifications for a user"""
        try:
            count = NotificationModel.query.filter_by(
                user_id=user_id,
                is_read=False
            ).count()

            return jsonify({
                "success": True,
                "unread_count": count,
                "user_id": user_id
            }), 200

        except Exception as e:
            print(f"❌ Error in get_unread_notifications_count: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def delete_notification(notification_id):
        """Delete a notification"""
        try:
            notification = NotificationModel.query.get(notification_id)

            if not notification:
                return jsonify({"success": False, "message": "Notification not found"}), 404

            db.session.delete(notification)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Notification deleted successfully"
            }), 200

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error in delete_notification: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500

    @staticmethod
    def create_child_match_notification(parent_user_id, child_data, request_data):
        """Create notification for parent when child match is found"""
        try:
            import json
            from datetime import datetime

            child_image = child_data.get('child_image') or child_data.get('image_path')

            print("📸 Child Match Notification - Image:", child_image)

            extra_data = {
                'child_id': child_data.get('id'),
                'child_name': child_data.get('name'),
                'child_age': child_data.get('age'),
                'child_gender': child_data.get('gender'),
                'child_image': child_image,
                'image_path': child_image,
                'request_id': request_data.get('id')
            }

            notification = NotificationModel(
                user_id=parent_user_id,
                type='child_match',
                title='👶 Child Match Found!',
                message=f"A child matching your preferences has been found!\n\nChild Details:\n• Name: {child_data.get('name')}\n• Age: {child_data.get('age')} years\n• Gender: {child_data.get('gender')}",
                priority='high',
                is_read=False,
                extra_data=json.dumps(extra_data),
                created_at=datetime.utcnow()
            )

            db.session.add(notification)
            db.session.commit()

            print("✅ Child match notification created with image:", child_image)

            return notification

        except Exception as e:
            print("❌ Error creating child match notification:", str(e))
            db.session.rollback()
            return None

    @staticmethod
    def create_found_child_notification(reporter_user_id, child_data, report_data, police_station_data):
        """Create notification for reporter when their missing child is found"""
        try:
            print(f"📝 Creating found child notification...")
            print(f"   Reporter User ID: {reporter_user_id}")

            if not reporter_user_id:
                print("❌ Reporter User ID is required")
                return None

            from models.UserModel import UserModel
            reporter_user = UserModel.query.get(reporter_user_id)
            if not reporter_user:
                print(f"❌ Reporter user not found with ID: {reporter_user_id}")
                return None

            title = "🎉 Your Missing Child Has Been Found!"
            message = f"""Good News! Your missing child has been found and identified.

Child Details:
• Name: {child_data.get('name')}
• Age: {child_data.get('age')} years
• Gender: {child_data.get('gender')}

Please visit the police station immediately to complete the verification process.

📍 Police Station: {police_station_data.get('name', 'N/A')}
🏢 Address: {police_station_data.get('address', 'N/A')}
📞 Contact: {police_station_data.get('phone', 'N/A')}"""

            extra_data = {
                'child_id': child_data.get('id'),
                'child_name': child_data.get('name'),
                'child_age': child_data.get('age'),
                'child_gender': child_data.get('gender'),
                'report_id': report_data.get('id'),
                'police_station_id': police_station_data.get('id'),
                'police_station_name': police_station_data.get('name'),
                'police_station_address': police_station_data.get('address'),
                'police_station_phone': police_station_data.get('phone'),
                'notification_type': 'found_child'
            }

            notification = NotificationModel(
                user_id=reporter_user_id,
                type='found_child',
                title=title,
                message=message,
                priority='high',
                is_read=False,
                extra_data=json.dumps(extra_data),
                created_at=datetime.utcnow()
            )

            db.session.add(notification)
            db.session.commit()

            print(f"✅ Found child notification created! ID: {notification.id}")
            return notification

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating found child notification: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def child_match_api():
        """API to send child match notification to parent"""
        try:
            data = request.get_json()

            parent_user_id = data.get("parent_user_id")
            child_data = data.get("child_data")
            request_data = data.get("request_data")

            print("📥 Child Match API Called")
            print("Parent:", parent_user_id)

            if not parent_user_id or not child_data or not request_data:
                return jsonify({
                    "success": False,
                    "message": "Missing required data"
                }), 400

            notification = NotificationController.create_child_match_notification(
                parent_user_id,
                child_data,
                request_data
            )

            if not notification:
                return jsonify({
                    "success": False,
                    "message": "Failed to create notification"
                }), 500

            return jsonify({
                "success": True,
                "message": "Child details sent successfully",
                "data": notification.to_dict()
            }), 200

        except Exception as e:
            print(f"❌ Error in child_match_api: {str(e)}")
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500