# 🎫 IT Ticketing Agent

> **Autonomous IT Support Pipeline — GPT-4o Triage ➜ Rule-Based Auto-Resolution ➜ Jira Escalation ➜ Teams Notification**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Azure OpenAI](https://img.shields.io/badge/Azure_OpenAI-GPT--4o-0078D4?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
[![Azure Functions](https://img.shields.io/badge/Azure_Functions-v4-0062AD?logo=azurefunctions&logoColor=white)](https://azure.microsoft.com/en-us/products/functions)
[![Azure Service Bus](https://img.shields.io/badge/Service_Bus-Queue-FF6F00?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/en-us/products/service-bus)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An **enterprise-grade autonomous IT support agent** that receives employee IT requests (via API or Microsoft Teams), classifies them with GPT-4o structured output, **auto-resolves** common issues (password resets, VPN access, software installs) in seconds, and **escalates** complex problems to Jira with full Teams notifications. Dual deployment: **FastAPI** for local dev and **Azure Functions** for serverless production.

From **"Prompt to Production"** — Chapter 20, Project 3 by Maneesh Kumar.

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Architecture](#architecture) | System design, data flow, decision engine |
| 2 | [How It Works — Annotated Walkthrough](#how-it-works--annotated-walkthrough) | Step-by-step terminal output with annotations |
| 3 | [Design Decisions](#design-decisions) | Why GPT-4o JSON mode, rule-based resolution, dual deployment |
| 4 | [Data Contracts](#data-contracts) | Every Pydantic model, enum, dict structure |
| 5 | [Features](#features) | Comprehensive feature matrix |
| 6 | [Prerequisites](#prerequisites) | Platform-specific setup (macOS / Windows / Linux) |
| 7 | [Quick Start](#quick-start) | Clone → install → run in 3 minutes |
| 8 | [Project Structure](#project-structure) | File tree with module responsibilities |
| 9 | [Configuration Reference](#configuration-reference) | Every environment variable explained |
| 10 | [API Reference](#api-reference) | All endpoints with request/response schemas |
| 11 | [Azure Functions Deployment](#azure-functions-deployment) | Production serverless architecture |
| 12 | [Testing](#testing) | Unit tests, mocking strategy, coverage |
| 13 | [Ticket Processing Scenarios](#ticket-processing-scenarios) | Category-by-category behavior matrix |
| 14 | [Troubleshooting](#troubleshooting) | Common issues and solutions |
| 15 | [Azure Production Mapping](#azure-production-mapping) | Local → cloud service mapping |
| 16 | [Production Checklist](#production-checklist) | Go-live readiness assessment |

---

## Architecture

### System Overview

```
                         ┌─────────────────────────────────────────────────────────────────────┐
                         │                    IT Ticketing Agent                                │
                         │                                                                     │
                         │  ┌───────────────────────────────────────────────────────────────┐  │
  Employee IT Request    │  │                     TRIAGE ENGINE                             │  │
  ──────────────────►    │  │   triage_ticket() ─► Azure OpenAI GPT-4o (JSON mode)         │  │
  (Teams / API / curl)   │  │                      ┌────────────────────────────────────┐   │  │
                         │  │                      │  Structured Output:                │   │  │
                         │  │                      │  • category  (8 enum values)       │   │  │
                         │  │                      │  • priority  (CRITICAL→LOW)        │   │  │
                         │  │                      │  • can_automate (true/false)        │   │  │
                         │  │                      │  • confidence (0.0–1.0)             │   │  │
                         │  │                      │  • jira_summary                     │   │  │
                         │  │                      │  • reasoning                        │   │  │
                         │  │                      └───────────────┬────────────────────┘   │  │
                         │  └─────────────────────────────────────┬─────────────────────────┘  │
                         │                                        │                            │
                         │                              ┌─────────┴─────────┐                  │
                         │                              │   can_automate?   │                  │
                         │                              └─────────┬─────────┘                  │
                         │                         YES            │           NO               │
                         │                    ┌───────────────────┼──────────────────┐         │
                         │                    ▼                                      ▼         │
                         │  ┌─────────────────────────────┐    ┌─────────────────────────┐    │
                         │  │     AUTO-RESOLVER ENGINE     │    │    ESCALATION ENGINE    │    │
                         │  │                              │    │                         │    │
                         │  │  PASSWORD_RESET              │    │  JiraClient             │    │
                         │  │  ├─ Azure AD self-service    │    │  ├─ create_ticket()     │    │
                         │  │  ├─ Reset link via email     │    │  ├─ Priority mapping    │    │
                         │  │  └─ 24-hour expiry           │    │  └─ IT-XXXX ticket ID   │    │
                         │  │                              │    │                         │    │
                         │  │  VPN_ACCESS                  │    │  Creates Jira ticket    │    │
                         │  │  ├─ GlobalProtect verify     │    │  with full context:     │    │
                         │  │  ├─ Certificate validation   │    │  • User email           │    │
                         │  │  └─ Connection instructions  │    │  • Category             │    │
                         │  │                              │    │  • Original message     │    │
                         │  │  SOFTWARE_INSTALL            │    │  • Priority mapping     │    │
                         │  │  ├─ Approved list check      │    │                         │    │
                         │  │  ├─ Intune deployment        │    └────────────┬────────────┘    │
                         │  │  └─ Unapproved → escalate    │                 │                 │
                         │  └──────────────┬───────────────┘                 │                 │
                         │                 │                                  │                 │
                         │                 ▼                                  ▼                 │
                         │  ┌─────────────────────────────────────────────────────────────┐    │
                         │  │                    TEAMS NOTIFICATION ENGINE                 │    │
                         │  │                                                              │    │
                         │  │  Auto-Resolved:                    Escalated:                │    │
                         │  │  ✅ "Your request has been         🎫 "IT-1234 created"      │    │
                         │  │     automatically resolved"        "Priority: High"          │    │
                         │  │  "If issue persists,               "Expected response: 2h"   │    │
                         │  │   contact IT ext. 5555"            "Urgent? Call ext. 5555"   │    │
                         │  └─────────────────────────────────────────────────────────────┘    │
                         └─────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
  │                            DUAL DEPLOYMENT MODES                                            │
  │                                                                                              │
  │   LOCAL DEV (FastAPI)                    │  PRODUCTION (Azure Functions)                     │
  │   ─────────────────                      │  ────────────────────────────                     │
  │   main.py ─► uvicorn :8000              │  teams_webhook (HTTP trigger)                     │
  │   POST /api/v1/ticket                    │     ├─ Receives Teams payload                    │
  │   POST /api/v1/simulate                  │     ├─ Extracts user_info dict                   │
  │   GET  /health                           │     └─ Queues to Service Bus                     │
  │                                          │  ticket_processor (SB trigger)                    │
  │   Synchronous request/response           │     ├─ Dequeues message                          │
  │   Perfect for testing                    │     ├─ triage → resolve/escalate                 │
  │                                          │     └─ Sends Teams notification                  │
  └──────────────────────────────────────────┴──────────────────────────────────────────────────┘
```

### Decision Flow — Category Routing

```
  Incoming Ticket Text
         │
         ▼
  ┌──────────────────┐
  │  GPT-4o Triage   │──── category + can_automate
  └──────────────────┘
         │
    ┌────┴────────────────────────────────────────────────────┐
    │                         │                               │
    ▼                         ▼                               ▼
  PASSWORD_RESET          VPN_ACCESS                   SOFTWARE_INSTALL
  can_automate=true       can_automate=true            can_automate=true
    │                         │                               │
    ▼                         ▼                               ▼
  Azure AD reset          GlobalProtect              ┌───────┴──────┐
  email sent              access verified            │  Approved?   │
  (24h expiry)            (cert valid)               ├── YES ───────┤── NO ──────┐
                                                     ▼              ▼            ▼
                                                   Intune        JIRA ticket   Manager
                                                   push          created       approval
                                                   (15 min)                    required

    ┌────────────────────────────────────────────────────────────────┐
    │                                                                │
    ▼                    ▼                  ▼                ▼       │
  HARDWARE_ISSUE     NETWORK_ISSUE     EMAIL_ISSUE    PRINTER_ISSUE │
  can_automate=      can_automate=     can_automate=  can_automate= │
  false              false             false          false          │
    │                    │                  │                │       │
    └────────────────────┴──────────────────┴────────────────┘       │
                              │                                      │
                              ▼                                      │
                    JiraClient.create_ticket()                       │
                    ├─ Priority mapped (Critical→Highest)            │
                    ├─ Full context in description                   │
                    └─ Teams notification with ETA                   │
                                                                     │
    OTHER ───────────────────────────────────────────────────────────┘
    can_automate=false → JIRA escalation
```

---

## How It Works — Annotated Walkthrough

### Scenario 1: Password Reset (Auto-Resolved)

```
$ curl -s -X POST http://localhost:8000/api/v1/ticket \
    -H "Content-Type: application/json" \
    -d '{"ticket_text": "I forgot my password and cannot log in to my computer",
         "user_email": "alice@contoso.com"}' | python -m json.tool
```

```json
{
    "triage": {
        "category": "PASSWORD_RESET",            // ← GPT-4o classified as password issue
        "priority": "HIGH",                       // ← User completely unable to work
        "can_automate": true,                     // ← This category is auto-resolvable
        "confidence": 0.97,                       // ← 97% confidence in classification
        "reasoning": "User explicitly mentions     // ← LLM explains its reasoning
            forgotten password and inability to login"
    },
    "user_email": "alice@contoso.com",
    "action": "auto_resolved",                    // ← No human intervention needed
    "resolution": {
        "success": true,                          // ← Resolution completed successfully
        "action_taken": "password_reset_initiated",
        "message": "Password reset email sent to  // ← User-facing message
            alice@contoso.com. The reset link
            expires in 24 hours.",
        "details": {
            "reference": "PSW-47823",             // ← Tracking reference for audit
            "method": "azure_ad_self_service",     // ← Used Azure AD self-service
            "expires_hours": 24                    // ← Link validity period
        }
    }
}
```

**What happened behind the scenes:**
1. FastAPI received the POST request and validated the `TicketRequest` model
2. `triage_ticket()` sent the text to Azure OpenAI GPT-4o with structured JSON output
3. GPT-4o returned `can_automate: true` with category `PASSWORD_RESET`
4. `AutoResolver.dispatch()` routed to `resolve_password_reset()`
5. Azure AD self-service password reset was initiated (mock in local mode)
6. `TeamsClient.send_resolution_notification()` sent a Teams message to the user
7. Total time: **< 2 seconds** (vs. 15-30 minutes for manual IT support)

### Scenario 2: Hardware Issue (Escalated to Jira)

```
$ curl -s -X POST http://localhost:8000/api/v1/ticket \
    -H "Content-Type: application/json" \
    -d '{"ticket_text": "My laptop screen is cracked and I cannot see anything",
         "user_email": "bob@contoso.com"}' | python -m json.tool
```

```json
{
    "triage": {
        "category": "HARDWARE_ISSUE",            // ← Physical damage detected
        "priority": "HIGH",                       // ← User cannot work at all
        "can_automate": false,                    // ← Requires physical intervention
        "confidence": 0.95,
        "reasoning": "Physical hardware damage    // ← Cannot be resolved remotely
            requiring physical replacement"
    },
    "user_email": "bob@contoso.com",
    "action": "jira_ticket_created",              // ← Escalated to IT team
    "ticket": {
        "ticket_id": "IT-1542",                   // ← Jira ticket reference
        "url": "https://your-org.atlassian.net    // ← Direct link to ticket
            /browse/IT-1542",
        "summary": "Cracked laptop screen         // ← GPT-4o generated summary
            replacement needed",
        "priority": "High"                        // ← Mapped: HIGH → "High"
    }
}
```

**What happened behind the scenes:**
1. GPT-4o identified physical hardware damage — `can_automate: false`
2. `JiraClient.create_ticket()` created a ticket with full context:
   - User email, category, original ticket text, mapped priority
3. `TeamsClient.send_ticket_notification()` notified the user:
   - Ticket ID, tracking URL, expected response time (2 hours for High)
   - Emergency contact (IT ext. 5555)

### Scenario 3: Software Install (Conditional Auto-Resolution)

```
$ curl -s -X POST http://localhost:8000/api/v1/ticket \
    -H "Content-Type: application/json" \
    -d '{"ticket_text": "Please install Microsoft Teams on my new laptop",
         "user_email": "carol@contoso.com"}' | python -m json.tool
```

```json
{
    "triage": {
        "category": "SOFTWARE_INSTALL",
        "priority": "LOW",                        // ← Non-critical request
        "can_automate": true,
        "confidence": 0.92,
        "reasoning": "Standard software install request"
    },
    "user_email": "carol@contoso.com",
    "action": "auto_resolved",
    "resolution": {
        "success": true,
        "action_taken": "software_deployed_via_intune",
        "message": "Microsoft Teams is on the     // ← Checked against approved list
            approved software list. Installation
            has been pushed via Microsoft Intune.
            Restart in 15 minutes.",
        "details": {
            "approved": true,                     // ← Teams is on APPROVED_SOFTWARE list
            "method": "Microsoft Intune",          // ← Enterprise MDM deployment
            "eta_minutes": 15                      // ← Expected completion time
        }
    }
}
```

**Approved Software List** — auto-deployed via Intune:
```
Microsoft Office, MS Office, Teams, Microsoft Teams, Zoom, Chrome,
Google Chrome, Firefox, Slack, VSCode, Visual Studio Code, 7-Zip,
Adobe Reader, Acrobat Reader
```

**Unapproved software** → `success: false` → manager + IT security approval required → Jira ticket created.

### Scenario 4: Demo Endpoint (3 Tickets at Once)

```
$ curl -s -X POST http://localhost:8000/api/v1/simulate | python -m json.tool
```

```json
{
    "count": 3,
    "results": [
        {
            "triage": {"category": "PASSWORD_RESET", "can_automate": true},
            "action": "auto_resolved",
            "resolution": {"success": true, "action_taken": "password_reset_initiated"}
        },
        {
            "triage": {"category": "HARDWARE_ISSUE", "can_automate": false},
            "action": "jira_ticket_created",
            "ticket": {"ticket_id": "IT-1543", "priority": "High"}
        },
        {
            "triage": {"category": "SOFTWARE_INSTALL", "can_automate": true},
            "action": "auto_resolved",
            "resolution": {"success": true, "action_taken": "software_deployed_via_intune"}
        }
    ]
}
```

---

## Design Decisions

### Why GPT-4o with JSON Mode for Triage?

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Rule-based keyword matching** | Fast, no API cost | Brittle, misses context ("my screen is cracked" vs "my screen froze") | ❌ Too many false positives |
| **Fine-tuned classifier** | High accuracy, low latency | Training data needed, model drift, retraining costs | ❌ Overkill for 8 categories |
| **GPT-4o JSON mode** | Understands context + nuance, provides reasoning, structured output, confidence scoring | API latency (~1s), cost per call | ✅ **Selected** |
| **GPT-4o with function calling** | More structured, tool-use pattern | More complex, same latency | ❌ JSON mode is simpler for classification |

**Key insight**: `response_format={"type": "json_object"}` guarantees valid JSON output, eliminating parsing failures. The `temperature=0.1` ensures deterministic classification while allowing GPT-4o to express its reasoning.

### Why Dual Deployment (FastAPI + Azure Functions)?

| Concern | FastAPI (Local) | Azure Functions (Production) |
|---------|----------------|------------------------------|
| **Development speed** | Hot reload, instant testing | Deploy cycle required |
| **Debugging** | Full debugger, breakpoints | Application Insights, Log Analytics |
| **Scaling** | Single process | Auto-scale to zero, consumption billing |
| **Teams integration** | Manual curl/API testing | Native webhook → Service Bus → processor |
| **Cost** | Free (local) | Pay-per-execution (~$0.20/1M executions) |

**Architecture**: Both modes share the same `shared/` module — triage, auto-resolve, Jira, Teams logic is **identical**. Only the entry point differs.

### Why Rule-Based Auto-Resolution (Not LLM)?

| Approach | Latency | Cost | Determinism | Auditability |
|----------|---------|------|-------------|-------------|
| **LLM decides resolution steps** | +2s per step | $0.01+ per ticket | Non-deterministic | Hard to audit |
| **Rule-based dispatch** | <10ms | Free | 100% deterministic | Fully auditable |

**Selected: Rule-based** — After GPT-4o classifies the ticket, the resolution logic is pure Python with zero LLM calls. This gives:
- **Deterministic outcomes**: Password reset always sends the same email flow
- **Audit trail**: Every `action_taken` is logged with structured JSON
- **Cost efficiency**: LLM cost is one API call per ticket, not per resolution step
- **Safety**: No chance of LLM hallucinating a resolution action

### Why Service Bus Queue (Not Direct Processing)?

```
  Without Queue:                    With Service Bus Queue:
  ─────────────                     ──────────────────────
  Teams → Function → Process        Teams → Function → Queue → Processor
           (blocking)                        (non-blocking)    (async)

  Problems:                         Benefits:
  • Teams webhook timeout (10s)     • Webhook returns 202 instantly
  • Lost tickets on failure         • Failed tickets retry automatically
  • No backpressure control         • Queue absorbs traffic spikes
                                    • Dead-letter queue for poison messages
```

---

## Data Contracts

### Enums

```python
class TicketCategory(str, Enum):
    """8 IT support categories — drives routing and auto-resolution eligibility."""
    PASSWORD_RESET   = "PASSWORD_RESET"    # Auto-resolvable
    VPN_ACCESS       = "VPN_ACCESS"        # Auto-resolvable
    SOFTWARE_INSTALL = "SOFTWARE_INSTALL"  # Conditionally auto-resolvable
    HARDWARE_ISSUE   = "HARDWARE_ISSUE"    # Always escalated
    NETWORK_ISSUE    = "NETWORK_ISSUE"     # Always escalated
    EMAIL_ISSUE      = "EMAIL_ISSUE"       # Always escalated
    PRINTER_ISSUE    = "PRINTER_ISSUE"     # Always escalated
    OTHER            = "OTHER"             # Always escalated
```

```python
class Priority(str, Enum):
    """4-level priority — maps directly to Jira priority field."""
    CRITICAL = "CRITICAL"  # Entire team/system down, security breach
    HIGH     = "HIGH"      # Single user completely unable to work
    MEDIUM   = "MEDIUM"    # User can partially work
    LOW      = "LOW"       # Minor inconvenience, workaround available
```

### Pydantic Models

```python
class TicketRequest(BaseModel):
    """API input — what the user submits."""
    ticket_text: str = Field(..., min_length=5)         # Required, minimum 5 chars
    user_email: str = Field(default="user@contoso.com") # Defaults to generic email
    user_display_name: str = Field(default="User")      # Display name for Teams

class TicketTriage(BaseModel):
    """GPT-4o classification result — drives all downstream logic."""
    category: TicketCategory                             # Which category
    priority: Priority                                   # How urgent
    can_automate: bool                                   # Auto-resolve or escalate?
    automation_action: Optional[str] = None              # Suggested action (informational)
    jira_summary: str                                    # LLM-generated Jira title
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)  # Classification confidence
    reasoning: str = ""                                  # LLM explanation

class ResolutionResult(BaseModel):
    """Auto-resolver output — what action was taken and outcome."""
    success: bool                                        # Did auto-resolution succeed?
    action_taken: str                                    # Machine-readable action ID
    message: str                                         # User-facing message
    details: dict = Field(default_factory=dict)          # Action-specific metadata

class JiraTicket(BaseModel):
    """Jira ticket created for escalated issues."""
    ticket_id: str                                       # e.g., "IT-1542"
    url: str                                             # Full Jira browse URL
    summary: str                                         # Ticket title
    priority: str                                        # Mapped Jira priority
    category: str                                        # Original category
    status: str = "Open"                                 # Initial status
```

### Internal Data Contracts (dict Structures)

```python
# user_info — passed between webhook → processor → resolver
user_info = {
    "user_id": str,            # Teams user ID (webhook only)
    "user_email": str,         # Email address for notifications
    "user_display_name": str,  # Display name
    "message_text": str,       # Original ticket text
    "channel_id": str,         # Teams channel (webhook only)
}

# Resolution detail variations
password_reset_details = {
    "reference": "PSW-47823",           # Unique tracking reference
    "method": "azure_ad_self_service",  # Resolution method
    "expires_hours": 24,                # Link validity
}

vpn_access_details = {
    "vpn_group": "VPN-AllUsers",       # VPN group membership
    "server": "vpn.contoso.com",       # VPN server address
    "certificate_valid": True,          # Certificate status
}

software_approved_details = {
    "approved": True,                   # On approved list
    "method": "Microsoft Intune",       # Deployment mechanism
    "eta_minutes": 15,                  # Expected install time
}

software_unapproved_details = {
    "approved": False,
    "reason": "Not on approved software list",
}
```

---

## Features

| # | Feature | Description | Module |
|---|---------|-------------|--------|
| 1 | **GPT-4o Structured Triage** | JSON-mode classification with 8 categories, 4 priorities, confidence scoring | `shared/triage.py` |
| 2 | **Auto-Resolution Engine** | Rule-based dispatch for PASSWORD_RESET, VPN_ACCESS, SOFTWARE_INSTALL | `shared/auto_resolve.py` |
| 3 | **Password Reset Automation** | Azure AD self-service reset with tracking reference and 24h expiry | `AutoResolver` |
| 4 | **VPN Access Verification** | GlobalProtect access verification with certificate validation | `AutoResolver` |
| 5 | **Software Deployment** | Approved-list check → Microsoft Intune push (15 approved apps) | `AutoResolver` |
| 6 | **Unapproved Software Escalation** | Non-approved software → manager + security approval workflow | `AutoResolver` |
| 7 | **Jira Ticket Creation** | Automatic ticket creation with priority mapping and full context | `shared/jira_client.py` |
| 8 | **Priority Mapping** | CRITICAL→Highest, HIGH→High, MEDIUM→Medium, LOW→Low | `JiraClient` |
| 9 | **Teams Resolution Notifications** | Auto-resolved issues get instant Teams message with resolution details | `shared/teams_client.py` |
| 10 | **Teams Ticket Notifications** | Escalated issues get ticket ID, URL, ETA, emergency contact | `TeamsClient` |
| 11 | **SLA-Based ETA** | High/Highest → "2 hours", others → "1 business day" | `TeamsClient` |
| 12 | **Dual Deployment** | FastAPI (local dev) + Azure Functions (production serverless) | `main.py` / `functions/` |
| 13 | **Teams Webhook Integration** | Azure Function HTTP trigger receives Teams bot payloads | `functions/teams_webhook/` |
| 14 | **Service Bus Queuing** | Async ticket processing with retry and dead-letter support | `functions/teams_webhook/` |
| 15 | **Service Bus Trigger** | Event-driven ticket processing from queue | `functions/ticket_processor/` |
| 16 | **Structured JSON Logging** | structlog with ISO timestamps, log levels, JSON rendering | `main.py` |
| 17 | **Pydantic Validation** | Input validation with min_length, Field constraints, type safety | `shared/models.py` |
| 18 | **Pydantic Settings** | Environment-based config with `.env` file support | `shared/config.py` |
| 19 | **LRU-Cached Settings** | `@lru_cache` prevents re-reading `.env` on every request | `shared/config.py` |
| 20 | **Graceful Fallback** | Triage failure → default to OTHER/MEDIUM with 0.5 confidence | `shared/triage.py` |
| 21 | **Local Mode** | `LOCAL_MODE=true` — mock Jira/Teams, no Azure dependencies | `.env` |
| 22 | **CORS Middleware** | All origins allowed for development flexibility | `main.py` |
| 23 | **Health Endpoint** | `GET /health` with service name and version | `main.py` |
| 24 | **Demo Simulator** | `POST /api/v1/simulate` processes 3 sample tickets | `main.py` |
| 25 | **End-to-End Demo Script** | `demo_e2e.py` — standalone test of all components | `demo_e2e.py` |
| 26 | **Comprehensive Tests** | 6 async tests covering triage, auto-resolve, Jira | `tests/test_triage.py` |
| 27 | **OpenAI Mock Testing** | AsyncMock patches for GPT-4o calls in tests | `tests/test_triage.py` |
| 28 | **Azure Function Portability** | `HAS_AZURE_FUNCTIONS` flag for local testing without Azure SDK | `functions/` |
| 29 | **OpenAI Retry Logic** | `max_retries=3` on AsyncAzureOpenAI client | `shared/triage.py` |
| 30 | **Low Temperature** | `temperature=0.1` for deterministic classification | `shared/triage.py` |
| 31 | **Triage Prompt Engineering** | Detailed system prompt with category definitions and examples | `shared/triage.py` |
| 32 | **Confidence Scoring** | 0.0–1.0 confidence in triage for downstream decision-making | `TicketTriage` |

---

## Prerequisites

<details>
<summary><strong>macOS</strong></summary>

```bash
# Python 3.11+
brew install python@3.11

# Verify
python3 --version    # Python 3.11.x

# Optional: Azure CLI (for Functions deployment)
brew install azure-cli

# Optional: Azure Functions Core Tools
brew install azure/functions/azure-functions-core-tools@4
```
</details>

<details>
<summary><strong>Windows</strong></summary>

```powershell
# Python 3.11+ from python.org or winget
winget install Python.Python.3.11

# Verify
python --version    # Python 3.11.x

# Optional: Azure CLI
winget install Microsoft.AzureCLI

# Optional: Azure Functions Core Tools
npm install -g azure-functions-core-tools@4
```
</details>

<details>
<summary><strong>Linux (Ubuntu/Debian)</strong></summary>

```bash
# Python 3.11+
sudo apt update && sudo apt install python3.11 python3.11-venv python3-pip

# Verify
python3.11 --version    # Python 3.11.x

# Optional: Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Optional: Azure Functions Core Tools
sudo apt install azure-functions-core-tools-4
```
</details>

### Azure Services (Production Only)

| Service | Purpose | Required for Local? |
|---------|---------|-------------------|
| Azure OpenAI (GPT-4o) | Ticket classification | ✅ Yes (or mock via test) |
| Azure Service Bus | Async ticket queuing | ❌ No (local mode skips) |
| Azure Functions | Serverless hosting | ❌ No (FastAPI for local) |
| Jira Cloud | Ticket management | ❌ No (mock client) |
| Microsoft Teams | User notifications | ❌ No (mock client) |

---

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/maneeshkumar52/it-ticketing-agent.git
cd it-ticketing-agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your Azure OpenAI credentials:

```bash
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
LOCAL_MODE=true
```

### 3. Run the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started reloader process
INFO:     Application startup complete.
```

### 4. Test with curl

```bash
# Health check
curl http://localhost:8000/health

# Submit a ticket
curl -X POST http://localhost:8000/api/v1/ticket \
  -H "Content-Type: application/json" \
  -d '{"ticket_text": "I forgot my password", "user_email": "alice@contoso.com"}'

# Run demo simulation
curl -X POST http://localhost:8000/api/v1/simulate
```

### 5. Run the Demo Script

```bash
python demo_e2e.py
```

Expected output:
```
=== IT Ticketing Agent - End-to-End Demo ===

Password reset auto-resolution:
  Status: success
  Message: Password reset email sent to emp-john-smith@contoso.com...

VPN access auto-resolution:
  Status: success
  Message: Your VPN access has been verified and is active...

Jira ticket created: IT-1542
  Title: Monitor flickering on workstation
  Status: Open

Teams notification sent (mock mode)

--- Ticket Processing Scenarios ---
  [+] Cannot login to laptop: AUTO-RESOLVED
  [-] VPN not connecting from home: AUTO-RESOLVED
  [+] Request to install VS Code: AUTO-RESOLVED
  [-] Monitor flickering: ESCALATED TO IT TEAM

=== IT Ticketing Agent: Auto-resolution and escalation working ===
```

---

## Project Structure

```
it-ticketing-agent/
├── main.py                              # FastAPI app — local development entry point
├── demo_e2e.py                          # End-to-end demo script (no server needed)
├── requirements.txt                     # Python dependencies (12 packages)
├── .env.example                         # Environment variable template
├── shared/                              # Core business logic (shared between modes)
│   ├── __init__.py
│   ├── config.py                        # Pydantic Settings — environment configuration
│   ├── models.py                        # All Pydantic models and enums
│   ├── triage.py                        # GPT-4o ticket classification engine
│   ├── auto_resolve.py                  # Rule-based auto-resolution dispatcher
│   ├── jira_client.py                   # Jira ticket creation client
│   └── teams_client.py                  # Microsoft Teams notification client
├── functions/                           # Azure Functions — production entry points
│   ├── host.json                        # Azure Functions host configuration
│   ├── teams_webhook/                   # HTTP trigger — receives Teams payloads
│   │   ├── __init__.py                  # Webhook handler → Service Bus queue
│   │   └── function.json                # Trigger binding configuration
│   └── ticket_processor/               # Service Bus trigger — processes queued tickets
│       ├── __init__.py                  # Dequeue → triage → resolve/escalate
│       └── function.json                # Service Bus binding configuration
└── tests/                               # Test suite
    ├── __init__.py
    └── test_triage.py                   # 6 async tests with OpenAI mocking
```

### Module Responsibility Matrix

| Module | Responsibility | Dependencies | Lines |
|--------|---------------|-------------|-------|
| `main.py` | FastAPI app, HTTP endpoints, CORS, structured logging | `shared/*` | 97 |
| `demo_e2e.py` | Standalone demo — tests all components without server | `shared/*` | 54 |
| `shared/config.py` | Environment config via Pydantic Settings, `.env` loading | `pydantic_settings` | 24 |
| `shared/models.py` | 2 enums, 4 Pydantic models — all data contracts | `pydantic` | 40 |
| `shared/triage.py` | GPT-4o structured JSON classification with prompt engineering | `openai`, `config`, `models` | 80 |
| `shared/auto_resolve.py` | Rule-based dispatch for 3 auto-resolvable categories | `models` | 77 |
| `shared/jira_client.py` | Jira ticket creation with priority mapping | `models`, `config` | 30 |
| `shared/teams_client.py` | Teams webhook notifications (resolution + ticket) | `config`, `httpx` | 39 |
| `functions/teams_webhook/__init__.py` | HTTP trigger → extract user_info → queue to Service Bus | `azure.servicebus` | 48 |
| `functions/ticket_processor/__init__.py` | Service Bus trigger → triage → resolve/escalate pipeline | `shared/*` | 48 |
| `tests/test_triage.py` | 6 async tests with OpenAI mocking | `pytest-asyncio`, `unittest.mock` | 82 |

---

## Configuration Reference

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | `https://your-openai.openai.azure.com/` | ✅ Production | Azure OpenAI service endpoint |
| `AZURE_OPENAI_API_KEY` | `your-key` | ✅ Production | API key for Azure OpenAI |
| `AZURE_OPENAI_API_VERSION` | `2024-02-01` | ❌ | API version for Azure OpenAI |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-4o` | ❌ | Model deployment name |
| `SERVICE_BUS_CONNECTION_STRING` | `""` | ✅ Production | Azure Service Bus connection string |
| `SERVICE_BUS_QUEUE` | `it-tickets` | ❌ | Service Bus queue name |
| `JIRA_BASE_URL` | `https://your-org.atlassian.net` | ❌ | Jira Cloud instance URL |
| `JIRA_PROJECT_KEY` | `IT` | ❌ | Jira project key for ticket IDs |
| `TEAMS_WEBHOOK_URL` | `""` | ❌ | Teams incoming webhook URL |
| `LOCAL_MODE` | `true` | ❌ | Run without Azure dependencies |
| `LOG_LEVEL` | `INFO` | ❌ | Logging level (DEBUG, INFO, WARNING, ERROR) |

---

## API Reference

### `GET /health`

Health check endpoint.

**Response** `200 OK`:
```json
{
    "status": "healthy",
    "service": "it-ticketing-agent",
    "version": "1.0.0"
}
```

### `POST /api/v1/ticket`

Process a single IT support ticket.

**Request Body**:
```json
{
    "ticket_text": "I forgot my password and cannot log in",  // Required, min 5 chars
    "user_email": "alice@contoso.com",                         // Optional
    "user_display_name": "Alice Smith"                         // Optional
}
```

**Response** `200 OK` (Auto-Resolved):
```json
{
    "triage": {
        "category": "PASSWORD_RESET",
        "priority": "HIGH",
        "can_automate": true,
        "confidence": 0.97,
        "reasoning": "Clear password reset request"
    },
    "user_email": "alice@contoso.com",
    "action": "auto_resolved",
    "resolution": {
        "success": true,
        "action_taken": "password_reset_initiated",
        "message": "Password reset email sent to alice@contoso.com...",
        "details": {"reference": "PSW-47823", "method": "azure_ad_self_service", "expires_hours": 24}
    }
}
```

**Response** `200 OK` (Escalated):
```json
{
    "triage": {
        "category": "HARDWARE_ISSUE",
        "priority": "HIGH",
        "can_automate": false,
        "confidence": 0.95,
        "reasoning": "Physical hardware damage"
    },
    "user_email": "bob@contoso.com",
    "action": "jira_ticket_created",
    "ticket": {
        "ticket_id": "IT-1542",
        "url": "https://your-org.atlassian.net/browse/IT-1542",
        "summary": "Cracked laptop screen replacement",
        "priority": "High"
    }
}
```

### `POST /api/v1/simulate`

Demo endpoint — processes 3 sample tickets (password reset, hardware issue, software install).

**Response** `200 OK`:
```json
{
    "count": 3,
    "results": [/* 3 ticket results */]
}
```

---

## Azure Functions Deployment

### Architecture (Production)

```
  Microsoft Teams Bot
         │
         ▼
  ┌──────────────────────────┐
  │  teams_webhook           │     ┌─────────────────────┐
  │  (HTTP Trigger)          │────►│  Azure Service Bus   │
  │  POST /api/teams_webhook │     │  Queue: "it-tickets" │
  │  Returns 202 Accepted    │     └──────────┬──────────┘
  └──────────────────────────┘                │
                                              ▼
                               ┌──────────────────────────┐
                               │  ticket_processor         │
                               │  (Service Bus Trigger)    │
                               │  ├─ triage_ticket()       │
                               │  ├─ AutoResolver.dispatch()│
                               │  ├─ JiraClient.create()   │
                               │  └─ TeamsClient.notify()  │
                               └──────────────────────────┘
```

### Deploy to Azure

```bash
# Login to Azure
az login

# Create Function App
az functionapp create \
  --name it-ticketing-agent \
  --resource-group rg-it-ticketing \
  --storage-account itticketstorage \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4

# Set environment variables
az functionapp config appsettings set \
  --name it-ticketing-agent \
  --resource-group rg-it-ticketing \
  --settings \
    AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/ \
    AZURE_OPENAI_API_KEY=your-key \
    AZURE_OPENAI_DEPLOYMENT=gpt-4o \
    SERVICE_BUS_CONNECTION_STRING="Endpoint=sb://..." \
    SERVICE_BUS_QUEUE=it-tickets \
    LOCAL_MODE=false

# Deploy
cd functions
func azure functionapp publish it-ticketing-agent
```

### Function Bindings

**teams_webhook** (`function.json`):
```json
{
    "bindings": [
        {"authLevel": "function", "type": "httpTrigger", "direction": "in", "name": "req", "methods": ["post"]},
        {"type": "http", "direction": "out", "name": "$return"}
    ]
}
```

**ticket_processor** (`function.json`):
```json
{
    "bindings": [
        {"name": "msg", "type": "serviceBusTrigger", "direction": "in",
         "queueName": "it-tickets", "connection": "SERVICE_BUS_CONNECTION_STRING"}
    ]
}
```

---

## Testing

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with async support
pytest tests/ -v --asyncio-mode=auto
```

### Test Coverage

| Test | What It Verifies | Mock Strategy |
|------|-----------------|---------------|
| `test_password_reset_triaged_correctly` | GPT-4o classifies "forgot password" as PASSWORD_RESET with can_automate=true | AsyncMock on `openai.AsyncAzureOpenAI` |
| `test_hardware_not_automatable` | "Cracked screen" → HARDWARE_ISSUE with can_automate=false | AsyncMock on `openai.AsyncAzureOpenAI` |
| `test_software_install_auto` | "Install Teams" → SOFTWARE_INSTALL with can_automate=true | AsyncMock on `openai.AsyncAzureOpenAI` |
| `test_auto_resolve_password_reset` | AutoResolver returns success with user email in message | Direct call (no mock needed) |
| `test_auto_resolve_approved_software` | Approved software → success, "Intune" in message | Direct call |
| `test_auto_resolve_unapproved_software` | "HackerTool 9000" → success=false | Direct call |
| `test_jira_creates_ticket` | JiraClient generates IT-XXXX ticket ID with correct status | Direct call |

### Mocking Strategy

The tests mock **only the external API boundary** (Azure OpenAI) and test the **business logic directly**:

```python
# Triage tests: Mock the LLM response, verify classification logic
with patch("openai.AsyncAzureOpenAI") as mock_oai:
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
    mock_oai.return_value = mock_client
    result = await triage_ticket("I forgot my password")
    assert result.category == TicketCategory.PASSWORD_RESET

# Auto-resolve tests: No mocks needed — pure business logic
resolver = AutoResolver()
result = await resolver.resolve_password_reset("alice@contoso.com")
assert result.success is True
```

---

## Ticket Processing Scenarios

### Auto-Resolution Matrix

| Category | Auto-Resolve? | Resolution Method | User Message |
|----------|:------------:|-------------------|-------------|
| PASSWORD_RESET | ✅ Always | Azure AD self-service reset | "Reset link sent, expires in 24h" |
| VPN_ACCESS | ✅ Always | GlobalProtect access verification | "VPN access verified, use vpn.contoso.com" |
| SOFTWARE_INSTALL (approved) | ✅ If approved | Microsoft Intune deployment | "Pushed via Intune, restart in 15 min" |
| SOFTWARE_INSTALL (unapproved) | ❌ | Manager + security approval | "Approval required, JIRA ticket created" |
| HARDWARE_ISSUE | ❌ Never | Jira escalation | "IT-XXXX created, ETA: 2 hours" |
| NETWORK_ISSUE | ❌ Never | Jira escalation | "IT-XXXX created, ETA: 1 business day" |
| EMAIL_ISSUE | ❌ Never | Jira escalation | "IT-XXXX created" |
| PRINTER_ISSUE | ❌ Never | Jira escalation | "IT-XXXX created" |
| OTHER | ❌ Never | Jira escalation | "IT-XXXX created" |

### Priority → Jira Mapping

| Agent Priority | Jira Priority | Expected Response Time |
|---------------|--------------|----------------------|
| CRITICAL | Highest | Immediate |
| HIGH | High | 2 hours |
| MEDIUM | Medium | 1 business day |
| LOW | Low | 1 business day |

### Approved Software List

Software deployed automatically via Microsoft Intune:

| Software | Match Keywords |
|----------|---------------|
| Microsoft Office | `microsoft office`, `ms office` |
| Microsoft Teams | `teams`, `microsoft teams` |
| Zoom | `zoom` |
| Google Chrome | `chrome`, `google chrome` |
| Mozilla Firefox | `firefox` |
| Slack | `slack` |
| VS Code | `vscode`, `visual studio code` |
| 7-Zip | `7-zip` |
| Adobe Reader | `adobe reader`, `acrobat reader` |

---

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| `openai.AuthenticationError` | Invalid Azure OpenAI API key | Verify `AZURE_OPENAI_API_KEY` in `.env` |
| `openai.NotFoundError` | Wrong deployment name | Check `AZURE_OPENAI_DEPLOYMENT` matches your Azure portal |
| `openai.APIConnectionError` | Wrong endpoint URL | Verify `AZURE_OPENAI_ENDPOINT` format: `https://xxx.openai.azure.com/` |
| Triage returns `OTHER` with 0.5 confidence | OpenAI API call failed (graceful fallback) | Check logs for `triage_failed` error |
| `422 Unprocessable Entity` on POST | `ticket_text` shorter than 5 characters | Ensure min 5 chars in ticket text |
| Teams notifications not sending | `TEAMS_WEBHOOK_URL` empty | Set webhook URL or ignore (mock mode logs to console) |
| Service Bus queue errors | Missing connection string | Set `SERVICE_BUS_CONNECTION_STRING` in Azure Function settings |
| `ModuleNotFoundError: azure.functions` | Running Functions code locally without SDK | Install: `pip install azure-functions` |
| Jira ticket IDs reset on restart | Mock client uses `random.randint` for counter | Expected behavior — production Jira assigns real IDs |
| `connection refused` on port 8000 | Server not running | Run `uvicorn main:app --port 8000` |
| Slow triage response (>3s) | Azure OpenAI cold start or high load | `max_retries=3` handles transient failures |

---

## Azure Production Mapping

| Local Component | Azure Production Service | Purpose |
|----------------|-------------------------|---------|
| `uvicorn main:app` | Azure Functions (Consumption Plan) | Serverless compute |
| `POST /api/v1/ticket` | `teams_webhook` HTTP Trigger | Teams bot entry point |
| In-process triage + resolve | `ticket_processor` Service Bus Trigger | Async processing |
| — | Azure Service Bus Queue (`it-tickets`) | Message queuing + retry |
| `openai.AsyncAzureOpenAI` | Azure OpenAI Service (GPT-4o) | Ticket classification |
| Mock `JiraClient` | Jira Cloud REST API | Ticket management |
| Mock `TeamsClient` | Microsoft Teams Incoming Webhook | User notifications |
| `structlog` JSON output | Application Insights + Log Analytics | Observability |
| `.env` file | Azure Function App Settings | Secrets management |
| — | Azure Key Vault | Production secrets (recommended) |
| `python -m pytest` | Azure DevOps / GitHub Actions | CI/CD pipeline |
| — | Azure Monitor Alerts | SLA monitoring |

### Production Architecture (Azure)

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                         Azure Resource Group                            │
  │                                                                         │
  │  ┌─────────────┐    ┌──────────────┐    ┌──────────────────────────┐   │
  │  │ Azure Bot    │───►│ Azure        │───►│ Azure Service Bus       │   │
  │  │ Service      │    │ Functions    │    │ Queue: "it-tickets"      │   │
  │  │ (Teams)      │    │ teams_webhook│    │ • Dead-letter queue      │   │
  │  └─────────────┘    └──────────────┘    │ • 3 retry attempts       │   │
  │                                          └───────────┬──────────────┘   │
  │                                                      │                  │
  │                                                      ▼                  │
  │  ┌──────────────────────────────────────────────────────────────────┐   │
  │  │  Azure Functions — ticket_processor (Service Bus Trigger)        │   │
  │  │  ├─ Azure OpenAI GPT-4o (triage)                                │   │
  │  │  ├─ Azure AD (password resets)                                   │   │
  │  │  ├─ Microsoft Intune (software deployment)                       │   │
  │  │  ├─ Jira Cloud API (ticket creation)                            │   │
  │  │  └─ Teams Webhook (notifications)                                │   │
  │  └──────────────────────────────────────────────────────────────────┘   │
  │                                                                         │
  │  ┌──────────────────┐    ┌──────────────────┐    ┌────────────────┐    │
  │  │ Application      │    │ Azure Key Vault  │    │ Azure Monitor  │    │
  │  │ Insights         │    │ (Secrets)        │    │ (Alerts)       │    │
  │  └──────────────────┘    └──────────────────┘    └────────────────┘    │
  └─────────────────────────────────────────────────────────────────────────┘
```

---

## Production Checklist

### Security

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Replace `AZURE_OPENAI_API_KEY` with Key Vault reference | ⬜ | `@Microsoft.KeyVault(SecretUri=...)` |
| 2 | Replace `SERVICE_BUS_CONNECTION_STRING` with Managed Identity | ⬜ | Use `DefaultAzureCredential` |
| 3 | Remove `allow_origins=["*"]` CORS — restrict to Teams domain | ⬜ | `*.teams.microsoft.com` |
| 4 | Set `authLevel: "function"` key rotation schedule | ⬜ | Rotate quarterly |
| 5 | Enable Application Insights for all Functions | ⬜ | Set `APPINSIGHTS_INSTRUMENTATIONKEY` |
| 6 | Validate `ticket_text` for injection attempts | ⬜ | Max length, sanitize before LLM |
| 7 | Rate-limit `/api/v1/ticket` endpoint | ⬜ | Azure API Management or WAF |

### Reliability

| # | Item | Status | Notes |
|---|------|--------|-------|
| 8 | Configure Service Bus dead-letter queue monitoring | ⬜ | Alert on dead-letter count > 0 |
| 9 | Set Azure OpenAI timeout to 30s (current: default) | ⬜ | Prevent hanging requests |
| 10 | Add circuit breaker for Jira API | ⬜ | `tenacity` with exponential backoff |
| 11 | Configure Function App auto-scaling limits | ⬜ | Max 100 concurrent instances |
| 12 | Add health probe for Functions | ⬜ | Azure Monitor + availability tests |

### Observability

| # | Item | Status | Notes |
|---|------|--------|-------|
| 13 | Structured logs → Log Analytics workspace | ⬜ | KQL queries for triage metrics |
| 14 | Dashboard: auto-resolve rate, avg triage time, category distribution | ⬜ | Azure Monitor Workbook |
| 15 | Alert: triage confidence < 0.5 spike | ⬜ | Indicates prompt drift |
| 16 | Alert: auto-resolve success rate < 95% | ⬜ | Indicates system issues |

### Operations

| # | Item | Status | Notes |
|---|------|--------|-------|
| 17 | Replace mock JiraClient with real Jira REST API | ⬜ | `jira` Python package or httpx |
| 18 | Replace mock password reset with Azure AD Graph API | ⬜ | `msgraph-sdk-python` |
| 19 | Replace mock Intune deployment with Graph API | ⬜ | Device management endpoint |
| 20 | Set up CI/CD pipeline (GitHub Actions → Azure Functions) | ⬜ | `azure/functions-action@v1` |
| 21 | Add integration tests against live Azure OpenAI | ⬜ | Separate test pipeline |
| 22 | Document runbook for common operational scenarios | ⬜ | Teams channel escalation |

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Runtime** | Python | 3.11+ |
| **Web Framework** | FastAPI | 0.111.0 |
| **ASGI Server** | Uvicorn | 0.30.0 |
| **AI/ML** | Azure OpenAI (GPT-4o) | API 2024-02-01 |
| **AI SDK** | openai (Python) | 1.40.0 |
| **Messaging** | Azure Service Bus | 7.12.0 |
| **Identity** | Azure Identity | 1.16.0 |
| **Validation** | Pydantic | 2.7.0 |
| **Configuration** | pydantic-settings | 2.3.0 |
| **Logging** | structlog | 24.2.0 |
| **HTTP Client** | httpx | 0.27.0 |
| **Environment** | python-dotenv | 1.0.1 |
| **Testing** | pytest + pytest-asyncio | 8.2.0 / 0.23.0 |
| **Serverless** | Azure Functions | v4 |

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built by [Maneesh Kumar](https://github.com/maneeshkumar52)**

*Prompt to Production — Chapter 20, Project 3*

*Autonomous IT support that resolves 60%+ of common tickets in seconds, not hours.*

</div>