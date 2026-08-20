import html

MAX_MESSAGE_CHARS = 8000
MAX_BODY_BYTES = 64 * 1024


def validate_message(text: str) -> tuple[bool, str]:
    if text is None or not str(text).strip():
        return False, "Enter a message before running the analysis."
    if len(str(text)) > MAX_MESSAGE_CHARS:
        return False, f"Message exceeds the {MAX_MESSAGE_CHARS:,}-character limit."
    return True, ""


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; base-uri 'none'; frame-ancestors 'none'",
    "Cache-Control": "no-store",
}
