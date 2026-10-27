"""Authentication and User Account service."""
import re
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, PyMongoError
from werkzeug.security import check_password_hash, generate_password_hash
from ..database import get_db, is_db_ready

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z0-9-]{2,}$")


class AuthService:
    """Service handling registration, authentication, and user data retrieval."""

    @staticmethod
    def validate_email(email):
        """Validate email format and length."""
        if not isinstance(email, str):
            return False
        clean = email.strip()
        if len(clean) > 254 or len(clean) < 5:
            return False
        return bool(EMAIL_REGEX.match(clean))

    @staticmethod
    def serialize_user(user_doc):
        """Format MongoDB user document for safe JSON serialization."""
        if not user_doc:
            return None
        return {
            "id": str(user_doc["_id"]),
            "name": user_doc.get("name", ""),
            "email": user_doc.get("email", ""),
            "created_at": user_doc.get("created_at", "").isoformat() if isinstance(user_doc.get("created_at"), datetime) else str(user_doc.get("created_at", ""))
        }

    @classmethod
    def register_user(cls, name, email, password, confirm_password):
        """
        Validate and register a new user.
        Returns (user_dict, error_message, status_code).
        """
        if not is_db_ready():
            return None, "Database service is not ready. Please verify configuration.", 503

        name = str(name or "").strip()
        email = str(email or "").strip().lower()

        if len(name) < 2 or len(name) > 80:
            return None, "Full name must be between 2 and 80 characters.", 400

        if not cls.validate_email(email):
            return None, "Please enter a valid email address.", 400

        if not isinstance(password, str) or len(password) < 8:
            return None, "Password must be at least 8 characters long.", 400

        if password != confirm_password:
            return None, "Passwords do not match.", 400

        db = get_db()
        try:
            # Check existing email
            existing = db.users.find_one({"email": email})
            if existing:
                return None, "An account with this email address already exists. Please log in.", 409

            password_hash = generate_password_hash(password)
            now = datetime.now(timezone.utc)
            user_doc = {
                "name": name,
                "email": email,
                "password_hash": password_hash,
                "created_at": now
            }

            result = db.users.insert_one(user_doc)
            user_doc["_id"] = result.inserted_id
            return cls.serialize_user(user_doc), None, 201

        except DuplicateKeyError:
            return None, "An account with this email address already exists. Please log in.", 409
        except PyMongoError as err:
            return None, f"Database error occurred: {str(err)}", 500

    @classmethod
    def authenticate_user(cls, email, password):
        """
        Authenticate user credentials.
        Returns (user_dict, error_message, status_code).
        """
        if not is_db_ready():
            return None, "Database service is not ready. Please verify configuration.", 503

        email = str(email or "").strip().lower()

        if not cls.validate_email(email) or not password:
            return None, "Invalid email or password provided.", 400

        db = get_db()
        try:
            user = db.users.find_one({"email": email})
            if not user or not check_password_hash(user.get("password_hash", ""), password):
                return None, "Invalid email address or password.", 401

            return cls.serialize_user(user), None, 200
        except PyMongoError as err:
            return None, f"Database query error: {str(err)}", 500

    @classmethod
    def get_user_by_id(cls, user_id):
        """Retrieve user by ObjectId string."""
        if not is_db_ready() or not user_id:
            return None
        try:
            oid = ObjectId(user_id)
            db = get_db()
            user = db.users.find_one({"_id": oid})
            return cls.serialize_user(user) if user else None
        except Exception:
            return None
