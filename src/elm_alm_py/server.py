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
    select = "dcterms:title,dcterms:identifier,dcterms:type,oslc_cm:status,dcterms:contributor"
    results = await oslc.query_resources("ccm", project, query, select=select)
    parsed = []
    for item in results:
        entry = {"rdf:about": item.get("rdf:about", item.get("rdf:resource", ""))}
        if "dcterms:title" in item:
            entry["title"] = item["dcterms:title"]
        if "dcterms:identifier" in item:
            entry["id"] = item["dcterms:identifier"]
        if "dcterms:type" in item:
            t = item["dcterms:type"]
            entry["type"] = t.get("rdf:resource", t) if isinstance(t, dict) else t
        if "oslc_cm:status" in item:
            entry["status"] = item["oslc_cm:status"]
        if "dcterms:contributor" in item:
            c = item["dcterms:contributor"]
            entry["owner"] = c.get("rdf:resource", c) if isinstance(c, dict) else c
        parsed.append(entry)
    return parsed


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
async def list_iterations(project: str) -> list[dict]:
    """List iterations (sprints/releases) for an RTC project with title and dates."""
    project_url = await oslc._resolve_project_url("ccm", project)
    parts = project_url.split("/contexts/")
    project_area_id = parts[1].split("/")[0] if len(parts) > 1 else project_url.rstrip("/").split("/")[-1]
    client = await oslc.get_client()
    url = f"{settings.elm_url}/ccm/oslc/iterations?projectArea={project_area_id}"
    resp = await client.get(url, headers={"Accept": "application/json", "OSLC-Core-Version": "2.0"})
    resp.raise_for_status()
    results = resp.json().get("oslc:results", [])
    iterations = []
    for r in results:
        iter_uri = r.get("rdf:resource")
        if not iter_uri:
            continue
        detail = await client.get(iter_uri, headers={"Accept": "application/json", "OSLC-Core-Version": "2.0"})
        if detail.status_code != 200:
            continue
        d = detail.json()
        iterations.append(
            {
                "title": d.get("dcterms:title", ""),
                "identifier": d.get("dcterms:identifier", ""),
                "start_date": (d.get("rtc_cm:startDate") or "")[:10] or None,
                "end_date": (d.get("rtc_cm:endDate") or "")[:10] or None,
                "uri": iter_uri,
            }
        )
    return iterations


@mcp.tool()
async def get_plan_items(project: str, plan: str | None = None, item_ids: list[str] | None = None) -> dict:
    """Get hierarchical view of Items de Backlog with their child Tarefas expanded.

    RTC/EWM hierarchy: Plan → Sprint → Item de Backlog (grouper) → Tarefa (actual work).
    This tool resolves the hierarchy in one call, avoiding N+1 queries.

    Two modes:
    - item_ids: expand specific IBs by ID (fastest, use when you know the IDs)
    - plan: match iteration by title substring, then find IBs planned for it

    Args:
        project: Project name (e.g., "MEU IMOVEL RURAL (MIR)")
        plan: Iteration title substring to match (e.g., "Entrega 5"). Optional.
        item_ids: List of IB IDs to expand directly (e.g., ["622299", "622289"]). Optional.
    """
    if not plan and not item_ids:
        return {"error": "Provide either 'plan' (iteration name) or 'item_ids' (list of IB IDs)"}

    iteration_info = None

    if item_ids:
        # Direct mode: expand given IB IDs
        ib_ids_to_fetch = item_ids
    else:
        # Iteration mode: find matching iteration, then get IBs
        iterations = await list_iterations(project)
        matched = [i for i in iterations if plan.lower() in i["title"].lower()]
        if not matched:
            return {"error": f"No iteration matching '{plan}'", "available": [i["title"] for i in iterations if i["start_date"]]}
        iteration_info = matched[0]
        iter_uri = iteration_info["uri"]

        # Get all IBs (type=story) and filter by plannedFor
        all_items = await oslc.query_resources(
            "ccm", project, None,
            select="dcterms:title,dcterms:identifier,dcterms:type"
        )
        ib_ids_to_fetch = []
        for item in all_items:
            item_type = item.get("dcterms:type", "")
            if isinstance(item_type, dict):
                item_type = item_type.get("rdf:resource", "")
            if "story" in str(item_type).lower():
                ib_id = item.get("dcterms:identifier", "")
                if ib_id:
                    ib_ids_to_fetch.append(ib_id)

    # Fetch each IB and build hierarchy
    result_items = []
    for ib_id in ib_ids_to_fetch:
        try:
            full = await get_workitem(ib_id)
        except Exception:
            continue

        # If filtering by iteration, check plannedFor
        if iteration_info:
            planned = full.get("rtc_cm:plannedFor", {})
            planned_uri = planned.get("rdf:resource", "") if isinstance(planned, dict) else str(planned)
            if iter_uri not in planned_uri:
                continue

        # Extract children
        children_raw = full.get("rtc_cm:com.ibm.team.workitem.linktype.parentworkitem.children", [])
        children = []
        for child in children_raw:
            raw_title = child.get("dcterms:title", "")
            child_id = raw_title.split(":")[0].strip() if ":" in raw_title else ""
            child_title = raw_title.split(": ", 1)[1] if ": " in raw_title else raw_title
            children.append({"id": child_id, "title": child_title, "uri": child.get("rdf:resource", "")})

        status = full.get("oslc_cm:status", "")
        owner = full.get("dcterms:contributor", {})
        if isinstance(owner, dict):
            owner = owner.get("rdf:resource", "").split("/")[-1]

        result_items.append({
            "id": ib_id,
            "type": "Item de Backlog",
            "title": full.get("dcterms:title", ""),
            "status": status,
            "owner": owner,
            "children_count": len(children),
            "children": children,
        })

    result = {"items_count": len(result_items), "items": result_items}
    if iteration_info:
        result["iteration"] = iteration_info["title"]
        result["start_date"] = iteration_info["start_date"]
        result["end_date"] = iteration_info["end_date"]
    return result


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
    # project_url may be .../contexts/{id}/workitems/services.xml — extract the context ID
    parts = project_url.split("/contexts/")
    project_area_id = parts[1].split("/")[0] if len(parts) > 1 else project_url.rstrip("/").split("/")[-1]
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
    owner: str | None = None,
    estimate_hours: float | None = None,
    planned_for: str | None = None,
    custom_fields: dict | None = None,
) -> dict:
    """Update fields of an existing work item via OSLC PUT.

    Args:
        id: Work item ID (number)
        title: New title (optional)
        description: New description (optional)
        owner: Username to assign (e.g., "claudio.filho")
        estimate_hours: Estimate in hours (e.g., 8 = 8h)
        planned_for: Iteration URI (e.g., from get_workitem response)
        custom_fields: Dict of extra fields to merge into PUT payload
    """
    payload: dict = {}
    if title is not None:
        payload["dcterms:title"] = title
    if description is not None:
        payload["dcterms:description"] = description
    if owner is not None:
        from urllib.parse import quote

        payload["dcterms:contributor"] = {"rdf:resource": f"{settings.elm_url}/jts/users/{quote(owner)}"}
    if estimate_hours is not None:
        payload["rtc_cm:estimate"] = int(estimate_hours * 3600000)
    if planned_for is not None:
        payload["rtc_cm:plannedFor"] = {"rdf:resource": planned_for}
    if custom_fields:
        payload.update(custom_fields)
    if not payload:
        raise ValueError("At least one field must be provided")
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


@mcp.tool()
async def transition_workitem(id: str, action: str) -> str:
    """Transition a work item's workflow state.

    Args:
        id: Work item ID
        action: One of: start, resolve, close, reopen
    """
    valid_actions = ("start", "resolve", "close", "reopen")
    if action not in valid_actions:
        raise ValueError(f"Invalid action '{action}'. Must be one of: {valid_actions}")

    uri = f"{settings.elm_url}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/{id}"
    client = await oslc.get_client()

    # GET current state + ETag
    get_resp = await client.get(uri, headers={"Accept": "application/json", "OSLC-Core-Version": "2.0"})
    get_resp.raise_for_status()
    etag = get_resp.headers.get("ETag", "")
    if not etag:
        raise ValueError(f"Server did not return an ETag for work item {id}")

    current = get_resp.json()

    # Discover available actions from workflow
    actions_url = f"{uri}/rtc_cm:workflowActions"
    actions_resp = await client.get(actions_url, headers={"Accept": "application/json", "OSLC-Core-Version": "2.0"})

    target_state_uri = None
    if actions_resp.status_code == 200:
        actions_data = actions_resp.json()
        workflow_actions = actions_data.get("rtc_cm:actions", [])
        if isinstance(workflow_actions, dict):
            workflow_actions = [workflow_actions]
        for wa in workflow_actions:
            wa_id = (wa.get("dcterms:identifier") or "").lower()
            if action in wa_id:
                result_state = wa.get("rtc_cm:resultState") or {}
                target_state_uri = result_state.get("rdf:resource", "")
                break

    # Fallback: hardcoded common RTC state mappings
    if not target_state_uri:
        base = f"{settings.elm_url}/ccm/oslc/workflows"
        state_map = {
            "start": f"{base}/states/com.ibm.team.workitem.taskWorkflow/2",
            "resolve": f"{base}/states/com.ibm.team.workitem.taskWorkflow/3",
            "close": f"{base}/states/com.ibm.team.workitem.taskWorkflow/4",
            "reopen": f"{base}/states/com.ibm.team.workitem.taskWorkflow/1",
        }
        target_state_uri = state_map[action]

    # PUT with updated state
    current["rtc_cm:state"] = {"rdf:resource": target_state_uri}
    resp = await client.put(
        uri,
        json=current,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "OSLC-Core-Version": "2.0",
            "If-Match": etag,
        },
    )
    resp.raise_for_status()
    return f"Work item {id} transitioned to '{action}' (state: {target_state_uri})"


def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
