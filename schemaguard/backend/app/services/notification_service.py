"""Pure notification service for email and Slack webhook delivery."""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from html import escape
from typing import Any

logger = logging.getLogger("schemaguard.notifications")


def notify_schema_change(payload: dict[str, Any], config: dict[str, Any]) -> None:
    """Send all configured notifications for a schema upload."""
    for member in payload["members"]:
        try:
            _send_member_email(member, payload, config)
            logger.info("member_notification_sent", extra={"email": member["email"]})
        except Exception as error:
            logger.exception("member_notification_failed email=%s error=%s", member["email"], error)

    for subscriber in payload["subscribers"]:
        if subscriber["notify_breaking_only"] and not payload["is_breaking"]:
            continue
        try:
            _send_subscriber_email(subscriber, payload, config)
            logger.info("subscriber_email_sent", extra={"email": subscriber["email"]})
        except Exception as error:
            logger.exception("subscriber_email_failed email=%s error=%s", subscriber["email"], error)

        if subscriber.get("webhook_url"):
            try:
                _send_slack_webhook(subscriber["webhook_url"], payload)
                logger.info("slack_notification_sent", extra={"email": subscriber["email"]})
            except Exception as error:
                logger.exception("slack_notification_failed email=%s error=%s", subscriber["email"], error)


def notify_message(to_email: str, subject: str, content: str, link: str, config: dict[str, Any]) -> None:
    """Send one HTML message notification without raising."""
    try:
        body = f"""
        <div style="font-family:Inter,Arial,sans-serif;color:#0F172A;line-height:1.5">
          <h1>{escape(subject)}</h1>
          <p>{escape(content)}</p>
          <p><a href="{escape(link)}" style="background:#6366F1;color:#fff;padding:12px 16px;border-radius:8px;text-decoration:none;display:inline-block">Reply on SchemaGuard</a></p>
        </div>
        """
        _send_email(to_email, subject, body, config)
        logger.info("message_notification_sent email=%s", to_email)
    except Exception as error:
        logger.exception("message_notification_failed email=%s error=%s", to_email, error)


def _send_member_email(member: dict[str, Any], payload: dict[str, Any], config: dict[str, Any]) -> None:
    """Send a Team A member email."""
    status = "Breaking" if payload["is_breaking"] else "Safe"
    subject = f"{status} change in {payload['api_name']} {payload['version']}"
    body = _html_email(
        title=subject,
        intro=f"{escape(payload['uploaded_by'])} uploaded schema version {escape(payload['version'])}.",
        reason=payload.get("change_reason"),
        changes=payload["changes"],
        link=payload["dashboard_url"],
        button_text="Open Dashboard",
        warning=payload["is_breaking"],
    )
    _send_email(member["email"], subject, body, config)


def _send_subscriber_email(subscriber: dict[str, Any], payload: dict[str, Any], config: dict[str, Any]) -> None:
    """Send a Team B subscriber email."""
    subject = (
        f"BREAKING CHANGE in {payload['api_name']}"
        if payload["is_breaking"]
        else f"{payload['api_name']} updated - {payload['version']}"
    )
    changes = [change for change in payload["changes"] if change["change_type"] == "BREAKING"]
    body = _html_email(
        title=subject,
        intro="Action required before deployment." if payload["is_breaking"] else "The API contract was updated.",
        reason=payload.get("change_reason"),
        changes=changes or payload["changes"],
        link=payload["public_diff_url"],
        button_text="View Public Diff",
        warning=payload["is_breaking"],
    )
    _send_email(subscriber["email"], subject, body, config)


def _send_email(to_email: str, subject: str, html_body: str, config: dict[str, Any]) -> None:
    """Send an HTML email through SMTP when credentials are configured."""
    username = config.get("SMTP_USERNAME")
    password = config.get("SMTP_PASSWORD")
    from_email = config.get("SMTP_FROM_EMAIL") or username
    if not username or not password or not from_email:
        logger.warning("email_skipped_missing_smtp_config email=%s subject=%s", to_email, subject)
        return

    message = MIMEText(html_body, "html")
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email

    with smtplib.SMTP(config.get("SMTP_HOST", "smtp.gmail.com"), int(config.get("SMTP_PORT", 587))) as smtp:
        if config.get("SMTP_USE_TLS", True):
            smtp.starttls()
        smtp.login(username, password)
        smtp.sendmail(from_email, [to_email], message.as_string())


def _send_slack_webhook(webhook_url: str, payload: dict[str, Any]) -> None:
    """Send a Slack incoming webhook message."""
    import requests

    color = "#EF4444" if payload["is_breaking"] else "#22C55E"
    changes = payload["changes"][:5]
    change_lines = "\n".join(
        f"*{change['change_type']}* `{change['path']}` - {change['reason']}"
        for change in changes
    ) or "No changes detected."
    response = requests.post(
        webhook_url,
        json={
            "attachments": [
                {
                    "color": color,
                    "title": f"{payload['api_name']} {payload['version']} - {'BREAKING' if payload['is_breaking'] else 'SAFE'}",
                    "text": change_lines,
                    "actions": [
                        {
                            "type": "button",
                            "text": "View Diff",
                            "url": payload["public_diff_url"],
                        }
                    ],
                }
            ]
        },
        timeout=5,
    )
    response.raise_for_status()


def _html_email(
    title: str,
    intro: str,
    reason: str | None,
    changes: list[dict[str, Any]],
    link: str,
    button_text: str,
    warning: bool,
) -> str:
    """Render a compact HTML email body."""
    color = "#EF4444" if warning else "#22C55E"
    change_items = "".join(
        f"<li><strong>{escape(change['change_type'])}</strong> "
        f"<code>{escape(change['path'])}</code> - {escape(change['reason'])}</li>"
        for change in changes
    ) or "<li>No changes detected.</li>"
    reason_html = f"<p><strong>Change reason:</strong> {escape(reason)}</p>" if reason else ""
    return f"""
    <div style="font-family:Inter,Arial,sans-serif;color:#0F172A;line-height:1.5">
      <h1 style="color:{color}">{escape(title)}</h1>
      <p>{escape(intro)}</p>
      {reason_html}
      <ul>{change_items}</ul>
      <p><a href="{escape(link)}" style="background:#6366F1;color:#fff;padding:12px 16px;border-radius:8px;text-decoration:none;display:inline-block">{escape(button_text)}</a></p>
    </div>
    """
