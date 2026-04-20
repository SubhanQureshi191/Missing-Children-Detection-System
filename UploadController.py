from flask import request, jsonify
import os
import uuid

from werkzeug.utils import secure_filename


class UploadController:

    @staticmethod
    def upload_image():
        try:
            if 'image' not in request.files:
                return jsonify({"success": False, "message": "No image"}), 400

            file = request.files['image']

            # Create uploads folder
            os.makedirs('uploads', exist_ok=True)

            # Generate unique filename
            ext = file.filename.split('.')[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            filepath = f"uploads/{filename}"

            # Save file
            file.save(filepath)

            return jsonify({
                "success": True,
                "imageUrl": f"/uploads/{filename}"
            })

        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    # Add this to your UploadController.py

    @staticmethod
    def upload_document():
        """Upload document files (CNIC, FRC, etc.)"""
        try:
            file = request.files.get("file")
            file_type = request.form.get("type", "document")

            if not file:
                return jsonify({"success": False, "message": "No file provided"}), 400

            # Create uploads directory if not exists
            os.makedirs("uploads/documents", exist_ok=True)

            # Generate unique filename
            ext = os.path.splitext(file.filename)[1]
            filename = secure_filename(f"{file_type}_{uuid.uuid4().hex}{ext}")
            file_path = os.path.join("uploads/documents", filename)

            # Save file
            file.save(file_path)

            return jsonify({
                "success": True,
                "message": "File uploaded successfully",
                "filePath": filename,
                "fileUrl": f"/uploads/documents/{filename}"
            }), 200

        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500