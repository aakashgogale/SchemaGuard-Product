"""Service layer for API collaboration, messages, and public access."""

from datetime import datetime, timedelta, timezone

from app import db
from app.models.collaboration import (
    ActivityLog,
    APIMember,
    APISubscriber,
    MemberRole,
    RegistryMessage,
    SenderType,
)
from app.models.registry import APIRegistry
from app.models.version import SchemaVersion
from app.models.user import User
from app.schemas.collaboration_schema import (
    AddMemberRequest,
    AddSubscriberRequest,
    MemberListResponse,
    MemberResponse,
    MessageResponse,
    PublicConversationResponse,
    PublicDiffResponse,
    PublicSendMessageRequest,
    SendMessageRequest,
    SubscriberListResponse,
    SubscriberResponse,
    UpdateMemberRoleRequest,
)
from app.services.activity_service import activity_response


class DuplicateMemberError(Exception):
    """Raised when a member already exists for a registry."""


class DuplicateSubscriberError(Exception):
    """Raised when a subscriber already exists for a registry."""


class MemberNotFoundError(Exception):
    """Raised when a member does not exist."""


class SubscriberNotFoundError(Exception):
    """Raised when a subscriber does not exist."""


class PublicDiffNotFoundError(Exception):
    """Raised when a public diff token has no matching registry."""


class ForbiddenRegistryAccessError(Exception):
    """Raised when a user lacks a registry role."""


def get_member_role(registry_id: str, user_id: str) -> str | None:
    """Return the user's effective role for a registry."""
    registry = db.session.get(APIRegistry, registry_id)
    user = db.session.get(User, user_id)
    if registry is None or user is None:
        return None
    if registry.owner_id == user.id:
        return "OWNER"
    member = APIMember.query.filter_by(
        registry_id=registry.id,
        email=user.email,
    ).first()
    return member.role.value if member else None


def require_registry_role(registry: APIRegistry, user: User, allowed: set[str]) -> str:
    """Require a registry role and return it."""
    role = get_member_role(registry.id, user.id)
    if role not in allowed:
        raise ForbiddenRegistryAccessError("Access denied")
    return role


def list_members(registry: APIRegistry) -> MemberListResponse:
    """List Team A members for a registry."""
    members = [_member_response(member) for member in registry.members]
    return MemberListResponse(members=members, total=len(members))


def add_member(registry: APIRegistry, user: User, data: AddMemberRequest) -> MemberResponse:
    """Add a Team A member to a registry."""
    existing = APIMember.query.filter_by(registry_id=registry.id, email=data.email).first()
    if existing:
        raise DuplicateMemberError("Member already exists")

    member = APIMember(registry_id=registry.id, email=data.email, added_by=user.id)
    db.session.add(member)
    db.session.commit()
    return _member_response(member)


def remove_member(registry: APIRegistry, member_id: str) -> None:
    """Remove a Team A member from a registry."""
    member = db.session.get(APIMember, member_id)
    if member is None or member.registry_id != registry.id:
        raise MemberNotFoundError("Member not found")
    db.session.delete(member)
    db.session.commit()


def update_member_role(registry: APIRegistry, member_id: str, data: UpdateMemberRoleRequest) -> MemberResponse:
    """Change a member role."""
    member = db.session.get(APIMember, member_id)
    if member is None or member.registry_id != registry.id:
        raise MemberNotFoundError("Member not found")
    member.role = MemberRole(data.role)
    db.session.commit()
    return _member_response(member)


def list_subscribers(registry: APIRegistry) -> SubscriberListResponse:
    """List Team B subscribers for a registry."""
    subscribers = [_subscriber_response(item) for item in registry.subscribers]
    return SubscriberListResponse(subscribers=subscribers, total=len(subscribers))


def add_subscriber(
    registry: APIRegistry, data: AddSubscriberRequest
) -> SubscriberResponse:
    """Add a Team B subscriber to a registry."""
    existing = APISubscriber.query.filter_by(
        registry_id=registry.id, email=data.email
    ).first()
    if existing:
        raise DuplicateSubscriberError("Subscriber already exists")

    subscriber = APISubscriber(
        registry_id=registry.id,
        email=data.email,
        team_name=data.team_name,
        webhook_url=str(data.webhook_url) if data.webhook_url else None,
        notify_breaking_only=data.notify_breaking_only,
    )
    db.session.add(subscriber)
    db.session.commit()
    return _subscriber_response(subscriber)


def remove_subscriber(registry: APIRegistry, subscriber_id: str) -> None:
    """Remove a Team B subscriber from a registry."""
    subscriber = db.session.get(APISubscriber, subscriber_id)
    if subscriber is None or subscriber.registry_id != registry.id:
        raise SubscriberNotFoundError("Subscriber not found")
    db.session.delete(subscriber)
    db.session.commit()


def make_subscriber_lead(registry: APIRegistry, subscriber_id: str) -> SubscriberResponse:
    """Mark one subscriber as the Team B lead for a registry."""
    subscriber = db.session.get(APISubscriber, subscriber_id)
    if subscriber is None or subscriber.registry_id != registry.id:
        raise SubscriberNotFoundError("Subscriber not found")
    APISubscriber.query.filter_by(registry_id=registry.id).update({"is_lead": False})
    subscriber.is_lead = True
    db.session.commit()
    return _subscriber_response(subscriber)


def get_public_diff(public_token: str) -> PublicDiffResponse:
    """Return the latest diff for a public registry token."""
    registry = APIRegistry.query.filter_by(public_token=public_token).first()
    if registry is None:
        raise PublicDiffNotFoundError("Public diff not found")

    latest = registry.versions[0] if registry.versions else None
    if latest is None:
        raise PublicDiffNotFoundError("Public diff not found")

    return PublicDiffResponse(
        registry_name=registry.name,
        version=latest.version,
        diff_result=latest.diff_result,
        change_reason=latest.change_reason,
        uploaded_at=latest.uploaded_at,
    )


def team_activity(registry: APIRegistry) -> dict:
    """Return member activity and recent registry actions."""
    owner = registry.owner
    rows = [
        _team_member_activity(
            email=owner.email,
            role="OWNER",
            user=owner,
            registry=registry,
            joined_at=registry.created_at,
        )
    ]
    for member in registry.members:
        user = User.query.filter_by(email=member.email).first()
        rows.append(
            _team_member_activity(
                email=member.email,
                role=member.role.value,
                user=user,
                registry=registry,
                joined_at=member.added_at,
            )
        )
    logs = (
        ActivityLog.query.filter_by(registry_id=registry.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(10)
        .all()
    )
    return {"members": rows, "activity": [activity_response(item) for item in logs]}


def list_activity(registry: APIRegistry) -> list[dict]:
    """Return last 20 activity log entries for a registry."""
    entries = (
        ActivityLog.query.filter_by(registry_id=registry.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(20)
        .all()
    )
    return [activity_response(entry) for entry in entries]


def list_messages(registry: APIRegistry, mark_team_b_read: bool = False) -> list[MessageResponse]:
    """List registry messages chronologically."""
    messages = (
        RegistryMessage.query.filter_by(registry_id=registry.id)
        .order_by(RegistryMessage.sent_at.asc())
        .all()
    )
    if mark_team_b_read:
        for message in messages:
            if message.sender_type == SenderType.TEAM_B and not message.is_read:
                message.is_read = True
        db.session.commit()
    return [_message_response(message) for message in messages]


def send_team_a_message(registry: APIRegistry, user: User, data: SendMessageRequest) -> MessageResponse:
    """Create a Team A message."""
    message = RegistryMessage(
        registry_id=registry.id,
        sender_type=SenderType.TEAM_A,
        sender_email=user.email,
        content=data.content,
        is_read=False,
    )
    db.session.add(message)
    db.session.commit()
    return _message_response(message)


def public_conversation(public_token: str) -> PublicConversationResponse:
    """Return a public conversation by registry token."""
    registry = APIRegistry.query.filter_by(public_token=public_token).first()
    if registry is None:
        raise PublicDiffNotFoundError("Conversation not found")
    return PublicConversationResponse(
        registry_name=registry.name,
        messages=list_messages(registry),
    )


def send_team_b_message(public_token: str, data: PublicSendMessageRequest) -> MessageResponse:
    """Create a Team B lead message after validating lead email."""
    registry = APIRegistry.query.filter_by(public_token=public_token).first()
    if registry is None:
        raise PublicDiffNotFoundError("Conversation not found")
    lead = APISubscriber.query.filter_by(
        registry_id=registry.id,
        email=data.email,
        is_lead=True,
    ).first()
    if lead is None:
        raise ForbiddenRegistryAccessError("Team lead email mismatch")
    message = RegistryMessage(
        registry_id=registry.id,
        sender_type=SenderType.TEAM_B,
        sender_email=data.email,
        content=data.content,
        is_read=False,
    )
    db.session.add(message)
    db.session.commit()
    return _message_response(message)


def _member_response(member: APIMember) -> MemberResponse:
    """Convert a member model into a response."""
    return MemberResponse(
        id=member.id,
        email=member.email,
        role=member.role.value,
        added_at=member.added_at,
    )


def _subscriber_response(subscriber: APISubscriber) -> SubscriberResponse:
    """Convert a subscriber model into a response."""
    return SubscriberResponse(
        id=subscriber.id,
        email=subscriber.email,
        team_name=subscriber.team_name,
        is_lead=subscriber.is_lead,
        webhook_url=subscriber.webhook_url,
        notify_breaking_only=subscriber.notify_breaking_only,
        subscribed_at=subscriber.subscribed_at,
    )


def _message_response(message: RegistryMessage) -> MessageResponse:
    """Convert a message model into a response."""
    return MessageResponse(
        id=message.id,
        sender_type=message.sender_type.value,
        sender_email=message.sender_email,
        content=message.content,
        sent_at=message.sent_at,
        is_read=message.is_read,
    )


def _activity_status(user: User | None) -> str:
    """Compute online status server-side."""
    if not user or not user.last_active_at:
        return "never"
    last_active = user.last_active_at
    if last_active.tzinfo is None:
        last_active = last_active.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - last_active
    if age <= timedelta(minutes=5):
        return "online"
    if age <= timedelta(hours=2):
        return "away"
    return "inactive"


def _team_member_activity(
    email: str,
    role: str,
    user: User | None,
    registry: APIRegistry,
    joined_at,
) -> dict:
    """Build one member activity row."""
    uploads = 0
    if user:
        uploads = SchemaVersion.query.filter_by(
            registry_id=registry.id,
            uploaded_by_id=user.id,
        ).count()
    return {
        "email": email,
        "role": role,
        "activity_status": _activity_status(user),
        "last_active_at": user.last_active_at.isoformat() if user and user.last_active_at else None,
        "last_login_at": user.last_login_at.isoformat() if user and user.last_login_at else None,
        "total_uploads_for_this_registry": uploads,
        "joined_at": joined_at.isoformat() if joined_at else None,
    }
