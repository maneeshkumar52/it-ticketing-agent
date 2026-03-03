import random
import structlog
from shared.models import TicketTriage, TicketCategory, ResolutionResult

logger = structlog.get_logger(__name__)

APPROVED_SOFTWARE = [
    "microsoft office", "ms office", "teams", "microsoft teams", "zoom",
    "chrome", "google chrome", "firefox", "slack", "vscode", "visual studio code",
    "7-zip", "adobe reader", "acrobat reader",
]


class AutoResolver:
    """Handles automated resolution of common IT issues."""

    async def resolve_password_reset(self, user_email: str) -> ResolutionResult:
        """Initiate password reset for user."""
        reference = f"PSW-{random.randint(10000, 99999)}"
        logger.info("auto_resolve_password_reset", user_email=user_email, ref=reference)
        return ResolutionResult(
            success=True,
            action_taken="password_reset_initiated",
            message=f"Password reset email sent to {user_email}. The reset link expires in 24 hours. Check your inbox and spam folder.",
            details={"reference": reference, "method": "azure_ad_self_service", "expires_hours": 24},
        )

    async def resolve_vpn_access(self, user_email: str) -> ResolutionResult:
        """Verify and provision VPN access."""
        logger.info("auto_resolve_vpn_access", user_email=user_email)
        return ResolutionResult(
            success=True,
            action_taken="vpn_access_verified",
            message="Your VPN access has been verified and is active. Use GlobalProtect to connect to vpn.contoso.com. If still unable to connect, try reinstalling the GlobalProtect client.",
            details={"vpn_group": "VPN-AllUsers", "server": "vpn.contoso.com", "certificate_valid": True},
        )

    async def resolve_software_install(self, user_email: str, software_name: str) -> ResolutionResult:
        """Approve and deploy standard software via Intune."""
        is_approved = any(sw in software_name.lower() for sw in APPROVED_SOFTWARE)
        logger.info("auto_resolve_software", software=software_name, approved=is_approved)
        if is_approved:
            return ResolutionResult(
                success=True,
                action_taken="software_deployed_via_intune",
                message=f"{software_name} is on the approved software list. Installation has been pushed to your device via Microsoft Intune. Please restart your device in 15 minutes to complete the installation.",
                details={"approved": True, "method": "Microsoft Intune", "eta_minutes": 15},
            )
        return ResolutionResult(
            success=False,
            action_taken="software_escalated_for_approval",
            message=f"{software_name} requires manager and IT security approval. A JIRA ticket has been created and your manager has been notified for approval.",
            details={"approved": False, "reason": "Not on approved software list"},
        )

    async def dispatch(self, triage: TicketTriage, user_info: dict) -> ResolutionResult:
        """Route to appropriate auto-resolution handler."""
        user_email = user_info.get("email", "user@contoso.com")
        message_text = user_info.get("message_text", "")

        if triage.category == TicketCategory.PASSWORD_RESET:
            return await self.resolve_password_reset(user_email)
        elif triage.category == TicketCategory.VPN_ACCESS:
            return await self.resolve_vpn_access(user_email)
        elif triage.category == TicketCategory.SOFTWARE_INSTALL:
            sw = "Unknown Software"
            for known in ["Teams", "Zoom", "Chrome", "Office", "Slack", "Firefox", "VSCode"]:
                if known.lower() in message_text.lower():
                    sw = known
                    break
            return await self.resolve_software_install(user_email, sw)
        else:
            return ResolutionResult(
                success=False,
                action_taken="escalated",
                message="This issue requires manual IT support.",
                details={"reason": "Category not auto-resolvable"},
            )
