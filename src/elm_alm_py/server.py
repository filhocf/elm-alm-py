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


TYPE_IDS = {
    "task": "task",
    "story": "com.ibm.team.apt.workItemType.story",
}


@mcp.tool()
async def create_workitem(
    project: str,
    title: str,
    type: str = "task",
    description: str | None = None,
    parent_id: str | None = None,
    owner: str | None = None,
    filed_against: str | None = None,
    custom_fields: dict | None = None,
) -> dict:
    """Create a work item in an RTC project via OSLC.

    Args:
        project: Project name (e.g., "MEU IMOVEL RURAL (MIR)")
        title: Work item title (required)
        type: "task" or "story" (default: "task")
        description: HTML description (optional)
        parent_id: Parent work item ID (optional)
        owner: Username of the owner (optional, e.g., "claudio.filho")
        filed_against: Category URI (optional). If not provided, discovers default from project.
        custom_fields: Dict of extra RDF fields to inject (e.g., {"rtc_ext:campo": "valor"})
    """
    if type not in TYPE_IDS:
        raise ValueError(f"Invalid type '{type}'. Must be one of: {list(TYPE_IDS.keys())}")
    project_url = await oslc._resolve_project_url("ccm", project)
    project_area_id = project_url.rstrip("/").split("/")[-1]
    payload: dict = {
        "dcterms:title": title,
        "dcterms:type": "http://open-services.net/ns/cm#ChangeRequest",
        "rtc_cm:type": {"rdf:resource": f"{settings.elm_url}/ccm/oslc/types/{project_area_id}/{TYPE_IDS[type]}"},
    }
    if description:
        payload["dcterms:description"] = description
    if parent_id:
        payload["rtc_cm:com.ibm.team.workitem.linktype.parentworkitem.parent"] = [
            {"rdf:resource": f"{settings.elm_url}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/{parent_id}"}
        ]
    if owner:
        payload["rtc_cm:ownedBy"] = {"rdf:resource": f"{settings.elm_url}/jts/users/{owner}"}
    if not filed_against:
        filed_against = await oslc._find_default_category(project_url)
    if filed_against:
        payload["rtc_cm:filedAgainst"] = {"rdf:resource": filed_against}
    # Auto-discover current iteration
    planned_for = await oslc._find_current_iteration(project_url)
    if planned_for:
        payload["rtc_cm:plannedFor"] = {"rdf:resource": planned_for}
    # Inject custom fields (project-specific customizations)
    if custom_fields:
        payload.update(custom_fields)
    return await oslc.create_resource("ccm", project, payload, wi_type=type)


@mcp.tool()
async def update_workitem(
    id: str,
    title: str | None = None,
    description: str | None = None,
) -> dict:
    """Update fields of an existing work item via OSLC PUT."""
    payload: dict = {}
    if title is not None:
        payload["dcterms:title"] = title
    if description is not None:
        payload["dcterms:description"] = description
    if not payload:
        raise ValueError("At least one field (title, description) must be provided")
    uri = f"{settings.elm_url}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/{id}"
    return await oslc.update_resource(uri, payload)


@mcp.tool()
async def add_child_workitem(
    parent_id: str,
    title: str,
    type: str = "task",
    description: str | None = None,
    owner: str | None = None,
    project: str = "MEU IMOVEL RURAL (MIR)",
) -> dict:
    """Create a child work item under a parent in an RTC project."""
    return await create_workitem(
        project=project,
        title=title,
        type=type,
        description=description,
        parent_id=parent_id,
        owner=owner,
    )


def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
