"""MCP server for IBM ELM (Engineering Lifecycle Management)."""

from mcp.server.fastmcp import FastMCP

from . import oslc
from .config import settings

mcp = FastMCP("elm-alm-py", instructions="IBM ELM (DOORS Next, RTC, ETM) via OSLC")

VALID_DOMAINS = ("rm", "ccm", "qm")


@mcp.tool()
async def list_projects(domain: str) -> list[dict]:
    """List projects for a domain (rm=DOORS Next, ccm=RTC, qm=ETM)."""
    domain = domain.lower()
    if domain not in VALID_DOMAINS:
        raise ValueError(f"Invalid domain '{domain}'. Must be one of: {VALID_DOMAINS}")
    return await oslc.list_service_providers(domain)


@mcp.tool()
async def search_requirements(project: str, query: str | None = None) -> list[dict]:
    """Search requirements in a DOORS Next project. Query uses oslc.where syntax."""
    return await oslc.query_resources("rm", project, query)


@mcp.tool()
async def get_requirement(uri: str) -> dict:
    """Get a single requirement by its OSLC URI."""
    return await oslc.get_resource(uri)


@mcp.tool()
async def list_workitems(project: str, query: str | None = None) -> list[dict]:
    """Search work items in an RTC project. Query uses oslc.where syntax."""
    return await oslc.query_resources("ccm", project, query)


@mcp.tool()
async def get_workitem(id: str) -> dict:
    """Get a single work item by ID (constructs URI from CCM base)."""
    uri = f"{settings.elm_url}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/{id}"
    return await oslc.get_resource(uri)


@mcp.tool()
async def search_testcases(project: str, query: str | None = None) -> list[dict]:
    """Search test cases in an ETM project. Query uses oslc.where syntax."""
    return await oslc.query_resources("qm", project, query)


def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()


