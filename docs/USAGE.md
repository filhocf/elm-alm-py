# Usage Patterns

Examples use placeholder values. Replace the server host (`https://elm.company.com`),
project names, user logins and resource URIs with the ones discovered for your own
ELM project area.

## Query Syntax (list_workitems, search_requirements)

OSLC query syntax. Examples:

```python
# By title
list_workitems(project="MY PROJECT (KEY)", query='dcterms:title="Some title"')

# By iteration (plannedFor)
list_workitems(project="MY PROJECT (KEY)", query='rtc_cm:plannedFor=<https://elm.company.com/ccm/oslc/iterations/_ITERATION_OID>')

# By type
list_workitems(project="MY PROJECT (KEY)", query='dcterms:type="Task"')

# By state
list_workitems(project="MY PROJECT (KEY)", query='rtc_cm:state=<https://elm.company.com/ccm/oslc/workflows/_WORKFLOW_OID/states/com.ibm.team.workitem.taskWorkflow/com.ibm.team.workitem.taskWorkflow.state.s1>')
```

## Creating Work Items

```python
# Minimal (auto-discovers category and iteration)
create_workitem(project="MY PROJECT (KEY)", title="My Task", type="task")

# With explicit fields (project-specific attributes)
create_workitem(
    project="MY PROJECT (KEY)",
    title="My Task",
    type="task",
    owner="jdoe",
    filed_against="https://elm.company.com/ccm/resource/itemOid/com.ibm.team.workitem.Category/_CATEGORY_OID",
    custom_fields={
        "rtc_ext:com.company.team.workitem.attribute.customattr": {
            "rdf:resource": "https://elm.company.com/ccm/oslc/enumerations/_PROJECT_AREA_OID/com.company.team.workitem.enumeration.customattr/com.company.team.workitem.enumeration.customattr.literal.l10"
        }
    },
)

# Child task (under a parent work item)
add_child_workitem(parent_id="628430", title="Sub-task", type="task")
```

> Project-specific attributes (category, iteration, custom `rtc_ext:*` fields) vary per
> server and per project area. Discover them for your project rather than copying the
> placeholders above (see the adaptation layer / discovery tools on the roadmap).

## Updating Work Items

```python
# Set owner + estimate
update_workitem(id="629772", owner="jdoe", estimate_hours=16)

# Set iteration
update_workitem(id="629772", planned_for="https://elm.company.com/ccm/oslc/iterations/_ITERATION_OID")

# Custom fields
update_workitem(id="629772", custom_fields={"rtc_cm:someField": "value"})
```

## Notes

- Category auto-discovery picks the first category of the project; pass `filed_against`
  explicitly when the project has more than one.
- Current-iteration auto-discovery prefers bounded iterations (with an end date); pass
  `planned_for` explicitly if your sprint is not picked up.
- `list_iterations` fetches details per iteration and can be slow on projects with many.
- State changes go through `transition_workitem` (workflow action), not `update_workitem`.
- RM (DOORS Next) discovery differs from CCM (OSLC 1.0 vs 2.0 catalog shapes).
