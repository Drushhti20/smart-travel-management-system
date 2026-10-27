"""Trip Management Service for Beyond Horizons. Handles all CRUD logic and validation."""
from datetime import date, datetime, timezone
from bson import ObjectId
from pymongo.errors import PyMongoError
from ..database import get_db, is_db_ready


class TripService:
    """Service handling Trip CRUD operations and user data isolation."""

    @staticmethod
    def parse_date(date_str):
        """
        Parse date string to a date object.
        Supports standard YYYY-MM-DD as well as ISO timestamps (e.g. from MongoDB/API).
        """
        if not date_str:
            return None
        if isinstance(date_str, date) and not isinstance(date_str, datetime):
            return date_str
        if isinstance(date_str, datetime):
            return date_str.date()

        clean = str(date_str).strip()
        if "T" in clean:
            clean = clean.split("T")[0]
        elif " " in clean:
            clean = clean.split(" ")[0]

        try:
            return datetime.strptime(clean, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    @classmethod
    def serialize_trip(cls, trip_doc):
        """Format trip document for JSON response."""
        if not trip_doc:
            return None

        start_date_raw = trip_doc.get("start_date")
        end_date_raw = trip_doc.get("end_date")

        start_d = cls.parse_date(start_date_raw)
        end_d = cls.parse_date(end_date_raw)
        today = date.today()

        # Clean normalized YYYY-MM-DD strings for frontend input compatibility
        start_str = start_d.isoformat() if start_d else str(start_date_raw or "").split("T")[0]
        end_str = end_d.isoformat() if end_d else str(end_date_raw or "").split("T")[0]

        duration_days = (end_d - start_d).days + 1 if (start_d and end_d and end_d >= start_d) else 1

        # Determine trip status
        status = "Planned"
        if start_d and end_d:
            if end_d < today:
                status = "Completed"
            elif start_d <= today <= end_d:
                status = "Ongoing"
            else:
                status = "Upcoming"

        budget_val = float(trip_doc.get("budget", 0))
        travelers_val = trip_doc.get("travelers") if "travelers" in trip_doc else trip_doc.get("travellers", 1)

        return {
            "id": str(trip_doc["_id"]),
            "user_id": str(trip_doc.get("user_id", "")),
            "title": trip_doc.get("title", ""),
            "destination": trip_doc.get("destination", ""),
            "start_date": start_str,
            "end_date": end_str,
            "budget": budget_val,
            "travelers": int(travelers_val or 1),
            "notes": trip_doc.get("notes", ""),
            "duration_days": duration_days,
            "status": status,
            "created_at": trip_doc.get("created_at", "").isoformat() if isinstance(trip_doc.get("created_at"), datetime) else str(trip_doc.get("created_at", "")),
            "updated_at": trip_doc.get("updated_at", "").isoformat() if isinstance(trip_doc.get("updated_at"), datetime) else str(trip_doc.get("updated_at", ""))
        }

    @classmethod
    def validate_trip_data(cls, data):
        """Validate input dictionary for creating or updating a trip."""
        title = str(data.get("title", "")).strip()
        destination = str(data.get("destination", "")).strip()
        start_date_str = str(data.get("start_date") or data.get("startDate") or "").strip()
        end_date_str = str(data.get("end_date") or data.get("endDate") or "").strip()
        budget_raw = data.get("budget", 0)
        travelers_raw = data.get("travelers") if "travelers" in data else data.get("travellers", 1)
        notes = str(data.get("notes", "")).strip()

        if not title or len(title) < 2 or len(title) > 120:
            return None, "Trip title must be between 2 and 120 characters."

        if not destination or len(destination) < 2 or len(destination) > 120:
            return None, "Destination must be between 2 and 120 characters."

        start_d = cls.parse_date(start_date_str)
        if not start_d:
            return None, "Please provide a valid start date (YYYY-MM-DD)."

        end_d = cls.parse_date(end_date_str)
        if not end_d:
            return None, "Please provide a valid end date (YYYY-MM-DD)."

        if end_d < start_d:
            return None, "End date cannot be earlier than start date."

        try:
            budget = float(budget_raw)
            if budget < 0:
                return None, "Budget cannot be negative."
        except (ValueError, TypeError):
            return None, "Budget must be a valid number."

        try:
            travelers = int(travelers_raw)
            if travelers < 1:
                return None, "Traveler count must be at least 1."
        except (ValueError, TypeError):
            return None, "Travelers must be a valid whole number."

        if len(notes) > 2000:
            return None, "Notes must not exceed 2000 characters."

        validated = {
            "title": title,
            "destination": destination,
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "budget": round(budget, 2),
            "travelers": travelers,
            "notes": notes,
        }
        return validated, None

    @classmethod
    def _build_user_filter(cls, user_id):
        """Construct user_id query supporting both ObjectId and string storage representations."""
        filters = []
        if ObjectId.is_valid(user_id):
            filters.append(ObjectId(user_id))
        filters.append(str(user_id))
        return {"$in": filters}

    @classmethod
    def create_trip(cls, user_id, trip_data):
        """Create and persist a new trip for a specific user."""
        if not is_db_ready():
            return None, "Database service is not ready.", 503

        if not user_id:
            return None, "Authentication required.", 401

        validated, err = cls.validate_trip_data(trip_data)
        if err:
            return None, err, 400

        db = get_db()
        try:
            now = datetime.now(timezone.utc)
            doc = {
                "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id,
                "title": validated["title"],
                "destination": validated["destination"],
                "start_date": validated["start_date"],
                "end_date": validated["end_date"],
                "budget": validated["budget"],
                "travelers": validated["travelers"],
                "notes": validated["notes"],
                "created_at": now,
                "updated_at": now,
            }
            result = db.trips.insert_one(doc)
            doc["_id"] = result.inserted_id
            return cls.serialize_trip(doc), None, 201
        except PyMongoError as pe:
            return None, f"Database error creating trip: {str(pe)}", 500

    @classmethod
    def get_user_trips(cls, user_id):
        """Retrieve all trips owned by a specific user."""
        if not is_db_ready():
            return None, "Database service is not ready.", 503

        if not user_id:
            return None, "Authentication required.", 401

        db = get_db()
        try:
            user_filter = cls._build_user_filter(user_id)
            cursor = db.trips.find({"user_id": user_filter}).sort("start_date", 1)
            trips = [cls.serialize_trip(item) for item in cursor]
            return trips, None, 200
        except PyMongoError as pe:
            return None, f"Database error retrieving trips: {str(pe)}", 500

    @classmethod
    def get_trip_by_id(cls, trip_id, user_id):
        """Retrieve a single trip owned by the user."""
        if not is_db_ready():
            return None, "Database service is not ready.", 503

        if not user_id:
            return None, "Authentication required.", 401

        if not trip_id or not ObjectId.is_valid(trip_id):
            return None, "Invalid trip ID.", 400

        db = get_db()
        try:
            user_filter = cls._build_user_filter(user_id)
            trip = db.trips.find_one({"_id": ObjectId(trip_id), "user_id": user_filter})
            if not trip:
                return None, "Trip not found or access denied.", 404

            return cls.serialize_trip(trip), None, 200
        except PyMongoError as pe:
            return None, f"Database error: {str(pe)}", 500

    @classmethod
    def update_trip(cls, trip_id, user_id, trip_data):
        """Update an existing trip owned by the user."""
        if not is_db_ready():
            return None, "Database service is not ready.", 503

        if not user_id:
            return None, "Authentication required.", 401

        if not trip_id or not ObjectId.is_valid(trip_id):
            return None, "Invalid trip ID.", 400

        validated, err = cls.validate_trip_data(trip_data)
        if err:
            return None, err, 400

        db = get_db()
        try:
            user_filter = cls._build_user_filter(user_id)
            existing = db.trips.find_one({"_id": ObjectId(trip_id), "user_id": user_filter})
            if not existing:
                return None, "Trip not found or unauthorized.", 404

            now = datetime.now(timezone.utc)
            update_payload = {
                "title": validated["title"],
                "destination": validated["destination"],
                "start_date": validated["start_date"],
                "end_date": validated["end_date"],
                "budget": validated["budget"],
                "travelers": validated["travelers"],
                "notes": validated["notes"],
                "updated_at": now
            }

            db.trips.update_one(
                {"_id": ObjectId(trip_id), "user_id": user_filter},
                {"$set": update_payload}
            )

            updated = db.trips.find_one({"_id": ObjectId(trip_id)})
            return cls.serialize_trip(updated), None, 200
        except PyMongoError as pe:
            return None, f"Database error updating trip: {str(pe)}", 500

    @classmethod
    def delete_trip(cls, trip_id, user_id):
        """Delete a trip owned by the user."""
        if not is_db_ready():
            return False, "Database service is not ready.", 503

        if not user_id:
            return False, "Authentication required.", 401

        if not trip_id or not ObjectId.is_valid(trip_id):
            return False, "Invalid trip ID.", 400

        db = get_db()
        try:
            user_filter = cls._build_user_filter(user_id)
            result = db.trips.delete_one({"_id": ObjectId(trip_id), "user_id": user_filter})
            if result.deleted_count == 0:
                return False, "Trip not found or unauthorized to delete.", 404

            return True, "Trip deleted successfully.", 200
        except PyMongoError as pe:
            return False, f"Database error deleting trip: {str(pe)}", 500

    @classmethod
    def get_trip_stats(cls, user_id):
        """Compute real aggregate statistics for a user's dashboard."""
        trips, err, status = cls.get_user_trips(user_id)
        if err:
            return None, err, status

        total_trips = len(trips)
        total_budget = sum(t.get("budget", 0) for t in trips)
        unique_destinations = len(set(t["destination"].strip().lower() for t in trips if t.get("destination")))

        upcoming_count = sum(1 for t in trips if t.get("status") == "Upcoming")
        ongoing_count = sum(1 for t in trips if t.get("status") == "Ongoing")
        completed_count = sum(1 for t in trips if t.get("status") == "Completed")

        # Find next upcoming or ongoing trip
        active_trips = [t for t in trips if t.get("status") in ("Upcoming", "Ongoing")]
        next_trip = active_trips[0] if active_trips else None

        stats = {
            "total_trips": total_trips,
            "upcoming_trips": upcoming_count,
            "ongoing_trips": ongoing_count,
            "completed_trips": completed_count,
            "total_budget": round(total_budget, 2),
            "unique_destinations": unique_destinations,
            "next_trip": next_trip
        }
        return stats, None, 200
