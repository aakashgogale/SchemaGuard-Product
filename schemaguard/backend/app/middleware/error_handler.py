"""Global error handler middleware — consistent error response format across all endpoints."""

import logging
import traceback

from flask import Flask, jsonify, g
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

logger = logging.getLogger("schemaguard.errors")


def register_error_handlers(app: Flask) -> None:
    """Register global error handlers on the Flask app."""

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            "error": "bad_request",
            "message": str(error.description) if hasattr(error, "description") else "Bad request",
            "request_id": g.get("request_id", "unknown"),
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        return jsonify({
            "error": "unauthorized",
            "message": "Authentication required",
            "request_id": g.get("request_id", "unknown"),
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        return jsonify({
            "error": "forbidden",
            "message": "Access denied",
            "request_id": g.get("request_id", "unknown"),
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            "error": "not_found",
            "message": "Resource not found",
            "request_id": g.get("request_id", "unknown"),
        }), 404

    @app.errorhandler(409)
    def conflict(error):
        """Handle 409 Conflict errors."""
        return jsonify({
            "error": "conflict",
            "message": str(error.description) if hasattr(error, "description") else "Resource conflict",
            "request_id": g.get("request_id", "unknown"),
        }), 409

    @app.errorhandler(422)
    def validation_error(error):
        """Handle 422 Validation errors."""
        detail = error.description if hasattr(error, "description") and isinstance(error.description, list) else []
        return jsonify({
            "error": "validation_error",
            "detail": detail,
            "request_id": g.get("request_id", "unknown"),
        }), 422

    @app.errorhandler(ValidationError)
    def pydantic_validation_error(error):
        """Handle Pydantic ValidationError directly."""
        detail = []
        for err in error.errors():
            detail.append({
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
                "type": err["type"],
            })
        return jsonify({
            "error": "validation_error",
            "detail": detail,
            "request_id": g.get("request_id", "unknown"),
        }), 422

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        request_id = g.get("request_id", "unknown")
        logger.error(
            "Internal server error [request_id=%s]: %s\n%s",
            request_id,
            str(error),
            traceback.format_exc(),
        )
        return jsonify({
            "error": "internal_error",
            "message": "Something went wrong",
            "request_id": request_id,
        }), 500

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        """Catch-all for unhandled exceptions."""
        if isinstance(error, HTTPException):
            return error
        request_id = g.get("request_id", "unknown")
        logger.error(
            "Unhandled exception [request_id=%s]: %s\n%s",
            request_id,
            str(error),
            traceback.format_exc(),
        )
        return jsonify({
            "error": "internal_error",
            "message": "Something went wrong",
            "request_id": request_id,
        }), 500
