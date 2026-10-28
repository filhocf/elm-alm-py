"""OSLC service discovery and query builder for IBM ELM."""

import logging
from xml.etree import ElementTree as ET

import httpx

from .auth import get_client
from .config import settings

logger = logging.getLogger(__name__)

# OSLC XML namespaces (ELM 7.x uses OSLC 1.0 namespaces in rootservices)
NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "oslc": "http://open-services.net/ns/core#",
    "oslc_rm": "http://open-services.net/ns/rm#",
    "oslc_cm": "http://open-services.net/ns/cm#",
    "oslc_qm": "http://open-services.net/ns/qm#",
    "oslc_rm_v1": "http://open-services.net/xmlns/rm/1.0/",
    "oslc_cm_v1": "http://open-services.net/xmlns/cm/1.0/",
    "oslc_qm_v1": "http://open-services.net/xmlns/qm/1.0/",
    "dcterms": "http://purl.org/dc/terms/",
    "jfs": "http://jazz.net/xmlns/prod/jazz/jfs/1.0/",
}

DOMAIN_PATHS = {
    "rm": "/rm/rootservices",
    "ccm": "/ccm/rootservices",
    "qm": "/qm/rootservices",
}

# Catalog discovery XPath per domain — try v1 namespace first (ELM 7.x), fallback to v2
CATALOG_XPATH = {
    "rm": [".//oslc_rm_v1:rmServiceProviders", ".//oslc_rm:rmServiceProviders"],
    "ccm": [".//oslc_cm_v1:cmServiceProviders", ".//oslc_cm:cmServiceProviders"],
    "qm": [".//oslc_qm_v1:qmServiceProviders", ".//oslc_qm:qmServiceProviders"],
}

# Query capability resource types per domain
QUERY_RESOURCE_TYPE = {
    "rm": "http://open-services.net/ns/rm#Requirement",
    "ccm": "http://open-services.net/ns/cm#ChangeRequest",
    "qm": "http://open-services.net/ns/qm#TestCase",
}


async def _get_xml(client: httpx.AsyncClient, url: str) -> ET.Element:
    """Fetch URL and parse as XML."""
    resp = await client.get(url, headers={"Accept": "application/rdf+xml, application/xml"})
    resp.raise_for_status()
    return ET.fromstring(resp.text)


async def _get_json(client: httpx.AsyncClient, url: str) -> dict:
    """Fetch URL as JSON (OSLC JSON response)."""
    resp = await client.get(url, headers={"Accept": "application/json", "OSLC-Core-Version": "2.0"})
    resp.raise_for_status()
    return resp.json()


async def get_catalog_url(domain: str) -> str:
    """Discover the service provider catalog URL from rootservices."""
    client = await get_client()
    root_url = f"{settings.elm_url}{DOMAIN_PATHS[domain]}"
    root = await _get_xml(client, root_url)
    for xpath in CATALOG_XPATH[domain]:
        elem = root.find(xpath, NS)
        if elem is not None:
            return elem.get(f"{{{NS['rdf']}}}resource")
    raise ValueError(f"Cannot find service provider catalog for domain '{domain}'")


async def list_service_providers(domain: str) -> list[dict]:
    """List all service providers (projects) for a domain."""
    import re

    client = await get_client()
    catalog_url = await get_catalog_url(domain)
    resp = await client.get(catalog_url, headers={"Accept": "application/rdf+xml, application/xml"})
    resp.raise_for_status()
    xml_text = resp.text
    providers = []

    # RM (Discovery 1.0): use regex directly — ET has issues in MCP stdio context
    if domain == "rm":
        entries = re.findall(
            r"<\w+:ServiceProvider>\s*"
            r"<(?:\w+:)?title>([^<]+)</(?:\w+:)?title>\s*.*?"
            r"<\w+:services\s+[^>]*rdf:resource=\"([^\"]+)\"",
            xml_text,
            re.DOTALL,
        )
        for title, svc_url in entries:
            providers.append({"title": title, "url": svc_url})
        return providers

    # CCM/QM: parse with ElementTree (OSLC Core namespace)
    catalog = ET.fromstring(xml_text)
    for sp in catalog.findall(".//{http://open-services.net/ns/core#}ServiceProvider"):
        title_el = sp.find("{http://purl.org/dc/terms/}title")
        about = sp.get(f"{{{NS['rdf']}}}about")
        if title_el is not None:
            providers.append({"title": title_el.text, "url": about})

    return providers


async def _find_query_base(domain: str, project_url: str) -> str:
    """Find the OSLC query base URL for a project's service provider."""
    client = await get_client()
    resource_type = QUERY_RESOURCE_TYPE[domain]

    # RM (DOORS Next): uses /views endpoint with projectURL parameter
    if domain == "rm" and project_url and "services.xml" in project_url:
        # Extract project ID from services.xml URL
        # Pattern: /rm/oslc_rm/{project_id}/services.xml
        parts = project_url.split("/")
        idx = parts.index("oslc_rm") if "oslc_rm" in parts else -1
        if idx >= 0 and idx + 1 < len(parts):
            project_id = parts[idx + 1]
            return (
                f"{settings.elm_url}/rm/views?oslc.query=true&projectURL={settings.elm_url}/rm/rm-projects/{project_id}"
            )

    # CCM/QM: derive services endpoint from catalog URL
    urls_to_try = []
    if project_url and not project_url.endswith("services.xml"):
        urls_to_try = [project_url.rstrip("/") + "/services", project_url]
    else:
        urls_to_try = [project_url.replace("/services.xml", "/services"), project_url]

    for url in urls_to_try:
        try:
            sp = await _get_xml(client, url)
        except (httpx.HTTPError, ET.ParseError) as exc:
            logger.debug("OSLC discovery: skipping %s (%s)", url, exc)
            continue
        for qc in sp.iter(f"{{{NS['oslc']}}}QueryCapability"):
            rt_el = qc.find(f"{{{NS['oslc']}}}resourceType")
            if rt_el is not None and rt_el.get(f"{{{NS['rdf']}}}resource") == resource_type:
                qb = qc.find(f"{{{NS['oslc']}}}queryBase")
                if qb is not None:
                    return qb.get(f"{{{NS['rdf']}}}resource")
        # Fallback: any queryBase
        for qc in sp.iter(f"{{{NS['oslc']}}}QueryCapability"):
            qb = qc.find(f"{{{NS['oslc']}}}queryBase")
            if qb is not None:
                return qb.get(f"{{{NS['rdf']}}}resource")

    raise ValueError(f"No query capability found for {domain} in project '{project_url}'")


async def _resolve_project_url(domain: str, project_name: str) -> str:
    """Resolve project name to service provider URL."""
    providers = await list_service_providers(domain)
    for p in providers:
        if p["title"] and p["title"].lower() == project_name.lower():
            return p["url"]
    available = [p["title"] for p in providers]
    raise ValueError(f"Project '{project_name}' not found. Available: {available}")


async def query_resources(domain: str, project: str, where: str | None = None, select: str | None = None) -> list[dict]:
    """Execute an OSLC query on a project, returning JSON results."""
    project_url = await _resolve_project_url(domain, project)
    query_base = await _find_query_base(domain, project_url)
    client = await get_client()
    params = {}
    if where:
        params["oslc.where"] = where
    if select:
        params["oslc.select"] = select
    params["oslc.pageSize"] = "50"

    # If query_base already has query params (e.g., RM /views?oslc.query=true&projectURL=...),
    # merge our params into the existing URL
    if "?" in query_base:
        from urllib.parse import parse_qs, urlparse, urlunparse

        parsed = urlparse(query_base)
        existing_params = parse_qs(parsed.query, keep_blank_values=True)
        # Flatten single-value lists
        merged = {k: v[0] if len(v) == 1 else v for k, v in existing_params.items()}
        merged.update(params)
        url = urlunparse(parsed._replace(query=""))
        params = merged
    else:
        url = query_base

    resp = await client.get(
        url,
        params=params,
        headers={"Accept": "application/json", "OSLC-Core-Version": "2.0"},
    )
    # Some domains (QM) don't support JSON — fallback to XML
    if resp.status_code == 406:
        resp = await client.get(
            url,
            params=params,
            headers={"Accept": "application/xml", "OSLC-Core-Version": "2.0"},
        )
        resp.raise_for_status()
        # Parse XML response into list of resource URIs
        from xml.etree import ElementTree as ET

        root = ET.fromstring(resp.text)
        results = []
        for member in root.iter(f"{{{NS['rdf']}}}Description"):
            about = member.get(f"{{{NS['rdf']}}}about")
            title_el = member.find("{http://purl.org/dc/terms/}title")
            entry = {"rdf:about": about}
            if title_el is not None:
                entry["dcterms:title"] = title_el.text
            results.append(entry)
        return results if results else [{"raw_xml": resp.text[:2000]}]

    resp.raise_for_status()
    data = resp.json()
    # OSLC JSON responses have members in rdfs:member or oslc:results
    return data.get("oslc:results", data.get("rdfs:member", data.get("results", [data])))


async def get_resource(uri: str) -> dict:
    """Fetch a single OSLC resource by URI."""
    client = await get_client()
    return await _get_json(client, uri)


async def _find_default_category(project_url: str) -> str | None:
    """Discover the default category (filedAgainst) for a CCM project area."""
    client = await get_client()
    # RTC exposes categories at /ccm/oslc/categories?projectArea={id}
    project_area_id = project_url.rstrip("/").split("/")[-1]
    categories_url = f"{settings.elm_url}/ccm/oslc/categories?projectArea={project_area_id}"
    try:
        resp = await client.get(
            categories_url,
            headers={"Accept": "application/json", "OSLC-Core-Version": "2.0"},
        )
        resp.raise_for_status()
        data = resp.json()
        # Categories are in the response; pick the first (default) one
        members = data.get("oslc:results", data.get("rdfs:member", []))
        if members and isinstance(members, list):
            first = members[0]
            # Return the rdf:about URI of the category
            return first.get("rdf:about", first.get("rdf:resource"))
    except Exception as exc:  # noqa: BLE001 — discovery is best-effort, degrade to None
        logger.debug("Iteration discovery failed: %s", exc)
    return None


async def _find_current_iteration(project_url: str) -> str | None:
    """Discover the current iteration (plannedFor) for a CCM project area.

    Finds the iteration whose date range contains today. Falls back to last iteration with dates.
    """
    from datetime import datetime, timezone

    client = await get_client()
    parts = project_url.split("/contexts/")
    project_area_id = parts[1].split("/")[0] if len(parts) > 1 else project_url.rstrip("/").split("/")[-1]
    iterations_url = f"{settings.elm_url}/ccm/oslc/iterations?projectArea={project_area_id}"
    try:
        resp = await client.get(
            iterations_url,
            headers={"Accept": "application/json", "OSLC-Core-Version": "2.0"},
        )
        resp.raise_for_status()
        members = resp.json().get("oslc:results", [])
        now = datetime.now(timezone.utc)
        candidates = []  # (uri, start_dt, has_end)
        for m in members:
            iter_uri = m.get("rdf:resource")
            if not iter_uri:
                continue
            detail = await client.get(iter_uri, headers={"Accept": "application/json", "OSLC-Core-Version": "2.0"})
            if detail.status_code != 200:
                continue
            d = detail.json()
            start = d.get("rtc_cm:startDate")
            end = d.get("rtc_cm:endDate")
            if not start:
                continue
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00")) if end else None
            is_current = start_dt <= now and (end_dt is None or now <= end_dt)
            if is_current:
                candidates.append((iter_uri, start_dt, end_dt is not None))
        if candidates:
            # Prefer: bounded (has end_date) > unbounded, then most recent start
            candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)
            return candidates[0][0]
        return None
    except Exception as exc:  # noqa: BLE001 — discovery is best-effort, degrade to None
        logger.debug("Iteration discovery failed: %s", exc)
    return None


def _payload_to_rdfxml(payload: dict) -> str:
    """Convert a payload dict to RDF/XML format for OSLC resource creation."""
    # Namespace prefixes used in payloads
    ns_map = {
        "dcterms": "http://purl.org/dc/terms/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "oslc_cm": "http://open-services.net/ns/cm#",
        "rtc_cm": "http://jazz.net/xmlns/prod/jazz/rtc/cm/1.0/",
        "rtc_ext": "http://jazz.net/xmlns/prod/jazz/rtc/ext/1.0/",
    }
    # Build namespace declarations
    ns_decls = " ".join(f'xmlns:{p}="{u}"' for p, u in ns_map.items())
    elements = []
    for key, value in payload.items():
        if isinstance(value, dict) and "rdf:resource" in value:
            elements.append(f'  <{key} rdf:resource="{value["rdf:resource"]}"/>')
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and "rdf:resource" in item:
                    elements.append(f'  <{key} rdf:resource="{item["rdf:resource"]}"/>')
        else:
            from xml.sax.saxutils import escape

            elements.append(f"  <{key}>{escape(str(value))}</{key}>")
    body = "\n".join(elements)
    return f"<rdf:RDF {ns_decls}>\n<oslc_cm:ChangeRequest>\n{body}\n</oslc_cm:ChangeRequest>\n</rdf:RDF>"


async def create_resource(domain: str, project: str, payload: dict, wi_type: str | None = None) -> dict:
    """POST a new resource (RDF/XML) to the creation factory."""
    if domain != "ccm":
        raise NotImplementedError(f"create_resource only supports 'ccm' domain, got '{domain}'")
    project_url = await _resolve_project_url(domain, project)
    # Extract projectAreaId from URL (may contain /workitems/services.xml suffix)
    parts = project_url.split("/contexts/")
    project_area_id = parts[1].split("/")[0] if len(parts) > 1 else project_url.rstrip("/").split("/")[-1]
    # Creation URL is always /workitems — the dc:type in payload differentiates WI type
    creation_url = f"{settings.elm_url}/ccm/oslc/contexts/{project_area_id}/workitems"
    client = await get_client()
    rdfxml_body = _payload_to_rdfxml(payload)
    # Refresh session (prevents CSRF stale after idle)
    await client.get(
        creation_url,
        headers={"Accept": "application/json", "OSLC-Core-Version": "2.0"},
    )
    post_headers = {
        "Content-Type": "application/rdf+xml",
        "Accept": "application/json",
        "OSLC-Core-Version": "2.0",
    }
    resp = await client.post(creation_url, content=rdfxml_body, headers=post_headers)
    if resp.status_code in (401, 403) or "j_security_check" in str(resp.headers.get("location", "")):
        from .auth import _authenticate

        await _authenticate(client)
        resp = await client.post(creation_url, content=rdfxml_body, headers=post_headers)
    if resp.status_code != 201:
        resp.raise_for_status()
        raise RuntimeError(f"Expected 201 Created, got {resp.status_code}")
    return resp.json()


async def update_resource(uri: str, payload: dict) -> dict:
    """PUT updated fields to an existing resource (with ETag)."""
    client = await get_client()
    # GET full resource to obtain ETag and current state
    get_resp = await client.get(uri, headers={"Accept": "application/json", "OSLC-Core-Version": "2.0"})
    get_resp.raise_for_status()
    etag = get_resp.headers.get("ETag", "")
    if not etag:
        raise ValueError(f"Server did not return an ETag for resource '{uri}'. Cannot safely update.")
    # Merge payload into full resource
    current = get_resp.json()
    merged = {**current, **payload}
    # PUT with If-Match
    resp = await client.put(
        uri,
        json=merged,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "OSLC-Core-Version": "2.0",
            "If-Match": etag,
        },
    )
    resp.raise_for_status()
    return resp.json()


# =====================================================================
# RM (DOORS Next) write path — ADDITIVE (G0-rm-write.md §E).
# Fully separate from the CCM create_resource/_payload_to_rdfxml path to
# avoid regression on the single write gargalo of CCM. Uses regex (not ET)
# for RM discovery — ET fails in the MCP stdio context (memória 0c1b2aa4).
# =====================================================================

import re as _re  # local alias for the RM regex path, kept out of CCM code
from xml.sax.saxutils import escape as _xml_escape

# RM-specific namespaces (jazz_rm:primaryText, nav:parent). Additive to NS.
NS["jazz_rm"] = "http://jazz.net/ns/rm#"
NS["nav"] = "http://jazz.net/ns/rm/navigation#"

# RDF/XML namespace block for RM requirement bodies (own block — does NOT touch
# the CCM _payload_to_rdfxml ns_map).
_RM_NS_DECLS = (
    'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
    'xmlns:dcterms="http://purl.org/dc/terms/" '
    'xmlns:oslc="http://open-services.net/ns/core#" '
    'xmlns:oslc_rm="http://open-services.net/ns/rm#" '
    'xmlns:jazz_rm="http://jazz.net/ns/rm#" '
    'xmlns:nav="http://jazz.net/ns/rm/navigation#"'
)

_RM_REQUIREMENT_TYPE = "http://open-services.net/ns/rm#Requirement"


def sanitize_html_to_xhtml(html: str) -> str:
    """Convert HTML to XHTML valid for the RM primaryText.

    Mirrors publicar_elm.sanitizar_html (G0 §E pt.4): strip html/head/body/meta
    wrappers, close void tags (br/hr/img/input), escape lone ampersands without
    double-escaping existing entities, and drop emojis that break the ALM XML.
    """
    if not html:
        return ""
    content = html
    # Remove html/head/body/meta wrappers
    content = _re.sub(r"<html[^>]*>", "", content, flags=_re.IGNORECASE)
    content = _re.sub(r"</html>", "", content, flags=_re.IGNORECASE)
    content = _re.sub(r"<head[^>]*>.*?</head>", "", content, flags=_re.IGNORECASE | _re.DOTALL)
    content = _re.sub(r"<body[^>]*>", "", content, flags=_re.IGNORECASE)
    content = _re.sub(r"</body>", "", content, flags=_re.IGNORECASE)
    content = _re.sub(r"<meta[^>]*/?>", "", content, flags=_re.IGNORECASE)
    # Close void tags for XHTML
    content = _re.sub(r"<hr\s*/?>", "<hr/>", content, flags=_re.IGNORECASE)
    content = _re.sub(r"<br\s*/?>", "<br/>", content, flags=_re.IGNORECASE)
    content = _re.sub(r"<img([^>]*?)/?>", r"<img\1/>", content, flags=_re.IGNORECASE)
    content = _re.sub(r"<input([^>]*?)/?>", r"<input\1/>", content, flags=_re.IGNORECASE)
    # Escape lone ampersands (not already-encoded entities) — no double-escape
    content = _re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)", "&amp;", content)
    # Drop emojis (break ALM XML)
    content = _re.sub(r"[\U0001F600-\U0001F9FF]", "", content)
    content = _re.sub(r"[\u2600-\u27BF]", "", content)
    content = _re.sub(r"[\U0001FA00-\U0001FA6F]", "", content)
    content = _re.sub(r"[\U0001F300-\U0001F5FF]", "", content)
    return content.strip()


async def _find_requirement_factory(project_url: str) -> str:
    """Discover the RM CreationFactory URL (oslc:creation) for a service provider.

    Mirrors publicar_elm.descobrir_creation_factory: finds the CreationFactory
    whose oslc:resourceType is rm#Requirement and returns its oslc:creation URI.
    Uses regex (not ElementTree) — ET fails in the MCP stdio context.
    """
    client = await get_client()
    resp = await client.get(
        project_url,
        headers={"Accept": "application/rdf+xml, application/xml", "OSLC-Core-Version": "2.0"},
    )
    resp.raise_for_status()
    xml_text = resp.text

    # Match each CreationFactory block, then pick the one whose resourceType is
    # EXACTLY rm#Requirement — not a substring match, which would also accept
    # rm#RequirementCollection (DOORS Next exposes both). Mistake note ed14f77c.
    for block in _re.findall(r"<\w*:?CreationFactory\b.*?</\w*:?CreationFactory>", xml_text, _re.DOTALL):
        rt = _re.search(r"<\w*:?resourceType\s+[^>]*rdf:resource=\"([^\"]+)\"", block)
        if rt is None or rt.group(1) != _RM_REQUIREMENT_TYPE:
            continue
        m = _re.search(r"<\w*:?creation\s+[^>]*rdf:resource=\"([^\"]+)\"", block)
        if m:
            return m.group(1)
    raise ValueError(f"RM CreationFactory for Requirement not found in '{project_url}'")


def _assert_xhtml_wellformed(xhtml: str) -> None:
    """Reject XHTML content that is not well-formed, to prevent it from breaking
    out of the jazz_rm:primaryText literal (XML injection). The content goes in
    non-escaped (parseType="Literal"), so a stray </jazz_rm:primaryText> or
    unbalanced tag could inject sibling structure. Parse it in isolation first.
    """
    if not xhtml:
        return
    fragment = f'<div xmlns="http://www.w3.org/1999/xhtml">{xhtml}</div>'
    try:
        ET.fromstring(fragment)
    except ET.ParseError as exc:
        raise ValueError(f"requirement content is not well-formed XHTML: {exc}") from exc


def _requirement_to_rdfxml(title: str, xhtml: str, shape: str | None = None, folder: str | None = None) -> str:
    """Build the RM requirement RDF/XML body.

    The XHTML is embedded NON-escaped inside jazz_rm:primaryText with
    rdf:parseType="Literal" (different from the CCM _payload_to_rdfxml, which
    escapes everything). Title is escaped (it is plain text, not markup).
    The XHTML must be well-formed (checked by the caller) so it cannot break out
    of the literal.
    """
    shape_tag = f'    <oslc:instanceShape rdf:resource="{shape}"/>\n' if shape else ""
    folder_tag = f'    <nav:parent rdf:resource="{folder}"/>\n' if folder else ""
    primary_text = ""
    if xhtml:
        primary_text = (
            '    <jazz_rm:primaryText rdf:parseType="Literal">'
            '<div xmlns="http://www.w3.org/1999/xhtml">'
            f"{xhtml}</div></jazz_rm:primaryText>\n"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f"<rdf:RDF {_RM_NS_DECLS}>\n"
        '  <rdf:Description rdf:about="">\n'
        f'    <rdf:type rdf:resource="{_RM_REQUIREMENT_TYPE}"/>\n'
        f"    <dcterms:title>{_xml_escape(title)}</dcterms:title>\n"
        f"{shape_tag}"
        f"{primary_text}"
        f"{folder_tag}"
        "  </rdf:Description>\n"
        "</rdf:RDF>"
    )


def _extract_identifier(xml_text: str) -> str | None:
    """Pull dcterms:identifier out of an RM response body (regex)."""
    if not xml_text:
        return None
    m = _re.search(r"<\w*:?identifier[^>]*>([^<]+)</\w*:?identifier>", xml_text)
    return m.group(1) if m else None


async def create_requirement(
    project: str, title: str, xhtml: str, folder: str | None = None, shape: str | None = None
) -> dict:
    """Create an RM requirement via OSLC POST to the requirementFactory.

    Resolves the project, discovers the factory, sanitizes nothing here (the
    caller passes already-sanitized XHTML), builds the RDF/XML, and POSTs it
    (Accept/Content-Type application/rdf+xml). Accepts 200 or 201. Retries once
    on 401/403 after a session refresh (same pattern as create_resource).
    Returns {"uri": ..., "identifier": ...}. Raises ValueError if the project
    does not exist (propagated from _resolve_project_url).
    """
    project_url = await _resolve_project_url("rm", project)
    factory_url = await _find_requirement_factory(project_url)
    _assert_xhtml_wellformed(xhtml)
    rdf_body = _requirement_to_rdfxml(title, xhtml, shape=shape, folder=folder)
    client = await get_client()
    post_headers = {
        "Content-Type": "application/rdf+xml",
        "Accept": "application/rdf+xml",
        "OSLC-Core-Version": "2.0",
    }
    resp = await client.post(factory_url, content=rdf_body.encode("utf-8"), headers=post_headers)
    if resp.status_code in (401, 403) or "j_security_check" in str(resp.headers.get("location", "")):
        from .auth import _authenticate

        await _authenticate(client)
        resp = await client.post(factory_url, content=rdf_body.encode("utf-8"), headers=post_headers)
    if resp.status_code not in (200, 201):
        resp.raise_for_status()
        raise RuntimeError(f"Expected 200/201 Created, got {resp.status_code}")
    location = resp.headers.get("Location", "")
    identifier = _extract_identifier(resp.text)
    return {"uri": location, "identifier": identifier}


async def update_requirement(uri: str, title: str | None = None, xhtml: str | None = None) -> dict:
    """Update an RM requirement via OSLC PUT with If-Match (ETag).

    GETs the resource as rdf+xml for its ETag, edits the XML as a string
    preserving parseType="Literal" (mirrors publicar_elm.atualizar_requisito),
    then PUTs with If-Match. Accepts 200/204. On 412 raises ValueError signalling
    an ETag conflict (the @tool boundary converts it to a legible ToolError).
    """
    client = await get_client()
    get_resp = await client.get(
        uri, headers={"Accept": "application/rdf+xml, application/xml", "OSLC-Core-Version": "2.0"}
    )
    get_resp.raise_for_status()
    etag = get_resp.headers.get("ETag", "")
    if not etag:
        raise ValueError(f"Server did not return an ETag for resource '{uri}'. Cannot safely update.")
    xml_content = get_resp.text
    if xhtml is not None:
        _assert_xhtml_wellformed(sanitize_html_to_xhtml(xhtml))

    # Edit ONLY inside the target resource's <rdf:Description> block, not the
    # first/any match in the whole document (a GET may return several Descriptions
    # — linked resources, folders). Anchor on rdf:about matching the uri; fall
    # back to the first Description if the server omits/abbreviates rdf:about.
    desc_re = _re.compile(
        r'(<\w*:?Description\b[^>]*rdf:about="' + _re.escape(uri) + r'"[^>]*>)(.*?)(</\w*:?Description>)',
        _re.DOTALL,
    )
    m = desc_re.search(xml_content)
    if m is None:
        desc_re = _re.compile(r"(<\w*:?Description\b[^>]*>)(.*?)(</\w*:?Description>)", _re.DOTALL)
        m = desc_re.search(xml_content)
    if m is None:
        raise ValueError(f"could not locate the requirement's rdf:Description in '{uri}'")

    open_tag, body, close_tag = m.group(1), m.group(2), m.group(3)

    if title is not None:
        body = _re.sub(
            r"(<\w*:?title[^>]*>)(.*?)(</\w*:?title>)",
            lambda t: t.group(1) + _xml_escape(title) + t.group(3),
            body,
            count=1,
            flags=_re.DOTALL,
        )

    if xhtml is not None:
        clean = sanitize_html_to_xhtml(xhtml)
        primary_content = f'<div xmlns="http://www.w3.org/1999/xhtml">{clean}</div>'
        if "jazz_rm:primaryText" in body:
            body = _re.sub(
                r"(<jazz_rm:primaryText[^>]*>)(.*?)(</jazz_rm:primaryText>)",
                lambda t: t.group(1) + primary_content + t.group(3),
                body,
                count=1,
                flags=_re.DOTALL,
            )
        else:
            primary_tag = f'<jazz_rm:primaryText rdf:parseType="Literal">{primary_content}</jazz_rm:primaryText>'
            body = body + f"    {primary_tag}\n  "

    xml_content = xml_content[: m.start()] + open_tag + body + close_tag + xml_content[m.end() :]

    put_resp = await client.put(
        uri,
        content=xml_content.encode("utf-8"),
        headers={
            "Content-Type": "application/rdf+xml",
            "Accept": "application/rdf+xml",
            "OSLC-Core-Version": "2.0",
            "If-Match": etag,
        },
    )
    if put_resp.status_code == 412:
        raise ValueError("conflito de ETag: o requisito foi alterado por outro cliente; recarregue e tente novamente")
    if put_resp.status_code not in (200, 204):
        put_resp.raise_for_status()
        raise RuntimeError(f"Expected 200/204, got {put_resp.status_code}")
    return {"uri": uri, "identifier": _extract_identifier(put_resp.text)}
