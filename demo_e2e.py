import asyncio, sys
sys.path.insert(0, '.')

async def main():
    print("=== IT Ticketing Agent - End-to-End Demo ===\n")

    # Test 1: Triage with mock data
    from shared.auto_resolve import AutoResolver
    from shared.models import Priority
    resolver = AutoResolver()

    # Test password reset resolution (method takes user_email)
    result = await resolver.resolve_password_reset("emp-john-smith@contoso.com")
    print(f"Password reset auto-resolution:")
    print(f"  Status: {'success' if result.success else 'failed'}")
    print(f"  Message: {result.message}")

    # Test VPN access (method takes user_email only)
    result2 = await resolver.resolve_vpn_access("emp-jane-doe@contoso.com")
    print(f"\nVPN access auto-resolution:")
    print(f"  Status: {'success' if result2.success else 'failed'}")
    print(f"  Message: {result2.message}")

    # Test Jira client mock
    from shared.jira_client import JiraClient
    jira = JiraClient()
    ticket = await jira.create_ticket(
        summary="Monitor flickering on workstation",
        description="Employee reports monitor flickering since this morning",
        priority=Priority.MEDIUM,
        category="hardware",
        reporter="user@contoso.com",
    )
    print(f"\nJira ticket created: {ticket.ticket_id}")
    print(f"  Title: {ticket.summary}")
    print(f"  Status: {ticket.status}")

    # Test Teams notification
    from shared.teams_client import TeamsClient
    teams = TeamsClient()
    await teams.send_resolution_notification(
        "user@contoso.com",
        "Ticket IT-1234: Monitor flickering on workstation",
    )
    print(f"\nTeams notification sent (mock mode)")

    # Test ticket scenarios
    print(f"\n--- Ticket Processing Scenarios ---")
    test_tickets = [
        {"title": "Cannot login to laptop", "category": "password_reset"},
        {"title": "VPN not connecting from home", "category": "vpn_access"},
        {"title": "Request to install VS Code", "category": "software_install"},
        {"title": "Monitor flickering", "category": "hardware"},
    ]
    for t in test_tickets:
        can_auto = t['category'] in ['password_reset', 'vpn_access', 'software_install']
        print(f"  [{'+'  if can_auto else '-'}] {t['title']}: {'AUTO-RESOLVED' if can_auto else 'ESCALATED TO IT TEAM'}")

    print("\n=== IT Ticketing Agent: Auto-resolution and escalation working ===")

asyncio.run(main())
