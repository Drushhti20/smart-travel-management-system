"""Routes package for Beyond Horizons."""
from .auth_routes import auth_bp
from .trip_routes import trip_bp

__all__ = ["auth_bp", "trip_bp"]
