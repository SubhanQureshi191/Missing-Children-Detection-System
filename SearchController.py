from flask import request, jsonify
from models.ReportsModel import ReportsModel
from models.ChildModel import ChildModel
from db import db


class SearchController:

    @staticmethod
    def search_cases():
        try:
            data = request.get_json()
            print(f"🔍 Search request: {data}")

            # Get all reports
            reports = ReportsModel.query.all()

            results = []
            for r in reports:
                child = ChildModel.query.get(r.child_id)

                # Apply filters
                match = True

                if data.get('caseId') and str(r.id) != str(data['caseId']):
                    match = False

                if data.get('childName') and child:
                    if data['childName'].lower() not in child.name.lower():
                        match = False

                if data.get('date') and r.date != data['date']:
                    match = False

                if match:
                    results.append({
                        "id": r.id,
                        "child_name": child.name if child else "Unknown",
                        "child_age": child.age if child else None,
                        "child_gender": child.gender if child else None,
                        "status": r.status or "missing",
                        "date": r.date,
                        "last_seen_location": r.last_seen_location,
                        "current_location": r.current_location,
                        "found_location": r.found_location,
                    })

            return jsonify({
                "success": True,
                "data": results,
                "count": len(results)
            }), 200

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return jsonify({"success": False, "message": str(e)}), 500