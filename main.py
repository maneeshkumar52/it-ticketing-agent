"""Standalone FastAPI app for local testing — simulates the full ticket pipeline."""
import logging, sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger(__name__)

from shared.triage import triage_ticket
from shared.auto_resolve import AutoResolver
from shared.jira_client import JiraClient
from shared.teams_client import TeamsClient

app = FastAPI(
    title="IT Ticketing Agent",
    description="Autonomous IT Support — Project 3, Chapter 20, Prompt to Production by Maneesh Kumar",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

resolver = AutoResolver()
jira = JiraClient()
teams = TeamsClient()


class TicketRequest(BaseModel):
    ticket_text: str = Field(..., min_length=5)
    user_email: str = Field(default="user@contoso.com")
    user_display_name: str = Field(default="User")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "it-ticketing-agent", "version": "1.0.0"}


@app.post("/api/v1/ticket")
async def process_ticket(request: TicketRequest) -> dict:
    """
    Process an IT support ticket.
    Auto-resolves password resets, VPN issues, and standard software installs.
    Creates JIRA tickets for hardware, network, and complex issues.
    """
    user_info = {"email": request.user_email, "message_text": request.ticket_text, "display_name": request.user_display_name}
    try:
        triage = await triage_ticket(request.ticket_text)
        result = {
            "triage": {
                "category": triage.category.value,
                "priority": triage.priority.value,
                "can_automate": triage.can_automate,
                "confidence": triage.confidence,
                "reasoning": triage.reasoning,
            },
            "user_email": request.user_email,
        }

        if triage.can_automate:
            resolution = await resolver.dispatch(triage, user_info)
            await teams.send_resolution_notification(request.user_email, resolution.message)
            result["action"] = "auto_resolved"
            result["resolution"] = {
                "success": resolution.success,
                "action_taken": resolution.action_taken,
                "message": resolution.message,
                "details": resolution.details,
            }
        else:
            ticket = await jira.create_ticket(
                summary=triage.jira_summary,
                description=f"User: {request.user_email}\nCategory: {triage.category.value}\n\nDetails:\n{request.ticket_text}",
                priority=triage.priority,
                category=triage.category.value,
                reporter=request.user_email,
            )
            await teams.send_ticket_notification(request.user_email, ticket.ticket_id, ticket.url, ticket.priority)
            result["action"] = "jira_ticket_created"
            result["ticket"] = {"ticket_id": ticket.ticket_id, "url": ticket.url, "summary": ticket.summary, "priority": ticket.priority}

        logger.info("ticket_processed", action=result["action"], category=triage.category.value)
        return result
    except Exception as exc:
        logger.error("ticket_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/v1/simulate")
async def simulate_tickets() -> dict:
    """Demo endpoint — simulate 3 different ticket types."""
    samples = [
        {"ticket_text": "I forgot my password and cannot log in to my computer", "user_email": "alice@contoso.com"},
        {"ticket_text": "My laptop screen is cracked and I cannot see anything", "user_email": "bob@contoso.com"},
        {"ticket_text": "Please install Microsoft Teams on my new laptop", "user_email": "carol@contoso.com"},
    ]
    results = []
    for s in samples:
        try:
            r = await process_ticket(TicketRequest(**s))
            results.append(r)
        except Exception as exc:
            results.append({"error": str(exc)})
    return {"count": len(results), "results": results}
