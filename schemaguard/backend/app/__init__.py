"""Flask application factory module."""

import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS

from config import config_by_name

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}, r"/public/*": {"origins": "*"}})

    if config_name != "testing":
        migrate.init_app(app, db)

    # Configure logging
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"), logging.INFO)
    logging.basicConfig(level=log_level)

    # Register middleware
    from app.middleware.request_logger import register_request_logger
    from app.middleware.error_handler import register_error_handlers

    register_request_logger(app)
    register_error_handlers(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.registry import registry_bp
    from app.routes.versions import versions_bp
    from app.routes.diff import diff_bp
    from app.routes.health import health_bp
    from app.routes.profile import profile_bp
    from app.routes.collaboration import collaboration_bp, public_bp
    from app.routes.agent import agent_bp, dashboard_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(registry_bp)
    app.register_blueprint(versions_bp)
    app.register_blueprint(diff_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(collaboration_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)

    # Create tables for testing
    if config_name == "testing":
        with app.app_context():
            from app.models import user, registry, version, collaboration  # noqa: F401

            db.create_all()

    return app
