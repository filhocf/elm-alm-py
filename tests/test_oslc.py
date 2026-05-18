"""Tests for OSLC service discovery and queries."""

import pytest
import httpx
import respx

from elm_alm_py import oslc
from elm_alm_py.auth import close_client

ROOTSERVICES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rdf:Description xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:oslc_rm="http://open-services.net/ns/rm#">
    <oslc_rm:rmServiceProviders
        rdf:resource="https://www-elm.prevnet/rm/oslc_rm/catalog"/>
</rdf:Description>
"""

CATALOG_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:oslc="http://open-services.net/ns/core#"
    xmlns:dcterms="http://purl.org/dc/terms/">
    <oslc:ServiceProviderCatalog>
        <oslc:serviceProvider>
            <oslc:ServiceProvider rdf:about="https://www-elm.prevnet/rm/oslc_rm/sp/1">
                <dcterms:title>My Project</dcterms:title>
            </oslc:ServiceProvider>
        </oslc:serviceProvider>
    </oslc:ServiceProviderCatalog>
</rdf:RDF>
"""


@pytest.fixture(autouse=True)
async def cleanup():
    yield
    await close_client()


@respx.mock
async def test_get_catalog_url(monkeypatch):
    respx.post("https://www-elm.prevnet/auth/j_security_check").mock(return_value=httpx.Response(200))
    respx.get("https://www-elm.prevnet/rm/rootservices").mock(return_value=httpx.Response(200, text=ROOTSERVICES_XML))
    url = await oslc.get_catalog_url("rm")
    assert url == "https://www-elm.prevnet/rm/oslc_rm/catalog"


@respx.mock
async def test_list_service_providers():
    respx.post("https://www-elm.prevnet/auth/j_security_check").mock(return_value=httpx.Response(200))
    respx.get("https://www-elm.prevnet/rm/rootservices").mock(return_value=httpx.Response(200, text=ROOTSERVICES_XML))
    respx.get("https://www-elm.prevnet/rm/oslc_rm/catalog").mock(return_value=httpx.Response(200, text=CATALOG_XML))
    providers = await oslc.list_service_providers("rm")
    assert len(providers) == 1
    assert providers[0]["title"] == "My Project"
    assert providers[0]["url"] == "https://www-elm.prevnet/rm/oslc_rm/sp/1"
