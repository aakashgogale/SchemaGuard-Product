"""Health check route — verifies service and database connectivity."""

from datetime import datetime, timezone

from flask import Blueprint, jsonify

from app import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Return service health status including database connectivity."""
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "connected"
        status_code = 200
        status = "ok"
    except Exception:
        db_status = "disconnected"
        status_code = 503
        status = "degraded"

    return jsonify({
        "status": status,
        "db": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), status_code
