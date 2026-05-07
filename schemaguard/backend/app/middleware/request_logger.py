"""Request logging middleware — logs every request with timing and request_id."""

import uuid
import time
import logging
import json
from datetime import datetime, timezone

from flask import Flask, abort, g, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app import db
from app.models.user import User

logger = logging.getLogger("schemaguard.request")


class RequestLogFormatter(logging.Formatter):
    """JSON formatter for structured request logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_data"):
            log_data.update(record.request_data)
        return json.dumps(log_data)


def register_request_logger(app: Flask) -> None:
    """Register before_request and after_request hooks for logging."""
    handler = logging.StreamHandler()
    handler.setFormatter(RequestLogFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    @app.before_request
    def log_request_start() -> None:
        """Log incoming request and store timing context."""
        g.request_id = str(uuid.uuid4())
        g.start_time = time.time()
        logger.info(
            "Request started",
            extra={
                "request_data": {
                    "request_id": g.request_id,
                    "method": request.method,
                    "path": request.path,
                }
            },
        )
        if request.method == "OPTIONS" or not request.headers.get("Authorization"):
            return
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except Exception:
            return
        if not user_id:
            return
        user = db.session.get(User, user_id)
        if not user:
            return
        if not user.is_active:
            abort(403, description="Account suspended")
        user.last_active_at = datetime.now(timezone.utc)
        db.session.commit()

    @app.after_request
    def log_request_end(response):
        """Log completed request with duration and status."""
        duration_ms = round((time.time() - g.get("start_time", time.time())) * 1000)
        logger.info(
            "Request completed",
            extra={
                "request_data": {
                    "request_id": g.get("request_id", "unknown"),
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                }
            },
        )
        response.headers["X-Request-ID"] = g.get("request_id", "unknown")
        return response
