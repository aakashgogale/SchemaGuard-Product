"""Routes for API members, subscribers, and public diff links."""

import threading

from flask import Blueprint, abort, current_app, jsonify, request
from pydantic import ValidationError

from app.middleware.auth_guard import jwt_required_custom
from app.schemas.collaboration_schema import (
    AddMemberRequest,
    AddSubscriberRequest,
    PublicSendMessageRequest,
    SendMessageRequest,
    UpdateMemberRoleRequest,
)
from app.schemas.errors import format_validation_errors
from app.services.collaboration_service import (
    DuplicateMemberError,
    DuplicateSubscriberError,
    ForbiddenRegistryAccessError,
    MemberNotFoundError,
    PublicDiffNotFoundError,
    SubscriberNotFoundError,
    add_member,
    add_subscriber,
    get_public_diff,
    list_activity,
    list_members,
    list_messages,
    list_subscribers,
    make_subscriber_lead,
    public_conversation,
    remove_member,
    remove_subscriber,
    require_registry_role,
    send_team_a_message,
    send_team_b_message,
    team_activity,
    update_member_role,
)
from app.services.activity_service import log_activity
from app.services.registry_service import RegistryNotFoundError, get_registry

collaboration_bp = Blueprint("collaboration", __name__, url_prefix="/api/registries")
public_bp = Blueprint("public", __name__, url_prefix="/public")


def _registry_with_role(registry_id: str, current_user, allowed: set[str]):
    """Load a registry and enforce role-based access."""
    try:
        registry = get_registry(registry_id)
    except RegistryNotFoundError:
        abort(404)
    try:
        role = require_registry_role(registry, current_user, allowed)
    except ForbiddenRegistryAccessError:
        abort(403)
    return registry, role


def _email_config() -> dict:
    """Return SMTP/frontend config for message notifications."""
    return {
        "SMTP_HOST": current_app.config.get("SMTP_HOST"),
        "SMTP_PORT": current_app.config.get("SMTP_PORT"),
        "SMTP_USE_TLS": current_app.config.get("SMTP_USE_TLS"),
        "SMTP_USERNAME": current_app.config.get("SMTP_USERNAME"),
        "SMTP_PASSWORD": current_app.config.get("SMTP_PASSWORD"),
        "SMTP_FROM_EMAIL": current_app.config.get("SMTP_FROM_EMAIL"),
        "FRONTEND_URL": current_app.config.get("FRONTEND_URL"),
    }


@collaboration_bp.route("/<registry_id>/members", methods=["GET"])
@jwt_required_custom
def get_members(registry_id, current_user):
    """List members for a registry."""
    registry, _role = _registry_with_role(registry_id, current_user, {"OWNER", "CO_LEAD", "MEMBER"})
    return jsonify(list_members(registry).model_dump()), 200


@collaboration_bp.route("/<registry_id>/members", methods=["POST"])
@jwt_required_custom
def create_member(registry_id, current_user):
    """Add a member to a registry."""
    registry, role = _registry_with_role(registry_id, current_user, {"OWNER", "CO_LEAD"})
    try:
        data = AddMemberRequest.model_validate(request.get_json())
        response = add_member(registry, current_user, data)
    except ValidationError as error:
        abort(422, description=format_validation_errors(error))
    except DuplicateMemberError as error:
        abort(409, description=str(error))
    log_activity(registry.id, current_user.email, role, "MEMBER_ADDED", {"member_email": response.email, "role": response.role})
    return jsonify(response.model_dump()), 201


@collaboration_bp.route("/<registry_id>/members/<member_id>", methods=["DELETE"])
@jwt_required_custom
def delete_member(registry_id, member_id, current_user):
    """Remove a member from a registry."""
    registry, role = _registry_with_role(registry_id, current_user, {"OWNER", "CO_LEAD"})
    try:
        member = next((item for item in registry.members if item.id == member_id), None)
        remove_member(registry, member_id)
    except MemberNotFoundError:
        abort(404)
    log_activity(registry.id, current_user.email, role, "MEMBER_REMOVED", {"member_email": member.email if member else member_id})
    return "", 204


@collaboration_bp.route("/<registry_id>/members/<member_id>/role", methods=["PATCH"])
@jwt_required_custom
def patch_member_role(registry_id, member_id, current_user):
    """Update a Team A member role."""
    registry, role = _registry_with_role(registry_id, current_user, {"OWNER"})
    try:
        data = UpdateMemberRoleRequest.model_validate(request.get_json())
        response = update_member_role(registry, member_id, data)
    except ValidationError as error:
        abort(422, description=format_validation_errors(error))
    except (MemberNotFoundError, ValueError):
        abort(404)
    log_activity(registry.id, current_user.email, role, "ROLE_CHANGED", {"member_email": response.email, "role": response.role})
    return jsonify(response.model_dump()), 200


@collaboration_bp.route("/<registry_id>/subscribers", methods=["GET"])
@jwt_required_custom
def get_subscribers(registry_id, current_user):
    """List subscribers for a registry."""
    registry, _role = _registry_with_role(registry_id, current_user, {"OWNER", "CO_LEAD", "MEMBER"})
    return jsonify(list_subscribers(registry).model_dump()), 200


@collaboration_bp.route("/<registry_id>/subscribers", methods=["POST"])
@jwt_required_custom
def create_subscriber(registry_id, current_user):
    """Add a subscriber to a registry."""
    registry, role = _registry_with_role(registry_id, current_user, {"OWNER", "CO_LEAD"})
    try:
        data = AddSubscriberRequest.model_validate(request.get_json())
        response = add_subscriber(registry, data)
    except ValidationError as error:
        abort(422, description=format_validation_errors(error))
    except DuplicateSubscriberError as error:
        abort(409, description=str(error))
    log_activity(registry.id, current_user.email, role, "SUBSCRIBER_ADDED", {"subscriber_email": response.email})
    return jsonify(response.model_dump()), 201


@collaboration_bp.route("/<registry_id>/subscribers/<subscriber_id>", methods=["DELETE"])
@jwt_required_custom
def delete_subscriber(registry_id, subscriber_id, current_user):
    """Remove a subscriber from a registry."""
    registry, role = _registry_with_role(registry_id, current_user, {"OWNER", "CO_LEAD"})
    try:
        subscriber = next((item for item in registry.subscribers if item.id == subscriber_id), None)
        remove_subscriber(registry, subscriber_id)
    except SubscriberNotFoundError:
        abort(404)
    log_activity(registry.id, current_user.email, role, "SUBSCRIBER_REMOVED", {"subscriber_email": subscriber.email if subscriber else subscriber_id})
    return "", 204


@collaboration_bp.route("/<registry_id>/subscribers/<subscriber_id>/make-lead", methods=["PATCH"])
@jwt_required_custom
def patch_subscriber_lead(registry_id, subscriber_id, current_user):
    """Set a subscriber as Team B lead."""
    registry, role = _registry_with_role(registry_id, current_user, {"OWNER", "CO_LEAD"})
    try:
        response = make_subscriber_lead(registry, subscriber_id)
    except SubscriberNotFoundError:
        abort(404)
    log_activity(registry.id, current_user.email, role, "SUBSCRIBER_LEAD_CHANGED", {"subscriber_email": response.email})
    return jsonify(response.model_dump()), 200


@collaboration_bp.route("/<registry_id>/team-activity", methods=["GET"])
@jwt_required_custom
def get_team_activity(registry_id, current_user):
    """Return full team activity for a registry."""
    registry, _role = _registry_with_role(registry_id, current_user, {"OWNER", "CO_LEAD", "MEMBER"})
    return jsonify(team_activity(registry)), 200


@collaboration_bp.route("/<registry_id>/activity", methods=["GET"])
@jwt_required_custom
def get_activity(registry_id, current_user):
    """Return recent registry activity logs."""
    registry, _role = _registry_with_role(registry_id, current_user, {"OWNER", "CO_LEAD", "MEMBER"})
    return jsonify({"activity": list_activity(registry)}), 200


@collaboration_bp.route("/<registry_id>/messages", methods=["GET"])
@jwt_required_custom
def get_messages(registry_id, current_user):
    """List registry messages for Team A."""
    registry, _role = _registry_with_role(registry_id, current_user, {"OWNER", "CO_LEAD", "MEMBER"})
    return jsonify({"messages": [item.model_dump() for item in list_messages(registry, mark_team_b_read=True)]}), 200


@collaboration_bp.route("/<registry_id>/messages", methods=["POST"])
@jwt_required_custom
def create_message(registry_id, current_user):
    """Send a message from Team A to Team B lead."""
    registry, role = _registry_with_role(registry_id, current_user, {"OWNER", "CO_LEAD"})
    try:
        data = SendMessageRequest.model_validate(request.get_json())
        response = send_team_a_message(registry, current_user, data)
    except ValidationError as error:
        abort(422, description=format_validation_errors(error))
    lead = next((subscriber for subscriber in registry.subscribers if subscriber.is_lead), None)
    if lead:
        from app.services.notification_service import notify_message

        frontend_url = (_email_config().get("FRONTEND_URL") or "http://localhost:3001").rstrip("/")
        threading.Thread(
            target=notify_message,
            args=(
                lead.email,
                f"Message about {registry.name}",
                data.content,
                f"{frontend_url}/public/conversation/{registry.public_token}",
                _email_config(),
            ),
            daemon=True,
        ).start()
    log_activity(registry.id, current_user.email, role, "MESSAGE_SENT", {"target": "TEAM_B"})
    return jsonify(response.model_dump()), 201


@public_bp.route("/diff/<public_token>", methods=["GET"])
def public_diff(public_token):
    """Return latest diff data for a public token."""
    try:
        response = get_public_diff(public_token)
    except PublicDiffNotFoundError:
        abort(404)
    return jsonify(response.model_dump()), 200


@public_bp.route("/messages/<public_token>", methods=["GET"])
def get_public_messages(public_token):
    """Return public Team B conversation."""
    try:
        response = public_conversation(public_token)
    except PublicDiffNotFoundError:
        abort(404)
    return jsonify(response.model_dump()), 200


@public_bp.route("/messages/<public_token>", methods=["POST"])
def create_public_message(public_token):
    """Create a public Team B lead reply."""
    try:
        data = PublicSendMessageRequest.model_validate(request.get_json())
        response = send_team_b_message(public_token, data)
        registry = get_registry_by_token(public_token)
    except ValidationError as error:
        abort(422, description=format_validation_errors(error))
    except ForbiddenRegistryAccessError:
        abort(403)
    except PublicDiffNotFoundError:
        abort(404)
    if registry:
        from app.services.notification_service import notify_message

        frontend_url = (_email_config().get("FRONTEND_URL") or "http://localhost:3001").rstrip("/")
        recipients = [registry.owner.email] + [
            member.email for member in registry.members if member.role.value == "CO_LEAD"
        ]
        for email in recipients:
            threading.Thread(
                target=notify_message,
                args=(email, f"Team B replied about {registry.name}", data.content, f"{frontend_url}/api/{registry.id}", _email_config()),
                daemon=True,
            ).start()
        log_activity(registry.id, data.email, "TEAM_B", "MESSAGE_SENT", {"target": "TEAM_A"})
    return jsonify(response.model_dump()), 201


def get_registry_by_token(public_token: str):
    """Load registry for public-token helpers."""
    from app.models.registry import APIRegistry

    return APIRegistry.query.filter_by(public_token=public_token).first()
