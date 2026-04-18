# IT Ticketing Agent

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

Intelligent IT support agent for automated ticket triage, routing, auto-resolution, and escalation — powered by Azure OpenAI with Jira and Microsoft Teams integration.

## Architecture

```
Incoming Ticket (API / Service Bus / Teams Webhook)
        │
        ▼
┌───────────────────────────────────────┐
│  FastAPI Service (:8000)              │
│                                       │
│  POST /tickets ──► TriageEngine       │──► Priority + category classification
│       │                               │
│       ▼                               │
│  AutoResolver ──► Known-issue match   │──► Auto-resolve or escalate
│       │                               │
│       ├──► JiraClient                 │──► Create/update Jira tickets
│       └──► TeamsClient                │──► Send Teams notifications
└───────────────────────────────────────┘
        │
Azure Service Bus (async queue processing)
        │
Azure Functions (ticket_processor / teams_webhook)
```

## Key Features

- **AI-Powered Triage** — GPT-4o classifies ticket priority (P1-P4) and category (network, hardware, software, access, other)
- **Auto-Resolution** — Pattern matching against known issues for instant resolution
- **Jira Integration** — Automatic ticket creation and status updates via Jira REST API
- **Teams Notifications** — Webhook-based alerts for P1/P2 escalations
- **Azure Service Bus** — Async ticket queue processing for high-volume workloads
- **Azure Functions** — Serverless ticket processor and Teams webhook handler
- **LOCAL_MODE** — Full pipeline runs locally without Azure dependencies

## Step-by-Step Flow

### Step 1: Ticket Submission
User submits a ticket via `POST /tickets` with subject, description, and contact info.

### Step 2: AI Triage
`triage_ticket()` sends the ticket to GPT-4o, which returns structured JSON with priority, category, suggested_resolution, and confidence_score.

### Step 3: Auto-Resolution Check
`AutoResolver` checks if the ticket matches a known issue pattern. If confidence is high enough, it auto-resolves and skips escalation.

### Step 4: Jira Ticket Creation
`JiraClient.create_issue()` creates a Jira ticket with triage metadata (priority, category, AI-suggested resolution).

### Step 5: Teams Notification
For P1/P2 tickets, `TeamsClient.send_notification()` posts an adaptive card to the configured Teams channel.

### Step 6: Response
Returns the triage result, Jira ticket key, and resolution status.

## Repository Structure

```
it-ticketing-agent/
├── main.py                      # FastAPI app — /tickets endpoint
├── shared/
│   ├── triage.py                # AI triage engine (GPT-4o)
│   ├── auto_resolve.py          # Known-issue auto-resolution
│   ├── jira_client.py           # Jira REST API client
│   ├── teams_client.py          # Teams webhook client
│   ├── models.py                # Pydantic models
│   └── config.py                # Environment settings
├── functions/
│   ├── ticket_processor/        # Azure Function — queue-triggered processing
│   ├── teams_webhook/           # Azure Function — Teams webhook handler
│   └── host.json
├── tests/
│   └── test_triage.py
├── demo_e2e.py
├── requirements.txt
└── .env.example
```

## Quick Start

```bash
git clone https://github.com/maneeshkumar52/it-ticketing-agent.git
cd it-ticketing-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Set LOCAL_MODE=true for local testing
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Yes | Azure OpenAI endpoint |
| `AZURE_OPENAI_DEPLOYMENT` | Yes | Model deployment (gpt-4o) |
| `LOCAL_MODE` | No | Run without Azure dependencies (default: true) |
| `JIRA_BASE_URL` | No | Jira instance URL |
| `JIRA_PROJECT_KEY` | No | Jira project key (e.g., IT) |
| `TEAMS_WEBHOOK_URL` | No | Teams incoming webhook URL |
| `SERVICE_BUS_CONNECTION_STRING` | No | Azure Service Bus connection |

## Testing

```bash
pytest -q
python demo_e2e.py
```

## License

MIT
