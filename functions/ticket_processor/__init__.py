"""Azure Function Service Bus trigger — processes queued IT tickets."""
import json
import asyncio
import logging

try:
    import azure.functions as func
    HAS_AZURE_FUNCTIONS = True
except ImportError:
    HAS_AZURE_FUNCTIONS = False
    func = None


async def _process(user_info: dict) -> dict:
    """Core ticket processing logic."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from shared.triage import triage_ticket
    from shared.auto_resolve import AutoResolver
    from shared.jira_client import JiraClient
    from shared.teams_client import TeamsClient
    from shared.models import Priority

    triage = await triage_ticket(user_info.get("message_text", ""))
    resolver, jira, teams = AutoResolver(), JiraClient(), TeamsClient()
    user_email = user_info.get("user_email", "unknown@contoso.com")

    if triage.can_automate:
        resolution = await resolver.dispatch(triage, {"email": user_email, "message_text": user_info.get("message_text", "")})
        await teams.send_resolution_notification(user_email, resolution.message)
        return {"action": "auto_resolved", "category": triage.category.value}
    else:
        ticket = await jira.create_ticket(
            summary=triage.jira_summary,
            description=f"User: {user_email}\nCategory: {triage.category.value}\n\n{user_info.get('message_text', '')}",
            priority=triage.priority,
            category=triage.category.value,
            reporter=user_email,
        )
        await teams.send_ticket_notification(user_email, ticket.ticket_id, ticket.url, ticket.priority)
        return {"action": "jira_created", "ticket_id": ticket.ticket_id}


def main(msg=None):
    """Azure Function entry point."""
    if HAS_AZURE_FUNCTIONS and msg is not None:
        user_info = json.loads(msg.get_body().decode("utf-8"))
    else:
        user_info = msg or {}
    result = asyncio.get_event_loop().run_until_complete(_process(user_info))
    logging.info(f"Ticket processed: {result}")
    return result
