"""Authentication API routes."""
from flask import Blueprint, jsonify, request, session
from ..services import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    """Register a new user account and initialize a session."""
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    confirm = data.get("confirmPassword") if "confirmPassword" in data else data.get("confirm_password")

    user, error, status_code = AuthService.register_user(name, email, password, confirm)
    if error:
        return jsonify({"success": False, "message": error}), status_code

    # Establish session
    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]

    return jsonify({
        "success": True,
        "message": "Account created successfully! Welcome to Beyond Horizons.",
        "user": user
    }), 201


@auth_bp.post("/login")
def login():
    """Authenticate existing user credentials and initialize a session."""
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    user, error, status_code = AuthService.authenticate_user(email, password)
    if error:
        return jsonify({"success": False, "message": error}), status_code

    # Establish session
    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]

    return jsonify({
        "success": True,
        "message": "Signed in successfully. Welcome back!",
        "user": user
    }), 200


@auth_bp.get("/me")
def current_user():
    """Get profile of currently authenticated user."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False, "user": None}), 200

    user = AuthService.get_user_by_id(user_id)
    if not user:
        session.clear()
        return jsonify({"authenticated": False, "user": None}), 200

    return jsonify({"authenticated": True, "user": user}), 200


@auth_bp.post("/logout")
def logout():
    """Terminate user session."""
    session.clear()
    return jsonify({
        "success": True,
        "message": "You have been signed out successfully."
    }), 200
