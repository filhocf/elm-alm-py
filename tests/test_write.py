"""Tests for write operations (create/update work items)."""

import pytest
import httpx
import respx

from elm_alm_py import oslc
from elm_alm_py.auth import close_client
from elm_alm_py.server import create_workitem, update_workitem, add_child_workitem

BASE = "https://elm.example.com"

CCM_ROOTSERVICES_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<rdf:Description xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:oslc_cm="http://open-services.net/xmlns/cm/1.0/">
    <oslc_cm:cmServiceProviders
        rdf:resource="{BASE}/ccm/oslc/workitems/catalog"/>
</rdf:Description>
"""

CCM_CATALOG_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:oslc="http://open-services.net/ns/core#"
    xmlns:dcterms="http://purl.org/dc/terms/">
    <oslc:ServiceProvider rdf:about="{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g">
        <dcterms:title>MEU IMOVEL RURAL (MIR)</dcterms:title>
    </oslc:ServiceProvider>
</rdf:RDF>
"""

CCM_SERVICES_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:oslc="http://open-services.net/ns/core#">
    <oslc:CreationFactory>
        <oslc:resourceType rdf:resource="http://open-services.net/ns/cm#ChangeRequest"/>
        <oslc:creation rdf:resource="{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/workitems"/>
    </oslc:CreationFactory>
</rdf:RDF>
"""

CREATED_WI = {
    "dcterms:title": "New Task",
    "dcterms:identifier": "42",
    "rdf:about": f"{BASE}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/42",
}


@pytest.fixture(autouse=True)
async def cleanup(monkeypatch):
    monkeypatch.setattr("elm_alm_py.config.settings.elm_url", BASE)
    yield
    await close_client()


def _mock_auth():
    respx.post(f"{BASE}/jts/j_security_check").mock(return_value=httpx.Response(200))


def _mock_ccm_discovery():
    _mock_auth()
    respx.get(f"{BASE}/ccm/rootservices").mock(return_value=httpx.Response(200, text=CCM_ROOTSERVICES_XML))
    respx.get(f"{BASE}/ccm/oslc/workitems/catalog").mock(return_value=httpx.Response(200, text=CCM_CATALOG_XML))
    respx.get(f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/services").mock(
        return_value=httpx.Response(200, text=CCM_SERVICES_XML)
    )


@respx.mock
async def test_find_creation_factory():
    _mock_ccm_discovery()
    project_url = f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g"
    url = await oslc._find_creation_factory("ccm", project_url)
    assert url == f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/workitems"


@respx.mock
async def test_create_resource():
    _mock_ccm_discovery()
    respx.post(f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/workitems").mock(
        return_value=httpx.Response(201, json=CREATED_WI)
    )
    result = await oslc.create_resource("ccm", "MEU IMOVEL RURAL (MIR)", {"dcterms:title": "New Task"})
    assert result["dcterms:identifier"] == "42"


@respx.mock
async def test_update_resource():
    _mock_auth()
    uri = f"{BASE}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/42"
    respx.get(uri).mock(return_value=httpx.Response(200, json=CREATED_WI, headers={"ETag": '"abc123"'}))
    updated = {**CREATED_WI, "dcterms:title": "Updated Title"}
    respx.put(uri).mock(return_value=httpx.Response(200, json=updated))
    result = await oslc.update_resource(uri, {"dcterms:title": "Updated Title"})
    assert result["dcterms:title"] == "Updated Title"


@respx.mock
async def test_create_workitem_tool():
    _mock_ccm_discovery()
    respx.post(f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/workitems").mock(
        return_value=httpx.Response(201, json=CREATED_WI)
    )
    result = await create_workitem(project="MEU IMOVEL RURAL (MIR)", title="New Task", type="task")
    assert result["dcterms:identifier"] == "42"


@respx.mock
async def test_create_workitem_with_parent():
    _mock_ccm_discovery()
    respx.post(f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/workitems").mock(
        return_value=httpx.Response(201, json=CREATED_WI)
    )
    result = await create_workitem(project="MEU IMOVEL RURAL (MIR)", title="Child Task", type="task", parent_id="10")
    assert result["dcterms:identifier"] == "42"


@respx.mock
async def test_update_workitem_tool():
    _mock_auth()
    uri = f"{BASE}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/42"
    respx.get(uri).mock(return_value=httpx.Response(200, json=CREATED_WI, headers={"ETag": '"etag1"'}))
    updated = {**CREATED_WI, "dcterms:title": "New Title"}
    respx.put(uri).mock(return_value=httpx.Response(200, json=updated))
    result = await update_workitem(id="42", title="New Title")
    assert result["dcterms:title"] == "New Title"


@respx.mock
async def test_add_child_workitem_tool():
    _mock_ccm_discovery()
    respx.post(f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/workitems").mock(
        return_value=httpx.Response(201, json=CREATED_WI)
    )
    result = await add_child_workitem(parent_id="10", title="Sub-task")
    assert result["dcterms:identifier"] == "42"


async def test_create_workitem_invalid_type():
    with pytest.raises(ValueError, match="Invalid type"):
        await create_workitem(project="MIR", title="X", type="epic")


async def test_update_workitem_no_fields():
    with pytest.raises(ValueError, match="At least one field"):
        await update_workitem(id="1")


@respx.mock
async def test_create_resource_post_400():
    _mock_ccm_discovery()
    respx.post(f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/workitems").mock(
        return_value=httpx.Response(400, text="Bad Request")
    )
    with pytest.raises(httpx.HTTPStatusError):
        await oslc.create_resource("ccm", "MEU IMOVEL RURAL (MIR)", {"dcterms:title": "X"})


@respx.mock
async def test_create_resource_post_401():
    _mock_ccm_discovery()
    respx.post(f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/workitems").mock(
        return_value=httpx.Response(401, text="Unauthorized")
    )
    with pytest.raises(httpx.HTTPStatusError):
        await oslc.create_resource("ccm", "MEU IMOVEL RURAL (MIR)", {"dcterms:title": "X"})


@respx.mock
async def test_update_resource_put_409():
    _mock_auth()
    uri = f"{BASE}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/99"
    respx.get(uri).mock(return_value=httpx.Response(200, json=CREATED_WI, headers={"ETag": '"e1"'}))
    respx.put(uri).mock(return_value=httpx.Response(409, text="Conflict"))
    with pytest.raises(httpx.HTTPStatusError):
        await oslc.update_resource(uri, {"dcterms:title": "X"})


@respx.mock
async def test_update_resource_put_412():
    _mock_auth()
    uri = f"{BASE}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/99"
    respx.get(uri).mock(return_value=httpx.Response(200, json=CREATED_WI, headers={"ETag": '"e1"'}))
    respx.put(uri).mock(return_value=httpx.Response(412, text="Precondition Failed"))
    with pytest.raises(httpx.HTTPStatusError):
        await oslc.update_resource(uri, {"dcterms:title": "X"})


@respx.mock
async def test_update_resource_no_etag():
    _mock_auth()
    uri = f"{BASE}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/99"
    respx.get(uri).mock(return_value=httpx.Response(200, json=CREATED_WI))
    with pytest.raises(ValueError, match="did not return an ETag"):
        await oslc.update_resource(uri, {"dcterms:title": "X"})


@respx.mock
async def test_creation_factory_not_found():
    _mock_auth()
    respx.get(f"{BASE}/ccm/rootservices").mock(return_value=httpx.Response(200, text=CCM_ROOTSERVICES_XML))
    respx.get(f"{BASE}/ccm/oslc/workitems/catalog").mock(return_value=httpx.Response(200, text=CCM_CATALOG_XML))
    # Return services XML with no CreationFactory
    empty_services = '<?xml version="1.0"?><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"></rdf:RDF>'
    respx.get(f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/services").mock(
        return_value=httpx.Response(200, text=empty_services)
    )
    with pytest.raises(ValueError, match="No creation factory found"):
        await oslc.create_resource("ccm", "MEU IMOVEL RURAL (MIR)", {"dcterms:title": "X"})


async def test_create_resource_non_ccm_domain():
    with pytest.raises(NotImplementedError, match="only supports 'ccm'"):
        await oslc.create_resource("rm", "SomeProject", {"dcterms:title": "X"})
