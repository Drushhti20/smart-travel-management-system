"""Beyond Horizons - Smart Travel Management System Backend Server."""
import logging
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, make_response

from .config import Config
from .database import get_db, is_db_ready, is_using_mock_db
from .routes import auth_bp, trip_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("beyond_horizons")


def create_app(test_config=None):
    """Application factory for Beyond Horizons Flask app."""
    frontend_folder = str(Config.FRONTEND_PATH)
    html_folder = str(Config.HTML_PATH)

    app = Flask(
        __name__,
        static_folder=frontend_folder,
        static_url_path=""
    )

    # Base configuration
    app.config.update(
        SECRET_KEY=Config.SECRET_KEY,
        SESSION_COOKIE_HTTPONLY=Config.SESSION_COOKIE_HTTPONLY,
        SESSION_COOKIE_SAMESITE=Config.SESSION_COOKIE_SAMESITE,
        SESSION_COOKIE_SECURE=Config.SESSION_COOKIE_SECURE,
        PERMANENT_SESSION_LIFETIME=Config.PERMANENT_SESSION_LIFETIME,
    )

    if test_config:
        app.config.update(test_config)

    # Native CORS and Security Headers
    @app.before_request
    def handle_options():
        if request.method == "OPTIONS":
            response = make_response()
            origin = request.headers.get("Origin", "")
            allowed_origins = [
                "http://127.0.0.1:5000",
                "http://localhost:5000",
                "http://127.0.0.1:5500",
                "http://localhost:5500"
            ]
            if origin in allowed_origins or not origin:
                response.headers["Access-Control-Allow-Origin"] = origin or "*"
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
            return response, 200

    @app.after_request
    def apply_cors_and_headers(response):
        origin = request.headers.get("Origin")
        allowed_origins = [
            "http://127.0.0.1:5000",
            "http://localhost:5000",
            "http://127.0.0.1:5500",
            "http://localhost:5500"
        ]
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"

        # Additional security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        return response

    # Register API blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(trip_bp)

    # Initialize Database connection
    with app.app_context():
        get_db()

    # Frontend Page Routes
    @app.get("/")
    def serve_home():
        return send_from_directory(html_folder, "index.html")

    @app.get("/login")
    @app.get("/login.html")
    def serve_login():
        return send_from_directory(html_folder, "login.html")

    @app.get("/register")
    @app.get("/register.html")
    def serve_register():
        return send_from_directory(html_folder, "register.html")

    @app.get("/dashboard")
    @app.get("/dashboard.html")
    def serve_dashboard():
        return send_from_directory(html_folder, "dashboard.html")

    # API Health Check
    @app.get("/api/health")
    def health_check():
        ready = is_db_ready()
        is_mock = is_using_mock_db()
        return jsonify({
            "status": "healthy" if ready else "degraded",
            "service": "Beyond Horizons Travel Management API",
            "version": "1.0.0",
            "database": {
                "ready": ready,
                "type": "in-memory (mongomock)" if is_mock else "MongoDB Atlas",
                "notice": "Operating with real-time in-memory persistence. To connect to MongoDB Atlas, configure MONGODB_URI in your .env file." if is_mock else "Connected to MongoDB Atlas cluster."
            }
        }), 200

    # Error handling
    @app.errorhandler(404)
    def handle_not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({
                "success": False,
                "error": "Endpoint not found",
                "message": f"API endpoint '{request.path}' was not found on this server."
            }), 404
        return send_from_directory(html_folder, "index.html"), 404

    @app.errorhandler(500)
    def handle_server_error(e):
        logger.exception("Internal server error: %s", e)
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected server error occurred. Please try again shortly."
        }), 500

    return app


app = create_app()

if __name__ == "__main__":
    logger.info("Starting Beyond Horizons server on http://127.0.0.1:%s", Config.PORT)
    app.run(
        host="127.0.0.1",
        port=Config.PORT,
        debug=Config.FLASK_DEBUG
    )
