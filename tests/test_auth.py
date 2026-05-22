"""Tests for Jazz form-based authentication."""

import pytest
import httpx
import respx

from elm_alm_py.auth import _authenticate, close_client

BASE = "https://elm.example.com"


@pytest.fixture(autouse=True)
async def cleanup(monkeypatch):
    monkeypatch.setattr("elm_alm_py.config.settings.elm_url", BASE)
    yield
    await close_client()


@respx.mock
async def test_authenticate_success():
    respx.post(f"{BASE}/jts/j_security_check").mock(return_value=httpx.Response(200))
    client = httpx.AsyncClient(verify=False)
    await _authenticate(client)
    await client.aclose()


@respx.mock
async def test_authenticate_failure():
    respx.post(f"{BASE}/jts/j_security_check").mock(
        return_value=httpx.Response(200, headers={"X-com-ibm-team-repository-web-auth-msg": "authfailed"})
    )
    client = httpx.AsyncClient(verify=False)
    with pytest.raises(RuntimeError, match="authentication failed"):
        await _authenticate(client)
    await client.aclose()
