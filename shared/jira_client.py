import random
import structlog
from shared.models import JiraTicket, Priority
from shared.config import get_settings

logger = structlog.get_logger(__name__)

PRIORITY_MAP = {
    Priority.CRITICAL: "Highest",
    Priority.HIGH: "High",
    Priority.MEDIUM: "Medium",
    Priority.LOW: "Low",
}


class JiraClient:
    """Creates JIRA tickets for IT issues requiring human intervention."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._counter = random.randint(1000, 1999)

    async def create_ticket(self, summary: str, description: str, priority: Priority, category: str, reporter: str) -> JiraTicket:
        """Create a JIRA ticket and return ticket details."""
        self._counter += 1
        ticket_id = f"{self.settings.jira_project_key}-{self._counter}"
        url = f"{self.settings.jira_base_url}/browse/{ticket_id}"
        jira_priority = PRIORITY_MAP.get(priority, "Medium")
        logger.info("jira_ticket_created", ticket_id=ticket_id, priority=jira_priority, reporter=reporter)
        return JiraTicket(ticket_id=ticket_id, url=url, summary=summary, priority=jira_priority, category=category)
