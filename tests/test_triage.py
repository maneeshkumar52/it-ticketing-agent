"""Tests for IT ticket triage and auto-resolution."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from shared.models import TicketCategory, Priority


@pytest.mark.asyncio
async def test_password_reset_triaged_correctly():
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = '{"category":"PASSWORD_RESET","priority":"HIGH","can_automate":true,"automation_action":"send_password_reset_email","jira_summary":"Password reset for user","confidence":0.97,"reasoning":"Clear password reset"}'
    with patch("openai.AsyncAzureOpenAI") as mock_oai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
        mock_oai.return_value = mock_client
        from shared.triage import triage_ticket
        result = await triage_ticket("I forgot my password and can't login")
        assert result.category == TicketCategory.PASSWORD_RESET
        assert result.can_automate is True
        assert result.confidence >= 0.9


@pytest.mark.asyncio
async def test_hardware_not_automatable():
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = '{"category":"HARDWARE_ISSUE","priority":"HIGH","can_automate":false,"automation_action":null,"jira_summary":"Cracked laptop screen replacement","confidence":0.95,"reasoning":"Physical damage"}'
    with patch("openai.AsyncAzureOpenAI") as mock_oai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
        mock_oai.return_value = mock_client
        from shared.triage import triage_ticket
        result = await triage_ticket("My laptop screen is cracked")
        assert result.category == TicketCategory.HARDWARE_ISSUE
        assert result.can_automate is False


@pytest.mark.asyncio
async def test_software_install_auto():
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = '{"category":"SOFTWARE_INSTALL","priority":"LOW","can_automate":true,"automation_action":"deploy_via_intune","jira_summary":"Install Microsoft Teams","confidence":0.92,"reasoning":"Approved software"}'
    with patch("openai.AsyncAzureOpenAI") as mock_oai:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
        mock_oai.return_value = mock_client
        from shared.triage import triage_ticket
        result = await triage_ticket("Please install Microsoft Teams on my laptop")
        assert result.category == TicketCategory.SOFTWARE_INSTALL
        assert result.can_automate is True


@pytest.mark.asyncio
async def test_auto_resolve_password_reset():
    from shared.auto_resolve import AutoResolver
    r = AutoResolver()
    result = await r.resolve_password_reset("alice@contoso.com")
    assert result.success is True
    assert "alice@contoso.com" in result.message
    assert "reference" in result.details


@pytest.mark.asyncio
async def test_auto_resolve_approved_software():
    from shared.auto_resolve import AutoResolver
    r = AutoResolver()
    result = await r.resolve_software_install("bob@contoso.com", "Microsoft Teams")
    assert result.success is True
    assert "Intune" in result.message


@pytest.mark.asyncio
async def test_auto_resolve_unapproved_software():
    from shared.auto_resolve import AutoResolver
    r = AutoResolver()
    result = await r.resolve_software_install("bob@contoso.com", "HackerTool 9000")
    assert result.success is False


@pytest.mark.asyncio
async def test_jira_creates_ticket():
    from shared.jira_client import JiraClient
    jira = JiraClient()
    ticket = await jira.create_ticket("Cracked screen", "Details...", Priority.HIGH, "HARDWARE_ISSUE", "alice@contoso.com")
    assert ticket.ticket_id.startswith("IT-")
    assert ticket.status == "Open"
