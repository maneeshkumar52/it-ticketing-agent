import structlog
from typing import Optional, Dict
from shared.config import get_settings

logger = structlog.get_logger(__name__)


class TeamsClient:
    """Sends notifications via Microsoft Teams."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def send_message(self, channel_id: str, message: str, card_data: Optional[Dict] = None) -> bool:
        """Send message to Teams channel or user."""
        if self.settings.teams_webhook_url:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    resp = await client.post(self.settings.teams_webhook_url, json={"text": message}, timeout=10)
                    return resp.status_code == 200
            except Exception as exc:
                logger.error("teams_send_failed", error=str(exc))
                return False
        logger.info("teams_mock_message", preview=message[:100])
        return True

    async def send_resolution_notification(self, user_email: str, resolution_summary: str) -> bool:
        """Notify user of auto-resolution."""
        msg = f"✅ IT Support Update\n\nYour request has been automatically resolved.\n\nResolution: {resolution_summary}\n\nIf the issue persists, contact IT at ext. 5555."
        logger.info("resolution_notification", user=user_email)
        return await self.send_message("direct", msg)

    async def send_ticket_notification(self, user_email: str, ticket_id: str, ticket_url: str, priority: str) -> bool:
        """Notify user that a JIRA ticket has been created."""
        eta = "2 hours" if priority in ("High", "Highest") else "1 business day"
        msg = f"🎫 IT Support Ticket: {ticket_id} (Priority: {priority})\n\nTrack: {ticket_url}\nExpected response: {eta}\nUrgent? Call IT: ext. 5555"
        logger.info("ticket_notification", user=user_email, ticket=ticket_id)
        return await self.send_message("direct", msg)
