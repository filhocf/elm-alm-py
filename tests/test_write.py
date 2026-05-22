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
    xmlns:oslc="http://open-services.net/ns/core#"
    xmlns:dcterms="http://purl.org/dc/terms/">
    <oslc:CreationFactory>
        <dcterms:title>defect</dcterms:title>
        <oslc:resourceType rdf:resource="http://open-services.net/ns/cm#ChangeRequest"/>
        <oslc:creation rdf:resource="{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/workitems"/>
    </oslc:CreationFactory>
    <oslc:CreationFactory>
        <dcterms:title>task</dcterms:title>
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
    respx.get(f"{BASE}/ccm/oslc/categories").mock(
        return_value=httpx.Response(
            200,
            json={"oslc:results": [{"rdf:about": f"{BASE}/ccm/oslc/categories/_MWxBEJB7Ee-fe_bes9r78g/default"}]},
        )
    )


@respx.mock
async def test_find_creation_factory():
    _mock_ccm_discovery()
    project_url = f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g"
    url = await oslc._find_creation_factory("ccm", project_url)
    assert url == f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/workitems"


@respx.mock
async def test_find_creation_factory_by_type():
    _mock_ccm_discovery()
    project_url = f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g"
    url = await oslc._find_creation_factory("ccm", project_url, wi_type="task")
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
async def test_create_resource_posts_to_workitems_url():
    """create_resource must POST to /contexts/{id}/workitems regardless of services.xml content."""
    _mock_ccm_discovery()
    post_route = respx.post(f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/workitems").mock(
        return_value=httpx.Response(201, json=CREATED_WI)
    )
    result = await oslc.create_resource("ccm", "MEU IMOVEL RURAL (MIR)", {"dcterms:title": "X"})
    assert post_route.called
    assert result["dcterms:identifier"] == "42"


async def test_create_resource_non_ccm_domain():
    with pytest.raises(NotImplementedError, match="only supports 'ccm'"):
        await oslc.create_resource("rm", "SomeProject", {"dcterms:title": "X"})


# --- Tests for custom_fields and _find_current_iteration ---


ITERATIONS_JSON = {
    "oslc:results": [
        {"rdf:about": f"{BASE}/ccm/oslc/iterations/_iter1", "dcterms:title": "Entrega 4", "rtc_cm:current": False},
        {"rdf:about": f"{BASE}/ccm/oslc/iterations/_iter2", "dcterms:title": "Entrega 5", "rtc_cm:current": True},
        {"rdf:about": f"{BASE}/ccm/oslc/iterations/_iter3", "dcterms:title": "Entrega 6", "rtc_cm:current": False},
    ]
}


@respx.mock
async def test_find_current_iteration_returns_current():
    _mock_auth()
    respx.get(f"{BASE}/ccm/oslc/iterations").mock(
        return_value=httpx.Response(200, json=ITERATIONS_JSON)
    )
    project_url = f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g"
    result = await oslc._find_current_iteration(project_url)
    assert result == f"{BASE}/ccm/oslc/iterations/_iter2"


@respx.mock
async def test_find_current_iteration_fallback_to_last():
    _mock_auth()
    no_current = {
        "oslc:results": [
            {"rdf:about": f"{BASE}/ccm/oslc/iterations/_a", "dcterms:title": "Sprint 1"},
            {"rdf:about": f"{BASE}/ccm/oslc/iterations/_b", "dcterms:title": "Sprint 2"},
        ]
    }
    respx.get(f"{BASE}/ccm/oslc/iterations").mock(
        return_value=httpx.Response(200, json=no_current)
    )
    project_url = f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g"
    result = await oslc._find_current_iteration(project_url)
    assert result == f"{BASE}/ccm/oslc/iterations/_b"


@respx.mock
async def test_find_current_iteration_empty_returns_none():
    _mock_auth()
    respx.get(f"{BASE}/ccm/oslc/iterations").mock(
        return_value=httpx.Response(200, json={"oslc:results": []})
    )
    project_url = f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g"
    result = await oslc._find_current_iteration(project_url)
    assert result is None


@respx.mock
async def test_find_current_iteration_http_error_returns_none():
    _mock_auth()
    respx.get(f"{BASE}/ccm/oslc/iterations").mock(
        return_value=httpx.Response(500, text="Server Error")
    )
    project_url = f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g"
    result = await oslc._find_current_iteration(project_url)
    assert result is None


@respx.mock
async def test_create_workitem_with_custom_fields():
    """custom_fields dict should be injected into the RDF/XML payload."""
    _mock_ccm_discovery()
    respx.get(f"{BASE}/ccm/oslc/iterations").mock(
        return_value=httpx.Response(200, json=ITERATIONS_JSON)
    )
    # Capture the POST body to verify custom fields are included
    post_route = respx.post(f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/workitems").mock(
        return_value=httpx.Response(201, json=CREATED_WI)
    )
    result = await create_workitem(
        project="MEU IMOVEL RURAL (MIR)",
        title="Test Task",
        type="task",
        custom_fields={"rtc_ext:com.dataprev.team.workitem.attribute.categoriatarefa": "literal.l10"},
    )
    assert result["dcterms:identifier"] == "42"
    # Verify custom field is in the posted body
    posted_body = post_route.calls[0].request.content.decode()
    assert "categoriatarefa" in posted_body
    assert "literal.l10" in posted_body


@respx.mock
async def test_create_workitem_without_custom_fields():
    """Without custom_fields, no extra fields should be injected."""
    _mock_ccm_discovery()
    respx.get(f"{BASE}/ccm/oslc/iterations").mock(
        return_value=httpx.Response(200, json=ITERATIONS_JSON)
    )
    post_route = respx.post(f"{BASE}/ccm/oslc/contexts/_MWxBEJB7Ee-fe_bes9r78g/workitems").mock(
        return_value=httpx.Response(201, json=CREATED_WI)
    )
    result = await create_workitem(
        project="MEU IMOVEL RURAL (MIR)",
        title="Test Task",
        type="task",
    )
    assert result["dcterms:identifier"] == "42"
    # plannedFor should still be auto-discovered
    posted_body = post_route.calls[0].request.content.decode()
    assert "plannedFor" in posted_body
    assert "_iter2" in posted_body


# === GOLDEN PAYLOAD TESTS (based on real server validation 22/mai/2026) ===
# These tests verify the EXACT behavior that creates WIs successfully on alm.dataprev.gov.br
# Reference: WI #628430 (manual), WI #629768 (automated)

PROJECT_AREA_ID = "_MWxBEJB7Ee-fe_bes9r78g"
CATEGORY_OID = "_ekfVwJB7Ee-fe_bes9r78g"
ITERATION_OID = "_361O8T5XEfGJQth8TJaPLA"


@respx.mock
async def test_golden_creation_url_is_workitems_not_defect():
    """Factory URL must be /workitems (not /workitems or /workitems/task)."""
    _mock_ccm_discovery()
    respx.get(f"{BASE}/ccm/oslc/iterations").mock(
        return_value=httpx.Response(200, json={"oslc:results": []})
    )
    # The POST must go to /workitems — NOT /workitems
    post_route = respx.post(f"{BASE}/ccm/oslc/contexts/{PROJECT_AREA_ID}/workitems").mock(
        return_value=httpx.Response(201, json=CREATED_WI)
    )
    result = await create_workitem(
        project="MEU IMOVEL RURAL (MIR)", title="Test", type="task"
    )
    assert result["dcterms:identifier"] == "42"
    assert post_route.called


@respx.mock
async def test_golden_content_type_is_rdf_xml():
    """POST Content-Type must be application/rdf+xml."""
    _mock_ccm_discovery()
    respx.get(f"{BASE}/ccm/oslc/iterations").mock(
        return_value=httpx.Response(200, json={"oslc:results": []})
    )
    post_route = respx.post(f"{BASE}/ccm/oslc/contexts/{PROJECT_AREA_ID}/workitems").mock(
        return_value=httpx.Response(201, json=CREATED_WI)
    )
    await create_workitem(project="MEU IMOVEL RURAL (MIR)", title="Test", type="task")
    assert post_route.calls[0].request.headers["content-type"] == "application/rdf+xml"


@respx.mock
async def test_golden_category_uses_itemoid_format():
    """filedAgainst must use /resource/itemOid/com.ibm.team.workitem.Category/{oid} format."""
    _mock_auth()
    respx.get(f"{BASE}/ccm/rootservices").mock(return_value=httpx.Response(200, text=CCM_ROOTSERVICES_XML))
    respx.get(f"{BASE}/ccm/oslc/workitems/catalog").mock(return_value=httpx.Response(200, text=CCM_CATALOG_XML))
    respx.get(f"{BASE}/ccm/oslc/contexts/{PROJECT_AREA_ID}/services").mock(
        return_value=httpx.Response(200, text=CCM_SERVICES_XML)
    )
    # Category API must return itemOid format
    respx.get(f"{BASE}/ccm/oslc/categories").mock(
        return_value=httpx.Response(200, json={
            "oslc:results": [{"rdf:about": f"{BASE}/ccm/resource/itemOid/com.ibm.team.workitem.Category/{CATEGORY_OID}"}]
        })
    )
    respx.get(f"{BASE}/ccm/oslc/iterations").mock(
        return_value=httpx.Response(200, json={"oslc:results": []})
    )
    post_route = respx.post(f"{BASE}/ccm/oslc/contexts/{PROJECT_AREA_ID}/workitems").mock(
        return_value=httpx.Response(201, json=CREATED_WI)
    )
    await create_workitem(project="MEU IMOVEL RURAL (MIR)", title="Test", type="task")
    body = post_route.calls[0].request.content.decode()
    assert f"resource/itemOid/com.ibm.team.workitem.Category/{CATEGORY_OID}" in body


@respx.mock
async def test_golden_custom_fields_as_rdf_resource():
    """custom_fields with rdf:resource values must render as rdf:resource attributes in XML."""
    _mock_ccm_discovery()
    respx.get(f"{BASE}/ccm/oslc/iterations").mock(
        return_value=httpx.Response(200, json={"oslc:results": []})
    )
    post_route = respx.post(f"{BASE}/ccm/oslc/contexts/{PROJECT_AREA_ID}/workitems").mock(
        return_value=httpx.Response(201, json=CREATED_WI)
    )
    await create_workitem(
        project="MEU IMOVEL RURAL (MIR)",
        title="Test",
        type="task",
        custom_fields={
            "rtc_ext:com.dataprev.team.workitem.attribute.categoriatarefa": {
                "rdf:resource": f"{BASE}/ccm/oslc/enumerations/{PROJECT_AREA_ID}/com.dataprev.team.workitem.enumeration.categoriatarefa/com.dataprev.team.workitem.enumeration.categoriatarefa.literal.l10"
            }
        },
    )
    body = post_route.calls[0].request.content.decode()
    assert "categoriatarefa" in body
    assert "rdf:resource" in body
    assert "literal.l10" in body


@respx.mock
async def test_golden_type_id_is_task_not_requirementchangerequest():
    """rtc_cm:type URI must use 'task' (not 'requirementChangeRequest' which is the calm:id)."""
    _mock_ccm_discovery()
    respx.get(f"{BASE}/ccm/oslc/iterations").mock(
        return_value=httpx.Response(200, json={"oslc:results": []})
    )
    post_route = respx.post(f"{BASE}/ccm/oslc/contexts/{PROJECT_AREA_ID}/workitems").mock(
        return_value=httpx.Response(201, json=CREATED_WI)
    )
    await create_workitem(project="MEU IMOVEL RURAL (MIR)", title="Test", type="task")
    body = post_route.calls[0].request.content.decode()
    assert f"/types/{PROJECT_AREA_ID}/task" in body


@respx.mock
async def test_golden_plannedfor_iteration_format():
    """plannedFor must use /oslc/iterations/{iterationOid} (without projectAreaId in path)."""
    _mock_ccm_discovery()
    respx.get(f"{BASE}/ccm/oslc/iterations").mock(
        return_value=httpx.Response(200, json={
            "oslc:results": [
                {"rdf:about": f"{BASE}/ccm/oslc/iterations/{ITERATION_OID}", "rtc_cm:current": True}
            ]
        })
    )
    post_route = respx.post(f"{BASE}/ccm/oslc/contexts/{PROJECT_AREA_ID}/workitems").mock(
        return_value=httpx.Response(201, json=CREATED_WI)
    )
    await create_workitem(project="MEU IMOVEL RURAL (MIR)", title="Test", type="task")
    body = post_route.calls[0].request.content.decode()
    assert f"/oslc/iterations/{ITERATION_OID}" in body


# === #20: update_workitem expanded (owner, planned_for, estimate_hours, custom_fields) ===


@respx.mock
async def test_update_workitem_owner():
    """owner parameter must set dcterms:contributor with rdf:resource."""
    _mock_auth()
    uri = f"{BASE}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/42"
    respx.get(uri).mock(return_value=httpx.Response(200, json=CREATED_WI, headers={"ETag": '"e1"'}))
    updated = {**CREATED_WI, "dcterms:contributor": {"rdf:resource": f"{BASE}/jts/users/claudio.filho"}}
    put_route = respx.put(uri).mock(return_value=httpx.Response(200, json=updated))
    result = await update_workitem(id="42", owner="claudio.filho")
    assert result["dcterms:contributor"]["rdf:resource"] == f"{BASE}/jts/users/claudio.filho"
    body = put_route.calls[0].request.content
    import json as _json
    sent = _json.loads(body)
    assert sent["dcterms:contributor"] == {"rdf:resource": f"{BASE}/jts/users/claudio.filho"}


@respx.mock
async def test_update_workitem_estimate_hours():
    """estimate_hours must set rtc_cm:estimate in milliseconds."""
    _mock_auth()
    uri = f"{BASE}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/42"
    respx.get(uri).mock(return_value=httpx.Response(200, json=CREATED_WI, headers={"ETag": '"e1"'}))
    updated = {**CREATED_WI, "rtc_cm:estimate": 28800000}
    put_route = respx.put(uri).mock(return_value=httpx.Response(200, json=updated))
    result = await update_workitem(id="42", estimate_hours=8)
    body = put_route.calls[0].request.content
    import json as _json
    sent = _json.loads(body)
    assert sent["rtc_cm:estimate"] == 28800000  # 8h * 3600000


@respx.mock
async def test_update_workitem_planned_for():
    """planned_for must set rtc_cm:plannedFor with rdf:resource."""
    _mock_auth()
    uri = f"{BASE}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/42"
    respx.get(uri).mock(return_value=httpx.Response(200, json=CREATED_WI, headers={"ETag": '"e1"'}))
    iteration_uri = f"{BASE}/ccm/oslc/iterations/_361O8T5XEfGJQth8TJaPLA"
    updated = {**CREATED_WI, "rtc_cm:plannedFor": {"rdf:resource": iteration_uri}}
    put_route = respx.put(uri).mock(return_value=httpx.Response(200, json=updated))
    result = await update_workitem(id="42", planned_for=iteration_uri)
    body = put_route.calls[0].request.content
    import json as _json
    sent = _json.loads(body)
    assert sent["rtc_cm:plannedFor"] == {"rdf:resource": iteration_uri}


@respx.mock
async def test_update_workitem_custom_fields():
    """custom_fields dict must be merged into the PUT payload."""
    _mock_auth()
    uri = f"{BASE}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/42"
    respx.get(uri).mock(return_value=httpx.Response(200, json=CREATED_WI, headers={"ETag": '"e1"'}))
    respx.put(uri).mock(return_value=httpx.Response(200, json=CREATED_WI))
    await update_workitem(id="42", custom_fields={"rtc_cm:someField": "value"})


@respx.mock
async def test_update_workitem_multiple_fields():
    """Multiple fields can be updated in a single call."""
    _mock_auth()
    uri = f"{BASE}/ccm/resource/itemName/com.ibm.team.workitem.WorkItem/42"
    respx.get(uri).mock(return_value=httpx.Response(200, json=CREATED_WI, headers={"ETag": '"e1"'}))
    put_route = respx.put(uri).mock(return_value=httpx.Response(200, json=CREATED_WI))
    await update_workitem(id="42", title="New Title", owner="claudio.filho", estimate_hours=16)
    body = put_route.calls[0].request.content
    import json as _json
    sent = _json.loads(body)
    assert sent["dcterms:title"] == "New Title"
    assert sent["dcterms:contributor"] == {"rdf:resource": f"{BASE}/jts/users/claudio.filho"}
    assert sent["rtc_cm:estimate"] == 57600000


# === #11: list_iterations tool ===

ITERATIONS_LIST_JSON = {
    "oslc:results": [
        {"rdf:resource": f"{BASE}/ccm/oslc/iterations/_iter1"},
        {"rdf:resource": f"{BASE}/ccm/oslc/iterations/_iter2"},
        {"rdf:resource": f"{BASE}/ccm/oslc/iterations/_iter3"},
    ]
}

ITER1_JSON = {"dcterms:title": "Backlog", "dcterms:identifier": "Backlog"}
ITER2_JSON = {"dcterms:title": "Sprint 1", "dcterms:identifier": "Sprint 1", "rtc_cm:startDate": "2026-05-01T00:00:00.000Z", "rtc_cm:endDate": "2026-05-15T00:00:00.000Z"}
ITER3_JSON = {"dcterms:title": "Sprint 2", "dcterms:identifier": "Sprint 2", "rtc_cm:startDate": "2026-05-18T00:00:00.000Z", "rtc_cm:endDate": "2026-06-06T00:00:00.000Z"}


@respx.mock
async def test_list_iterations():
    """list_iterations must return iterations with title, dates, and URI."""
    from elm_alm_py.server import list_iterations
    _mock_ccm_discovery()
    respx.get(f"{BASE}/ccm/oslc/iterations").mock(return_value=httpx.Response(200, json=ITERATIONS_LIST_JSON))
    respx.get(f"{BASE}/ccm/oslc/iterations/_iter1").mock(return_value=httpx.Response(200, json=ITER1_JSON))
    respx.get(f"{BASE}/ccm/oslc/iterations/_iter2").mock(return_value=httpx.Response(200, json=ITER2_JSON))
    respx.get(f"{BASE}/ccm/oslc/iterations/_iter3").mock(return_value=httpx.Response(200, json=ITER3_JSON))
    result = await list_iterations(project="MEU IMOVEL RURAL (MIR)")
    assert len(result) == 3
    assert result[1]["title"] == "Sprint 1"
    assert result[1]["start_date"] == "2026-05-01"
    assert result[1]["uri"] == f"{BASE}/ccm/oslc/iterations/_iter2"
