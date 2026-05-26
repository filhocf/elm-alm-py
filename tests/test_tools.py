"""Tests for MCP tools — mocked OSLC responses."""

import pytest
from unittest.mock import AsyncMock, patch

from elm_alm_py.server import (
    list_projects,
    search_requirements,
    get_requirement,
    list_workitems,
    get_workitem,
    search_testcases,
)


@pytest.mark.asyncio
async def test_list_projects_rm():
    with patch("elm_alm_py.server.oslc.list_service_providers", new_callable=AsyncMock) as mock:
        mock.return_value = [{"title": "MIR", "url": "http://elm/rm/sp/1"}]
        result = await list_projects("rm")
        assert result == [{"title": "MIR", "url": "http://elm/rm/sp/1"}]
        mock.assert_called_once_with("rm")


@pytest.mark.asyncio
async def test_list_projects_ccm():
    with patch("elm_alm_py.server.oslc.list_service_providers", new_callable=AsyncMock) as mock:
        mock.return_value = [{"title": "RTC Project", "url": "http://elm/ccm/sp/1"}]
        result = await list_projects("ccm")
        assert len(result) == 1


@pytest.mark.asyncio
async def test_list_projects_qm():
    with patch("elm_alm_py.server.oslc.list_service_providers", new_callable=AsyncMock) as mock:
        mock.return_value = []
        result = await list_projects("qm")
        assert result == []


@pytest.mark.asyncio
async def test_list_projects_invalid_domain_raises():
    with pytest.raises(ValueError, match="Invalid domain"):
        await list_projects("invalid")


@pytest.mark.asyncio
async def test_search_requirements_with_query():
    with patch("elm_alm_py.server.oslc.query_resources", new_callable=AsyncMock) as mock:
        mock.return_value = [{"title": "REQ-001", "uri": "http://elm/rm/req/1"}]
        result = await search_requirements("MIR", "dcterms:title='REQ-001'")
        mock.assert_called_once_with("rm", "MIR", "dcterms:title='REQ-001'")
        assert result[0]["title"] == "REQ-001"


@pytest.mark.asyncio
async def test_search_requirements_no_query():
    with patch("elm_alm_py.server.oslc.query_resources", new_callable=AsyncMock) as mock:
        mock.return_value = []
        result = await search_requirements("MIR", None)
        mock.assert_called_once_with("rm", "MIR", None)
        assert result == []


@pytest.mark.asyncio
async def test_get_requirement():
    with patch("elm_alm_py.server.oslc.get_resource", new_callable=AsyncMock) as mock:
        mock.return_value = {"dcterms:title": "Login Feature", "dcterms:identifier": "REQ-42"}
        result = await get_requirement("http://elm/rm/req/42")
        mock.assert_called_once_with("http://elm/rm/req/42")
        assert result["dcterms:identifier"] == "REQ-42"


@pytest.mark.asyncio
async def test_list_workitems():
    with patch("elm_alm_py.server.oslc.query_resources", new_callable=AsyncMock) as mock:
        mock.return_value = [{"dcterms:title": "Bug #123", "dcterms:identifier": "123", "rdf:about": "http://x"}]
        result = await list_workitems("MIR", "oslc_cm:type='defect'")
        mock.assert_called_once_with(
            "ccm", "MIR", "oslc_cm:type='defect'",
            select="dcterms:title,dcterms:identifier,dcterms:type,oslc_cm:status,dcterms:contributor",
        )
        assert len(result) == 1
        assert result[0]["title"] == "Bug #123"


@pytest.mark.asyncio
async def test_get_workitem():
    with patch("elm_alm_py.server.oslc.get_resource", new_callable=AsyncMock) as mock:
        mock.return_value = {"dcterms:title": "Fix login", "dcterms:identifier": "123"}
        result = await get_workitem("123")
        assert "123" in mock.call_args[0][0]
        assert result["dcterms:title"] == "Fix login"


@pytest.mark.asyncio
async def test_search_testcases():
    with patch("elm_alm_py.server.oslc.query_resources", new_callable=AsyncMock) as mock:
        mock.return_value = [{"title": "TC-001"}]
        result = await search_testcases("QA Project")
        mock.assert_called_once_with("qm", "QA Project", None)
        assert result[0]["title"] == "TC-001"
