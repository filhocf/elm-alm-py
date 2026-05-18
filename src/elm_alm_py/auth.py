"""Form-based Jazz authentication with cookie management."""

import httpx

from .config import settings

_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    """Get authenticated httpx client, re-authenticating if needed."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(verify=False, timeout=60.0, follow_redirects=True)
        await _authenticate(_client)
    return _client


async def _authenticate(client: httpx.AsyncClient) -> None:
    """Perform Jazz form-based authentication."""
    auth_url = f"{settings.elm_url}/jts/j_security_check"
    resp = await client.post(
        auth_url,
        data={"j_username": settings.elm_user, "j_password": settings.elm_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    # Jazz returns 200 or 302 on success; check for auth failure header
    if "X-com-ibm-team-repository-web-auth-msg" in resp.headers:
        raise RuntimeError(f"ELM authentication failed for user '{settings.elm_user}'")


async def close_client() -> None:
    """Close the HTTP client."""
    global _client
    if _client:
        await _client.aclose()
        _client = None
