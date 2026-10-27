"""Database management and connection handler for Beyond Horizons."""
import logging
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
from ..config import Config

logger = logging.getLogger("beyond_horizons.database")

_client = None
_db = None
_is_mock = False


def init_db(uri=None, db_name=None, force_mock=False):
    """
    Initialize database connection.
    Attempts MongoDB Atlas connection if URI is present.
    If no URI is present, or connection fails, or force_mock=True, falls back
    to in-memory mongomock for safe local evaluation and testing.
    """
    global _client, _db, _is_mock

    mongo_uri = uri if uri is not None else Config.MONGODB_URI
    database_name = db_name if db_name is not None else Config.DB_NAME

    if force_mock:
        try:
            import mongomock
            _client = mongomock.MongoClient()
            _db = _client[database_name]
            _is_mock = True
            logger.info("Database initialized using in-memory mock client.")
            _ensure_indexes(_db)
            return _db
        except ImportError:
            logger.warning("mongomock not installed, cannot force mock mode.")

    if mongo_uri:
        try:
            logger.info("Attempting connection to MongoDB Atlas...")
            # Short timeout so connection failure does not hang server start
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            _client = client
            _db = client[database_name]
            _is_mock = False
            logger.info("Connected successfully to MongoDB Atlas database '%s'.", database_name)
            _ensure_indexes(_db)
            return _db
        except (PyMongoError, ServerSelectionTimeoutError) as err:
            logger.warning("MongoDB Atlas connection failed: %s", err)
            logger.info("Falling back to local in-memory storage (mongomock) for evaluation.")
            try:
                import mongomock
                _client = mongomock.MongoClient()
                _db = _client[database_name]
                _is_mock = True
                _ensure_indexes(_db)
                return _db
            except ImportError:
                _client = None
                _db = None
                _is_mock = False
                logger.error("Could not initialize database and mongomock is not available.")
                return None
    else:
        logger.info("No MONGODB_URI configured. Initializing local in-memory storage (mongomock).")
        try:
            import mongomock
            _client = mongomock.MongoClient()
            _db = _client[database_name]
            _is_mock = True
            _ensure_indexes(_db)
            return _db
        except ImportError:
            _client = None
            _db = None
            _is_mock = False
            logger.warning("No database connected and mongomock not available.")
            return None


def _ensure_indexes(database):
    """Ensure database indexes are set up."""
    if database is None:
        return
    try:
        database.users.create_index("email", unique=True)
        database.trips.create_index([("user_id", 1), ("created_at", -1)])
    except Exception as err:
        logger.debug("Index creation notice: %s", err)


def get_db():
    """Retrieve the active database instance, initializing if needed."""
    global _db
    if _db is None:
        init_db()
    return _db


def get_client():
    """Retrieve active Mongo client."""
    global _client
    if _client is None:
        init_db()
    return _client


def is_using_mock_db():
    """Return True if currently operating on in-memory mock database."""
    return _is_mock


def is_db_ready():
    """Check whether database is operational."""
    global _client, _db, _is_mock
    if _db is None or _client is None:
        return False
    if _is_mock:
        return True
    try:
        _client.admin.command("ping")
        return True
    except (PyMongoError, ServerSelectionTimeoutError):
        return False


def close_db():
    """Close active database connection."""
    global _client, _db, _is_mock
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
    _client = None
    _db = None
    _is_mock = False
