"""Tests for error handling — timeouts, auth failures, malformed XML."""

import pytest
from unittest.mock import AsyncMock, patch
import httpx

from elm_alm_py.oslc import get_catalog_url, query_resources, get_resource


@pytest.mark.asyncio
async def test_catalog_url_timeout():
    with patch("elm_alm_py.oslc.get_client", new_callable=AsyncMock) as mock_client:
        client = AsyncMock()
        client.get.side_effect = httpx.TimeoutException("Connection timed out")
        mock_client.return_value = client
        with pytest.raises(httpx.TimeoutException):
            await get_catalog_url("rm")


@pytest.mark.asyncio
async def test_catalog_url_401():
    with patch("elm_alm_py.oslc.get_client", new_callable=AsyncMock) as mock_client:
        client = AsyncMock()
        resp = httpx.Response(401, request=httpx.Request("GET", "http://test"))
        client.get.return_value = resp
        mock_client.return_value = client
        with pytest.raises(httpx.HTTPStatusError):
            await get_catalog_url("rm")


@pytest.mark.asyncio
async def test_get_resource_404():
    with patch("elm_alm_py.oslc.get_client", new_callable=AsyncMock) as mock_client:
        client = AsyncMock()
        resp = httpx.Response(404, request=httpx.Request("GET", "http://test/rm/req/999"))
        client.get.return_value = resp
        mock_client.return_value = client
        with pytest.raises(httpx.HTTPStatusError):
            await get_resource("http://test/rm/req/999")


@pytest.mark.asyncio
async def test_catalog_malformed_xml():
    with patch("elm_alm_py.oslc.get_client", new_callable=AsyncMock) as mock_client:
        client = AsyncMock()
        resp = httpx.Response(200, text="<not-valid-xml>", request=httpx.Request("GET", "http://test"))
        client.get.return_value = resp
        mock_client.return_value = client
        with pytest.raises(Exception):  # ET.ParseError or ValueError
            await get_catalog_url("rm")


@pytest.mark.asyncio
async def test_query_resources_project_not_found():
    with patch("elm_alm_py.oslc.list_service_providers", new_callable=AsyncMock) as mock:
        mock.return_value = [{"title": "Other", "url": "http://elm/sp/1"}]
        with pytest.raises(ValueError, match="not found"):
            await query_resources("rm", "NonExistent", None)
