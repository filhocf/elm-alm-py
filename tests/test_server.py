"""Tests for MCP server tool registration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from elm_alm_py.server import mcp, list_projects, transition_workitem

VALID_DOMAINS = ("rm", "ccm", "qm")


async def test_list_projects_invalid_domain():
    with pytest.raises(ValueError, match="Invalid domain"):
        await list_projects("invalid")


def test_mcp_tools_registered():
    """Verify all 6 tools are registered."""
    tool_names = [t.name for t in mcp._tool_manager.list_tools()]
    expected = [
        "list_projects",
        "search_requirements",
        "get_requirement",
        "list_workitems",
        "get_workitem",
        "search_testcases",
    ]
    for name in expected:
        assert name in tool_names, f"Tool '{name}' not registered"


def test_transition_workitem_registered():
    """Verify transition_workitem tool is registered."""
    tool_names = [t.name for t in mcp._tool_manager.list_tools()]
    assert "transition_workitem" in tool_names


@pytest.mark.asyncio
async def test_transition_workitem_invalid_action():
    """Invalid action should raise ValueError."""
    with pytest.raises(ValueError, match="Invalid action"):
        await transition_workitem(id="12345", action="invalid")


@pytest.mark.asyncio
async def test_transition_workitem_success():
    """Successful transition should return confirmation message."""
    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 200
    mock_get_resp.headers = {"ETag": '"etag123"'}
    mock_get_resp.json.return_value = {
        "dcterms:title": "Test WI",
        "rtc_cm:state": {"rdf:resource": "http://elm/ccm/oslc/workflows/states/old"},
    }
    mock_get_resp.raise_for_status = MagicMock()

    mock_actions_resp = MagicMock()
    mock_actions_resp.status_code = 404
    mock_actions_resp.json.return_value = {}

    mock_put_resp = MagicMock()
    mock_put_resp.status_code = 200
    mock_put_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=[mock_get_resp, mock_actions_resp])
    mock_client.put = AsyncMock(return_value=mock_put_resp)

    with patch("elm_alm_py.oslc.get_client", return_value=mock_client):
        result = await transition_workitem(id="12345", action="resolve")

    assert "12345" in result
    assert "resolve" in result
    mock_client.put.assert_called_once()
