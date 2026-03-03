# Autonomous IT Ticketing Agent

**Project 3, Chapter 20 — "Prompt to Production" by Maneesh Kumar**

An autonomous IT support agent that classifies incoming support requests using GPT-4o, auto-resolves common issues (password resets, VPN access, standard software installs), and creates JIRA tickets for issues requiring human escalation. Notifications are delivered back to users via Microsoft Teams.

---

## Architecture & Flow

```
Teams Message
     |
     v
[HTTP Trigger Function]  <-- Azure Function (functions/teams_webhook/)
     |
     | (enqueue JSON payload)
     v
[Azure Service Bus Queue: it-tickets]
     |
     v
[Ticket Processor Function]  <-- Azure Function (functions/ticket_processor/)
     |
     v
[GPT-4o Triage]  <-- shared/triage.py
     |
     +---> can_automate=True  ---> [AutoResolver]  ---> Teams DM: "Resolved"
     |                                (shared/auto_resolve.py)
     |
     +---> can_automate=False ---> [JiraClient]    ---> Teams DM: "Ticket IT-XXXX created"
                                   (shared/jira_client.py)
```

---

## Category Handling

| Category         | Auto-Resolve | Method                        | Escalate To |
|------------------|:------------:|-------------------------------|-------------|
| PASSWORD_RESET   | Yes          | Azure AD Self-Service Reset   | —           |
| VPN_ACCESS       | Yes          | GlobalProtect verification    | —           |
| SOFTWARE_INSTALL | Yes*         | Microsoft Intune deployment   | Manager + IT if unapproved |
| HARDWARE_ISSUE   | No           | —                             | JIRA ticket |
| NETWORK_ISSUE    | No           | —                             | JIRA ticket |
| EMAIL_ISSUE      | No           | —                             | JIRA ticket |
| PRINTER_ISSUE    | No           | —                             | JIRA ticket |
| OTHER            | No           | —                             | JIRA ticket |

*SOFTWARE_INSTALL is auto-resolved only for approved software (Teams, Zoom, Chrome, Office, Slack, Firefox, VSCode, 7-Zip, Adobe Reader).

---

## Project Structure

```
it-ticketing-agent/
├── functions/
│   ├── teams_webhook/
│   │   ├── __init__.py        # HTTP trigger — receives Teams webhook
│   │   └── function.json      # Azure Functions binding config
│   ├── ticket_processor/
│   │   ├── __init__.py        # Service Bus trigger — processes tickets
│   │   └── function.json      # Azure Functions binding config
│   └── host.json              # Azure Functions host configuration
├── shared/
│   ├── __init__.py
│   ├── config.py              # Pydantic settings with env var support
│   ├── models.py              # TicketTriage, ResolutionResult, JiraTicket
│   ├── triage.py              # GPT-4o ticket classification
│   ├── auto_resolve.py        # Automated resolution handlers
│   ├── jira_client.py         # JIRA ticket creation
│   └── teams_client.py        # Teams notification delivery
├── tests/
│   ├── __init__.py
│   └── test_triage.py         # Pytest async tests
├── main.py                    # FastAPI app for local development
├── .env.example               # Environment variable template
├── requirements.txt
└── README.md
```

---

## Quick Start (Local Development)

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd it-ticketing-agent
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your Azure OpenAI credentials
```

### 3. Run the FastAPI server

```bash
uvicorn main:app --reload
```

API docs available at: http://localhost:8000/docs

---

## API Endpoints

| Method | Path                  | Description                              |
|--------|-----------------------|------------------------------------------|
| GET    | /health               | Health check                             |
| POST   | /api/v1/ticket        | Submit an IT support ticket              |
| POST   | /api/v1/simulate      | Run a 3-ticket demo (no auth required)   |

---

## Sample Requests & Responses

### Auto-Resolve Path: Password Reset

```bash
curl -X POST http://localhost:8000/api/v1/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_text": "I forgot my password and cannot log in to my computer",
    "user_email": "alice@contoso.com",
    "user_display_name": "Alice Smith"
  }'
```

**Response:**

```json
{
  "triage": {
    "category": "PASSWORD_RESET",
    "priority": "HIGH",
    "can_automate": true,
    "confidence": 0.97,
    "reasoning": "User explicitly states forgotten password and login failure"
  },
  "user_email": "alice@contoso.com",
  "action": "auto_resolved",
  "resolution": {
    "success": true,
    "action_taken": "password_reset_initiated",
    "message": "Password reset email sent to alice@contoso.com. The reset link expires in 24 hours. Check your inbox and spam folder.",
    "details": {
      "reference": "PSW-47821",
      "method": "azure_ad_self_service",
      "expires_hours": 24
    }
  }
}
```

---

### Escalation Path: Hardware Issue (JIRA Ticket Created)

```bash
curl -X POST http://localhost:8000/api/v1/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_text": "My laptop screen is cracked and I cannot see anything on it",
    "user_email": "bob@contoso.com",
    "user_display_name": "Bob Jones"
  }'
```

**Response:**

```json
{
  "triage": {
    "category": "HARDWARE_ISSUE",
    "priority": "HIGH",
    "can_automate": false,
    "confidence": 0.95,
    "reasoning": "Physical hardware damage requires on-site technician"
  },
  "user_email": "bob@contoso.com",
  "action": "jira_ticket_created",
  "ticket": {
    "ticket_id": "IT-1042",
    "url": "https://your-org.atlassian.net/browse/IT-1042",
    "summary": "Cracked laptop screen — user unable to work",
    "priority": "High"
  }
}
```

---

### Demo: Simulate 3 Ticket Types

```bash
curl -X POST http://localhost:8000/api/v1/simulate
```

Runs three tickets in sequence:
1. Password reset (auto-resolved)
2. Cracked laptop screen (JIRA ticket)
3. Install Microsoft Teams (auto-resolved via Intune)

---

## Running Tests

```bash
pytest tests/ -v
```

Tests cover:
- Password reset triage classification
- Hardware issue flagged as non-automatable
- Software install auto-resolution (approved and unapproved)
- JIRA ticket creation with correct ID format
- AutoResolver dispatch routing

---

## Environment Variables

| Variable                      | Description                          | Default                                 |
|-------------------------------|--------------------------------------|-----------------------------------------|
| AZURE_OPENAI_ENDPOINT         | Azure OpenAI resource endpoint       | https://your-openai.openai.azure.com/   |
| AZURE_OPENAI_API_KEY          | Azure OpenAI API key                 | your-key                                |
| AZURE_OPENAI_API_VERSION      | API version                          | 2024-02-01                              |
| AZURE_OPENAI_DEPLOYMENT       | Deployment name (model)              | gpt-4o                                  |
| SERVICE_BUS_CONNECTION_STRING | Azure Service Bus connection string  | (empty — local mode)                    |
| SERVICE_BUS_QUEUE             | Queue name for ticket messages       | it-tickets                              |
| JIRA_BASE_URL                 | Jira instance base URL               | https://your-org.atlassian.net          |
| JIRA_PROJECT_KEY              | Jira project key for new tickets     | IT                                      |
| TEAMS_WEBHOOK_URL             | Incoming webhook URL for Teams       | (empty — mock mode)                     |
| LOCAL_MODE                    | Skip real Azure services when true   | true                                    |
| LOG_LEVEL                     | Logging verbosity                    | INFO                                    |

---

## Azure Functions Deployment

### Prerequisites

- Azure Functions Core Tools v4
- Azure CLI authenticated (`az login`)
- Azure Service Bus namespace with queue named `it-tickets`
- Azure OpenAI resource with a `gpt-4o` deployment

### Deploy

```bash
cd functions/
func azure functionapp publish <your-function-app-name>
```

### Configure App Settings

```bash
az functionapp config appsettings set \
  --name <your-function-app-name> \
  --resource-group <your-rg> \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com/" \
    AZURE_OPENAI_API_KEY="<key>" \
    AZURE_OPENAI_DEPLOYMENT="gpt-4o" \
    SERVICE_BUS_CONNECTION_STRING="<connection-string>" \
    JIRA_BASE_URL="https://your-org.atlassian.net" \
    JIRA_PROJECT_KEY="IT" \
    TEAMS_WEBHOOK_URL="<webhook-url>"
```

### Teams App Integration

Register the `teams_webhook` function URL as an outgoing webhook or bot endpoint in your Microsoft Teams admin portal. The function accepts POST requests with the Teams Activity schema.

---

## Key Design Decisions

- **GPT-4o with JSON mode**: Forces structured output to guarantee parseable triage results every time.
- **Confidence threshold**: Triage returns a confidence score (0.0–1.0); low-confidence results fall back to `OTHER` / JIRA escalation.
- **Graceful degradation**: If the OpenAI call fails, the ticket defaults to `OTHER / MEDIUM / can_automate=False` and creates a JIRA ticket rather than dropping the request.
- **Local mode**: When `SERVICE_BUS_CONNECTION_STRING` is empty, the webhook function logs instead of queuing. When `TEAMS_WEBHOOK_URL` is empty, Teams messages are logged instead of sent.
- **Approved software list**: Prevents unauthorized software deployment through the automated path.

---

## Book Reference

This project is **Project 3** from **Chapter 20** of:

> **Prompt to Production** by Maneesh Kumar
>
> *Building production-grade agentic AI systems with Azure, OpenAI, and Python.*

The chapter walks through designing an autonomous IT support pipeline that handles thousands of employee requests without human triage, integrating Azure Functions, Service Bus, Azure OpenAI, JIRA, and Microsoft Teams into a cohesive event-driven system.
