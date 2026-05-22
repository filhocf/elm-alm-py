# Usage Patterns & Known Limitations

## Query Syntax (list_workitems, search_requirements)

OSLC query syntax. Examples:

```python
# By title
list_workitems(project="MIR", query='dcterms:title="Produção certa"')

# By iteration (plannedFor)
list_workitems(project="MIR", query='rtc_cm:plannedFor=<https://alm.dataprev.gov.br/ccm/oslc/iterations/_361O8T5XEfGJQth8TJaPLA>')

# By type
list_workitems(project="MIR", query='dcterms:type="Tarefa"')

# By state
list_workitems(project="MIR", query='rtc_cm:state=<https://alm.dataprev.gov.br/ccm/oslc/workflows/_MWxBEJB7Ee-fe_bes9r78g/states/com.ibm.team.workitem.taskWorkflow/com.ibm.team.workitem.taskWorkflow.state.s1>')
```

## Creating Work Items

```python
# Minimal (auto-discovers category and iteration)
create_workitem(project="MIR", title="My Task", type="task")

# With all fields (recommended for Dataprev)
create_workitem(
    project="MIR",
    title="My Task",
    type="task",
    owner="claudio.filho",
    filed_against="https://alm.dataprev.gov.br/ccm/resource/itemOid/com.ibm.team.workitem.Category/_ekfVwJB7Ee-fe_bes9r78g",
    custom_fields={
        "rtc_ext:com.dataprev.team.workitem.attribute.categoriatarefa": {
            "rdf:resource": "https://alm.dataprev.gov.br/ccm/oslc/enumerations/_MWxBEJB7Ee-fe_bes9r78g/com.dataprev.team.workitem.enumeration.categoriatarefa/com.dataprev.team.workitem.enumeration.categoriatarefa.literal.l10"
        }
    },
)

# Child task (under an IB)
add_child_workitem(parent_id="628430", title="Sub-task", type="task")
```

## Updating Work Items

```python
# Set owner + estimate
update_workitem(id="629772", owner="claudio.filho", estimate_hours=16)

# Set iteration
update_workitem(id="629772", planned_for="https://alm.dataprev.gov.br/ccm/oslc/iterations/_361O8T5XEfGJQth8TJaPLA")

# Custom fields
update_workitem(id="629772", custom_fields={"rtc_cm:someField": "value"})
```

## Known Limitations

1. **_find_default_category** returns first category from project (may not be correct). Pass `filed_against` explicitly for MIR.

2. **_find_current_iteration** prefers bounded iterations (with endDate). If your sprint doesn't appear, pass `planned_for` explicitly in update_workitem.

3. **Iteration list is slow** — fetches details for each of 50 iterations. Use `list_iterations` sparingly.

4. **State transitions** not supported via update_workitem. RTC requires workflow action, not direct state change.

5. **RM domain (DOORS Next)** uses regex fallback for discovery (OSLC 1.0 format differs from CCM).

## MIR Project Constants

```python
PROJECT_AREA_ID = "_MWxBEJB7Ee-fe_bes9r78g"
CATEGORY_MIR = "https://alm.dataprev.gov.br/ccm/resource/itemOid/com.ibm.team.workitem.Category/_ekfVwJB7Ee-fe_bes9r78g"
ITERATION_SPRINT2 = "https://alm.dataprev.gov.br/ccm/oslc/iterations/_361O8T5XEfGJQth8TJaPLA"
CATEGORIATAREFA_DEV = "https://alm.dataprev.gov.br/ccm/oslc/enumerations/_MWxBEJB7Ee-fe_bes9r78g/com.dataprev.team.workitem.enumeration.categoriatarefa/com.dataprev.team.workitem.enumeration.categoriatarefa.literal.l10"
```
