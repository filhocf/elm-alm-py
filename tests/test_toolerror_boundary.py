"""G5 review follow-up: domain errors from oslc.py reach the MCP client as a
readable ToolError, and transition_workitem's missing-ETag path raises ToolError.

Addresses the two P1/P2 findings from the gate-5 review of the mcp 2.x migration:
- P1: without the tool-boundary wrap, a ValueError/RuntimeError bubbling out of a
  tool is rewrapped by MCPServer as UnexpectedToolError and its message dropped
  (client sees only "Error executing tool <name>"). These tests pin that the
  message is preserved via ToolError.
- P2: transition_workitem raises ToolError when the server returns no ETag.

Conventions: pytest + respx / unittest.mock (AGENTS.md).
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from elm_mcp import server
from elm_mcp.auth import close_client
from elm_mcp.server import (
    list_projects,
    list_workitems,
    search_requirements,
    transition_workitem,
)

BASE = "https://elm.example.com"


@pytest.fixture(autouse=True)
async def _cfg(monkeypatch):
    monkeypatch.setattr("elm_mcp.config.settings.elm_url", BASE)
    yield
    await close_client()


# --- P1: domain ValueError/RuntimeError from oslc.* -> ToolError at the boundary,
#         with the original message preserved (not swallowed). ---


async def test_list_projects_translates_oslc_valueerror_to_toolerror():
    """A ValueError from oslc.list_service_providers must surface as ToolError
    carrying the SAME message, so the MCP client sees why it failed."""
    msg = "Cannot find service provider catalog for domain 'ccm'"
    with (
        patch(
            "elm_mcp.server.oslc.list_service_providers",
            new=AsyncMock(side_effect=ValueError(msg)),
        ),
        pytest.raises(ToolError, match="Cannot find service provider catalog"),
    ):
        await list_projects("ccm")


async def test_search_requirements_translates_project_not_found():
    """'Project not found' is the most common user error — must be legible."""
    msg = "Project 'Nope' not found. Available: ['PROJ']"
    with (
        patch(
            "elm_mcp.server.oslc.query_resources",
            new=AsyncMock(side_effect=ValueError(msg)),
        ),
        pytest.raises(ToolError, match="Project 'Nope' not found"),
    ):
        await search_requirements("Nope")


async def test_list_workitems_translates_runtimeerror():
    """RuntimeError from the OSLC layer is also translated (not only ValueError)."""
    with (
        patch(
            "elm_mcp.server.oslc.query_resources",
            new=AsyncMock(side_effect=RuntimeError("Expected 201 Created, got 500")),
        ),
        pytest.raises(ToolError, match="Expected 201 Created"),
    ):
        await list_workitems("PROJ")


def test_tool_wrapper_preserves_tool_names():
    """The @tool wrapper (functools.wraps) must not rename the tools."""
    names = {t.name for t in server.mcp._tool_manager.list_tools()}
    for expected in ("list_projects", "search_requirements", "transition_workitem"):
        assert expected in names


# --- P2: transition_workitem missing-ETag branch -> ToolError (server.py). ---


async def test_transition_workitem_missing_etag_raises_toolerror():
    """If the work item GET returns no ETag, transition_workitem must raise a
    ToolError (cannot safely PUT without optimistic-lock token)."""
    fake_client = AsyncMock()
    # GET returns 200 but with NO ETag header.
    get_resp = httpx.Response(
        200,
        json={"dcterms:title": "WI"},
        request=httpx.Request("GET", f"{BASE}/ccm/x"),
    )
    fake_client.get = AsyncMock(return_value=get_resp)

    with (
        patch("elm_mcp.server.oslc.get_client", new=AsyncMock(return_value=fake_client)),
        pytest.raises(ToolError, match="did not return an ETag"),
    ):
        await transition_workitem(id="12345", action="start")
