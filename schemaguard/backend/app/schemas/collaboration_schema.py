"""Pydantic schemas for collaboration and notifications."""

from datetime import datetime

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class AddMemberRequest(BaseModel):
    """Request schema for adding a Team A member."""

    email: EmailStr


class UpdateMemberRoleRequest(BaseModel):
    """Request schema for changing a member role."""

    role: Literal["CO_LEAD", "MEMBER"]


class MemberResponse(BaseModel):
    """Response schema for a Team A member."""

    id: str
    email: str
    role: str
    added_at: datetime


class MemberListResponse(BaseModel):
    """Response schema for member lists."""

    members: list[MemberResponse]
    total: int


class AddSubscriberRequest(BaseModel):
    """Request schema for adding a Team B subscriber."""

    email: EmailStr
    webhook_url: HttpUrl | None = Field(default=None, max_length=500)
    notify_breaking_only: bool = True
    team_name: str | None = Field(default=None, max_length=100)


class SubscriberResponse(BaseModel):
    """Response schema for a Team B subscriber."""

    id: str
    email: str
    team_name: str | None
    is_lead: bool
    webhook_url: str | None
    notify_breaking_only: bool
    subscribed_at: datetime


class SubscriberListResponse(BaseModel):
    """Response schema for subscriber lists."""

    subscribers: list[SubscriberResponse]
    total: int


class PublicDiffResponse(BaseModel):
    """Response schema for public diff links."""

    registry_name: str
    version: str
    diff_result: dict | None
    change_reason: str | None
    uploaded_at: datetime


class SendMessageRequest(BaseModel):
    """Request schema for Team A and Team B messages."""

    content: str = Field(min_length=1, max_length=2000)


class PublicSendMessageRequest(SendMessageRequest):
    """Public message request from a Team B lead."""

    email: EmailStr


class MessageResponse(BaseModel):
    """Response schema for registry messages."""

    id: str
    sender_type: str
    sender_email: str
    content: str
    sent_at: datetime
    is_read: bool


class PublicConversationResponse(BaseModel):
    """Public Team B conversation payload."""

    registry_name: str
    messages: list[MessageResponse]
