"""Trip Management API routes."""
from functools import wraps
from flask import Blueprint, jsonify, request, session
from ..services import TripService

trip_bp = Blueprint("trips", __name__, url_prefix="/api/trips")


def login_required(f):
    """Decorator to protect routes requiring an active user session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({
                "success": False,
                "message": "Authentication required. Please log in to continue."
            }), 401
        return f(*args, **kwargs)
    return decorated_function


@trip_bp.get("")
@login_required
def list_trips():
    """Retrieve all trips belonging to the authenticated user."""
    user_id = session.get("user_id")
    trips, error, status_code = TripService.get_user_trips(user_id)
    if error:
        return jsonify({"success": False, "message": error}), status_code

    return jsonify({"success": True, "trips": trips, "count": len(trips)}), 200


@trip_bp.post("")
@login_required
def create_trip():
    """Create a new trip for the authenticated user."""
    user_id = session.get("user_id")
    payload = request.get_json(silent=True) or {}

    trip, error, status_code = TripService.create_trip(user_id, payload)
    if error:
        return jsonify({"success": False, "message": error}), status_code

    return jsonify({
        "success": True,
        "message": "Trip created successfully!",
        "trip": trip
    }), 201


@trip_bp.get("/stats")
@login_required
def trip_stats():
    """Compute and retrieve dashboard summary statistics for the user."""
    user_id = session.get("user_id")
    stats, error, status_code = TripService.get_trip_stats(user_id)
    if error:
        return jsonify({"success": False, "message": error}), status_code

    return jsonify({"success": True, "stats": stats}), 200


@trip_bp.get("/<trip_id>")
@login_required
def get_trip(trip_id):
    """Retrieve details of a single trip owned by the user."""
    user_id = session.get("user_id")
    trip, error, status_code = TripService.get_trip_by_id(trip_id, user_id)
    if error:
        return jsonify({"success": False, "message": error}), status_code

    return jsonify({"success": True, "trip": trip}), 200


@trip_bp.route("/<trip_id>", methods=["PUT", "PATCH"])
@login_required
def update_trip(trip_id):
    """Update an existing trip owned by the user."""
    user_id = session.get("user_id")
    payload = request.get_json(silent=True) or {}

    trip, error, status_code = TripService.update_trip(trip_id, user_id, payload)
    if error:
        return jsonify({"success": False, "message": error}), status_code

    return jsonify({
        "success": True,
        "message": "Trip updated successfully!",
        "trip": trip
    }), 200


@trip_bp.delete("/<trip_id>")
@login_required
def delete_trip(trip_id):
    """Delete a trip owned by the user."""
    user_id = session.get("user_id")
    success, message, status_code = TripService.delete_trip(trip_id, user_id)
    if not success:
        return jsonify({"success": False, "message": message}), status_code

    return jsonify({"success": True, "message": message}), 200
