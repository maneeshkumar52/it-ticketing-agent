import json
import structlog
from shared.config import get_settings
from shared.models import TicketTriage, TicketCategory, Priority

logger = structlog.get_logger(__name__)

TRIAGE_PROMPT = """You are an IT support triage specialist. Classify incoming IT support tickets.

CATEGORIES:
- PASSWORD_RESET: Unable to login, forgotten password, account locked
- VPN_ACCESS: Cannot connect to VPN, VPN credentials issues, remote access
- SOFTWARE_INSTALL: Request to install software, app not working after install
- HARDWARE_ISSUE: Broken hardware, laptop/keyboard/monitor not working
- NETWORK_ISSUE: No internet, slow connection, WiFi problems
- EMAIL_ISSUE: Cannot send/receive email, Outlook not working
- PRINTER_ISSUE: Cannot print, printer offline, paper jam
- OTHER: Anything else

PRIORITY:
- CRITICAL: Entire team/system down, security breach
- HIGH: Single user completely unable to work
- MEDIUM: User can partially work, significant disruption
- LOW: Minor inconvenience, workaround available

AUTO-RESOLVABLE (can_automate=true): PASSWORD_RESET, VPN_ACCESS, SOFTWARE_INSTALL (standard only)
NOT auto-resolvable: HARDWARE_ISSUE, NETWORK_ISSUE, OTHER

Respond ONLY with valid JSON:
{
  "category": "<CATEGORY>",
  "priority": "<PRIORITY>",
  "can_automate": <true/false>,
  "automation_action": "<action or null>",
  "jira_summary": "<concise JIRA title>",
  "confidence": <0.0-1.0>,
  "reasoning": "<brief explanation>"
}"""


async def triage_ticket(ticket_text: str) -> TicketTriage:
    """Classify an IT support ticket using GPT-4o structured output."""
    settings = get_settings()
    logger.info("ticket_triage_started", preview=ticket_text[:80])

    try:
        from openai import AsyncAzureOpenAI
        client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            max_retries=3,
        )
        response = await client.chat.completions.create(
            model=settings.azure_openai_deployment,
            messages=[
                {"role": "system", "content": TRIAGE_PROMPT},
                {"role": "user", "content": f"IT Ticket: {ticket_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=400,
        )
        parsed = json.loads(response.choices[0].message.content)
        result = TicketTriage(
            category=TicketCategory(parsed["category"]),
            priority=Priority(parsed["priority"]),
            can_automate=parsed["can_automate"],
            automation_action=parsed.get("automation_action"),
            jira_summary=parsed.get("jira_summary", ticket_text[:80]),
            confidence=float(parsed.get("confidence", 0.8)),
            reasoning=parsed.get("reasoning", ""),
        )
        logger.info("triage_complete", category=result.category.value, can_automate=result.can_automate)
        return result
    except Exception as exc:
        logger.error("triage_failed", error=str(exc))
        return TicketTriage(
            category=TicketCategory.OTHER,
            priority=Priority.MEDIUM,
            can_automate=False,
            jira_summary=ticket_text[:80],
            confidence=0.5,
            reasoning=f"Triage failed: {str(exc)}",
        )
