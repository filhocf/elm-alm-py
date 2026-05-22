"""OSLC service discovery and query builder for IBM ELM."""

from xml.etree import ElementTree as ET

import httpx

from .auth import get_client
from .config import settings

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
        except Exception:
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


async def query_resources(domain: str, project: str, where: str | None = None) -> list[dict]:
    """Execute an OSLC query on a project, returning JSON results."""
    project_url = await _resolve_project_url(domain, project)
    query_base = await _find_query_base(domain, project_url)
    client = await get_client()
    params = {}
    if where:
        params["oslc.where"] = where
    params["oslc.pageSize"] = "50"

    # If query_base already has query params (e.g., RM /views?oslc.query=true&projectURL=...),
    # merge our params into the existing URL
    if "?" in query_base:
        from urllib.parse import urlparse, parse_qs, urlunparse

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
    except Exception:
        pass
    return None


async def _find_creation_factory(domain: str, project_url: str, wi_type: str | None = None) -> str:
    """Find the OSLC CreationFactory URL for a project, optionally filtering by work item type."""
    client = await get_client()
    resource_type = QUERY_RESOURCE_TYPE[domain]

    urls_to_try = []
    if project_url and not project_url.endswith("services.xml"):
        urls_to_try = [project_url.rstrip("/") + "/services", project_url]
    else:
        urls_to_try = [project_url.replace("/services.xml", "/services"), project_url]

    for url in urls_to_try:
        try:
            sp = await _get_xml(client, url)
        except Exception:
            continue

        # Collect all matching creation factories
        generic_factory = None
        for cf in sp.iter(f"{{{NS['oslc']}}}CreationFactory"):
            rt_el = cf.find(f"{{{NS['oslc']}}}resourceType")
            if rt_el is None or rt_el.get(f"{{{NS['rdf']}}}resource") != resource_type:
                continue
            creation = cf.find(f"{{{NS['oslc']}}}creation")
            if creation is None:
                continue
            factory_url = creation.get(f"{{{NS['rdf']}}}resource")
            # If a specific type is requested, check title match
            if wi_type:
                title_el = cf.find(f"{{{NS['dcterms']}}}title")
                if title_el is not None and title_el.text and wi_type.lower() in title_el.text.lower():
                    return factory_url
            if generic_factory is None:
                generic_factory = factory_url

        if generic_factory:
            return generic_factory

        # Fallback: any creation factory
        for cf in sp.iter(f"{{{NS['oslc']}}}CreationFactory"):
            creation = cf.find(f"{{{NS['oslc']}}}creation")
            if creation is not None:
                return creation.get(f"{{{NS['rdf']}}}resource")

    raise ValueError(f"No creation factory found for {domain} in project '{project_url}'")


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
    creation_url = await _find_creation_factory(domain, project_url, wi_type=wi_type)
    client = await get_client()
    rdfxml_body = _payload_to_rdfxml(payload)
    resp = await client.post(
        creation_url,
        content=rdfxml_body,
        headers={
            "Content-Type": "application/rdf+xml",
            "Accept": "application/json",
            "OSLC-Core-Version": "2.0",
        },
    )
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
