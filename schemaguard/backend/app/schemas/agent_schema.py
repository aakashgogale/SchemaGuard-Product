"""Pydantic schemas for the SchemaGuard AI Agent."""

from pydantic import BaseModel, Field, field_validator


class AgentHistoryMessage(BaseModel):
    """A previous chat message sent to the AI Agent."""

    role: str
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("role")
    @classmethod
    def valid_role(cls, value: str) -> str:
        """Validate that history roles match Claude chat roles."""
        if value not in {"user", "assistant"}:
            raise ValueError("role must be user or assistant")
        return value


class AgentChatRequest(BaseModel):
    """Request body for AI Agent chat."""

    message: str = Field(min_length=1, max_length=1000)
    conversation_history: list[AgentHistoryMessage] = Field(default_factory=list, max_length=20)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        """Trim whitespace and reject empty messages."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("message is required")
        return stripped


class AgentChatResponse(BaseModel):
    """Response body for AI Agent chat."""

    reply: str
    used_context: bool
