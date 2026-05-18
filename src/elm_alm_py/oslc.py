"""OSLC service discovery and query builder for IBM ELM."""

from xml.etree import ElementTree as ET

import httpx

from .auth import get_client
from .config import settings

# OSLC XML namespaces
NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "oslc": "http://open-services.net/ns/core#",
    "oslc_rm": "http://open-services.net/ns/rm#",
    "oslc_cm": "http://open-services.net/ns/cm#",
    "oslc_qm": "http://open-services.net/ns/qm#",
    "dcterms": "http://purl.org/dc/terms/",
    "jfs": "http://jazz.net/xmlns/prod/jazz/jfs/1.0/",
}

DOMAIN_PATHS = {
    "rm": "/rm/rootservices",
    "ccm": "/ccm/rootservices",
    "qm": "/qm/rootservices",
}

# Catalog discovery XPath per domain
CATALOG_XPATH = {
    "rm": ".//oslc_rm:rmServiceProviders",
    "ccm": ".//oslc_cm:cmServiceProviders",
    "qm": ".//oslc_qm:qmServiceProviders",
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
    elem = root.find(CATALOG_XPATH[domain], NS)
    if elem is None:
        raise ValueError(f"Cannot find service provider catalog for domain '{domain}'")
    return elem.get(f"{{{NS['rdf']}}}resource")


async def list_service_providers(domain: str) -> list[dict]:
    """List all service providers (projects) for a domain."""
    client = await get_client()
    catalog_url = await get_catalog_url(domain)
    catalog = await _get_xml(client, catalog_url)
    providers = []
    for sp in catalog.findall(".//{http://open-services.net/ns/core#}ServiceProvider"):
        title_el = sp.find("{http://purl.org/dc/terms/}title")
        about = sp.get(f"{{{NS['rdf']}}}about")
        if title_el is not None:
            providers.append({"title": title_el.text, "url": about})
    return providers


async def _find_query_base(domain: str, project_url: str) -> str:
    """Find the OSLC query base URL for a project's service provider."""
    client = await get_client()
    sp = await _get_xml(client, project_url)
    resource_type = QUERY_RESOURCE_TYPE[domain]
    # Look for queryBase in services matching our resource type
    for svc in sp.iter(f"{{{NS['oslc']}}}service"):
        for qc in svc.iter(f"{{{NS['oslc']}}}QueryCapability"):
            rt_el = qc.find(f"{{{NS['oslc']}}}resourceType")
            if rt_el is not None and rt_el.get(f"{{{NS['rdf']}}}resource") == resource_type:
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
    resp = await client.get(
        query_base,
        params=params,
        headers={"Accept": "application/json", "OSLC-Core-Version": "2.0"},
    )
    resp.raise_for_status()
    data = resp.json()
    # OSLC JSON responses have members in rdfs:member or oslc:results
    return data.get("oslc:results", data.get("rdfs:member", data.get("results", [data])))


async def get_resource(uri: str) -> dict:
    """Fetch a single OSLC resource by URI."""
    client = await get_client()
    return await _get_json(client, uri)
