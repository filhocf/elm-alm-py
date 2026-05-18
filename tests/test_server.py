"""Tests for MCP server tool registration."""

import pytest

from elm_alm_py.server import mcp, list_projects

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
