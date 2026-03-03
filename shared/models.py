from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class TicketCategory(str, Enum):
    PASSWORD_RESET = "PASSWORD_RESET"
    VPN_ACCESS = "VPN_ACCESS"
    SOFTWARE_INSTALL = "SOFTWARE_INSTALL"
    HARDWARE_ISSUE = "HARDWARE_ISSUE"
    NETWORK_ISSUE = "NETWORK_ISSUE"
    EMAIL_ISSUE = "EMAIL_ISSUE"
    PRINTER_ISSUE = "PRINTER_ISSUE"
    OTHER = "OTHER"

class Priority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class TicketTriage(BaseModel):
    category: TicketCategory
    priority: Priority
    can_automate: bool
    automation_action: Optional[str] = None
    jira_summary: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    reasoning: str = ""

class ResolutionResult(BaseModel):
    success: bool
    action_taken: str
    message: str
    details: dict = Field(default_factory=dict)

class JiraTicket(BaseModel):
    ticket_id: str
    url: str
    summary: str
    priority: str
    category: str
    status: str = "Open"
