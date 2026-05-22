"""Tests for OSLC service discovery and queries."""

import pytest
import httpx
import respx

from elm_alm_py import oslc
from elm_alm_py.auth import close_client

BASE = "https://elm.example.com"

ROOTSERVICES_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<rdf:Description xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:oslc_rm="http://open-services.net/ns/rm#">
    <oslc_rm:rmServiceProviders
        rdf:resource="{BASE}/rm/oslc_rm/catalog"/>
</rdf:Description>
"""

CATALOG_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<oslc_disc:ServiceProviderCatalog
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:dcterms="http://purl.org/dc/terms/"
    xmlns:oslc_disc="http://open-services.net/xmlns/discovery/1.0/"
    rdf:about="{BASE}/rm/oslc_rm/catalog">
    <dcterms:title>RMCatalog</dcterms:title>
    <oslc_disc:entry>
        <oslc_disc:ServiceProvider>
            <dcterms:title>My Project</dcterms:title>
            <oslc_disc:services rdf:resource="{BASE}/rm/oslc_rm/_abc123/services.xml"/>
        </oslc_disc:ServiceProvider>
    </oslc_disc:entry>
</oslc_disc:ServiceProviderCatalog>
"""


@pytest.fixture(autouse=True)
async def cleanup(monkeypatch):
    monkeypatch.setattr("elm_alm_py.config.settings.elm_url", BASE)
    yield
    await close_client()


@respx.mock
async def test_get_catalog_url():
    respx.post(f"{BASE}/jts/j_security_check").mock(return_value=httpx.Response(200))
    respx.get(f"{BASE}/rm/rootservices").mock(return_value=httpx.Response(200, text=ROOTSERVICES_XML))
    url = await oslc.get_catalog_url("rm")
    assert url == f"{BASE}/rm/oslc_rm/catalog"


@respx.mock
async def test_list_service_providers():
    respx.post(f"{BASE}/jts/j_security_check").mock(return_value=httpx.Response(200))
    respx.get(f"{BASE}/rm/rootservices").mock(return_value=httpx.Response(200, text=ROOTSERVICES_XML))
    respx.get(f"{BASE}/rm/oslc_rm/catalog").mock(return_value=httpx.Response(200, text=CATALOG_XML))
    providers = await oslc.list_service_providers("rm")
    assert len(providers) == 1
    assert providers[0]["title"] == "My Project"
    assert providers[0]["url"] == f"{BASE}/rm/oslc_rm/_abc123/services.xml"
