"""
Resend Email API Client.

Requires: resend (pip install resend)
"""

from typing import Optional, Dict, Any, List

from ...config import require_secret, get_secret


def send_email(
    to: str | List[str],
    subject: str,
    text: str = None,
    html: str = None,
    reply_to: str = None,
    from_email: str = None,
    api_key: str = None,
) -> Dict[str, Any]:
    """
    Send an email via Resend.

    Args:
        to: Recipient email(s)
        subject: Email subject
        text: Plain text body
        html: HTML body
        reply_to: Reply-to address
        from_email: Sender email (default from RESEND_FROM_EMAIL)
        api_key: API key (default from RESEND_API_KEY)

    Returns:
        Dict with id and success status
    """
    try:
        import resend
    except ImportError:
        raise ImportError("resend package required. Install with: pip install resend")

    resend.api_key = api_key or require_secret("RESEND_API_KEY")
    from_addr = from_email or get_secret("RESEND_FROM_EMAIL", "noreply@example.com")

    params = {
        "from": from_addr,
        "to": [to] if isinstance(to, str) else to,
        "subject": subject,
    }

    if text:
        params["text"] = text
    if html:
        params["html"] = html
    if reply_to:
        params["reply_to"] = reply_to

    result = resend.Emails.send(params)

    return {
        "success": True,
        "id": result.get("id"),
    }


class ResendClient:
    """
    Resend email client.

    Usage:
        client = ResendClient()
        client.send(to="user@example.com", subject="Hello", text="Hi there!")
    """

    def __init__(self, api_key: str = None, from_email: str = None):
        """
        Initialize Resend client.

        Args:
            api_key: Resend API key (or set RESEND_API_KEY env var)
            from_email: Default from email (or set RESEND_FROM_EMAIL env var)
        """
        self.api_key = api_key or require_secret("RESEND_API_KEY")
        self.from_email = from_email or get_secret("RESEND_FROM_EMAIL", "noreply@example.com")

    def send(
        self,
        to: str | List[str],
        subject: str,
        text: str = None,
        html: str = None,
        reply_to: str = None,
        from_email: str = None,
    ) -> Dict[str, Any]:
        """
        Send an email.

        Args:
            to: Recipient email(s)
            subject: Email subject
            text: Plain text body
            html: HTML body
            reply_to: Reply-to address
            from_email: Override sender email

        Returns:
            Dict with id and success status
        """
        return send_email(
            to=to,
            subject=subject,
            text=text,
            html=html,
            reply_to=reply_to,
            from_email=from_email or self.from_email,
            api_key=self.api_key,
        )

    def send_template(
        self,
        to: str | List[str],
        subject: str,
        template_html: str,
        variables: Dict[str, str] = None,
        reply_to: str = None,
    ) -> Dict[str, Any]:
        """
        Send an email using an HTML template with variable substitution.

        Args:
            to: Recipient email(s)
            subject: Email subject
            template_html: HTML template with {variable} placeholders
            variables: Dict of variable replacements
            reply_to: Reply-to address

        Returns:
            Dict with id and success status
        """
        html = template_html
        if variables:
            for key, value in variables.items():
                html = html.replace(f"{{{key}}}", str(value))

        return self.send(
            to=to,
            subject=subject,
            html=html,
            reply_to=reply_to,
        )
