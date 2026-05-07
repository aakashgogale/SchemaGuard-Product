"""AI Agent routes backed by a configured LLM provider."""

import os
from flask import Blueprint, abort, current_app, jsonify, request
from pydantic import ValidationError

from app.middleware.auth_guard import jwt_required_custom
from app.schemas.agent_schema import AgentChatRequest, AgentChatResponse
from app.schemas.errors import format_validation_errors
from app.services.agent_service import (
    build_system_prompt,
    build_user_agent_context,
    generate_local_agent_reply,
)

agent_bp = Blueprint("agent", __name__, url_prefix="/api/agent")
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


def _gemini_contents(history, message: str) -> list[dict]:
    """Convert chat history to Gemini content parts."""
    contents = []
    for item in history[-20:]:
        role = "model" if item.role == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": item.content}]})
    contents.append({"role": "user", "parts": [{"text": message}]})
    return contents


def _extract_gemini_reply(payload: dict) -> str:
    """Extract text from a Gemini generateContent response."""
    candidates = payload.get("candidates") or []
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(part.get("text", "") for part in parts).strip()


def _call_gemini(api_key: str, system_prompt: str, data: AgentChatRequest) -> str:
    """Call Gemini generateContent and return assistant text."""
    import requests

    model = current_app.config.get("AGENT_MODEL", "gemini-2.5-flash")
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model}:generateContent"
    )
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": _gemini_contents(data.conversation_history, data.message),
        "generationConfig": {
            "maxOutputTokens": current_app.config.get("AGENT_MAX_TOKENS", 500),
            "temperature": 0.2,
        },
    }
    response = requests.post(
        endpoint,
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    return _extract_gemini_reply(response.json())


def _call_anthropic(api_key: str, system_prompt: str, data: AgentChatRequest) -> str:
    """Call Anthropic Claude and return assistant text."""
    from anthropic import Anthropic

    messages = [
        {"role": item.role, "content": item.content}
        for item in data.conversation_history[-20:]
    ]
    messages.append({"role": "user", "content": data.message})
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022"),
        max_tokens=current_app.config.get("AGENT_MAX_TOKENS"),
        system=system_prompt,
        messages=messages,
    )
    return "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    ).strip()


@agent_bp.route("/chat", methods=["POST"])
@jwt_required_custom
def chat(current_user):
    """Answer a user question with SchemaGuard context."""
    try:
        data = AgentChatRequest.model_validate(request.get_json())
    except ValidationError as error:
        abort(422, description=format_validation_errors(error))

    provider = (current_app.config.get("AGENT_PROVIDER") or "gemini").lower()
    gemini_key = current_app.config.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    anthropic_key = current_app.config.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    api_key = gemini_key if provider == "gemini" else anthropic_key

    context, _stats = build_user_agent_context(current_user)
    system_prompt = build_system_prompt(context)

    if not api_key:
        reply = generate_local_agent_reply(current_user, data.message)
        result = AgentChatResponse(reply=reply, used_context=True)
        return jsonify(result.model_dump()), 200

    try:
        if provider == "gemini":
            reply = _call_gemini(api_key, system_prompt, data)
        else:
            reply = _call_anthropic(api_key, system_prompt, data)
    except Exception:
        current_app.logger.exception("AI Agent provider request failed")
        return jsonify({"error": "bad_gateway", "message": "AI service temporarily unavailable"}), 502

    result = AgentChatResponse(reply=reply, used_context=True)
    return jsonify(result.model_dump()), 200


@dashboard_bp.route("/stats", methods=["GET"])
@jwt_required_custom
def dashboard_stats(current_user):
    """Return quick user stats for the AI Agent context panel."""
    _context, stats = build_user_agent_context(current_user)
    return jsonify(stats), 200
