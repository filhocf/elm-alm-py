# Tools reference

The twelve MCP tools exposed today. All are async and validated through the `@tool` boundary
(invalid input or domain failures surface as `ToolError`). `domain` is one of `rm`, `ccm`, `qm`.
See `docs/USAGE.md` for query syntax and examples.

## Read

| Tool | Signature | Description |
|------|-----------|-------------|
| `list_projects`     | `(domain)` | List projects (service providers) for a domain. |
| `search_requirements` | `(project, query=None)` | OSLC query over RM requirements (DOORS Next). |
| `get_requirement`   | `(uri)` | Fetch a single requirement by its OSLC URI. |
| `list_workitems`    | `(project, query=None)` | OSLC query over CCM work items; returns id/title/type/status/owner inline. |
| `get_workitem`      | `(id)` | Fetch a single work item by ID. |
| `search_testcases`  | `(project, query=None)` | OSLC query over QM test cases (ETM). |
| `list_iterations`   | `(project)` | List a project's iterations (title, dates, URI). |
| `get_plan_items`    | `(project, plan=None, item_ids=None)` | Hierarchical view: backlog items with child tasks expanded in one call. Select by `plan` (iteration title substring) or `item_ids`. |

## Write (CCM work items)

| Tool | Signature | Description |
|------|-----------|-------------|
| `create_workitem`     | `(project, title, type="task", description=None, parent_id=None, owner=None, filed_against=None, custom_fields=None)` | Create a work item. `type` is `task` or `story`. Category/iteration auto-discovered if omitted. |
| `update_workitem`     | `(id, title=None, description=None, owner=None, estimate_hours=None, planned_for=None, custom_fields=None)` | Update fields via ETag-based PUT. |
| `add_child_workitem`  | `(parent_id, title, type="task", description=None, owner=None, project=...)` | Create a work item linked as a child of `parent_id`. |
| `transition_workitem` | `(id, action)` | Move a work item through its workflow. `action` ∈ `start`, `resolve`, `close`, `reopen`. |

## Notes

- `create_workitem` currently supports `task` and `story`. Additional types (defect, technical debt,
  risk, impediment) are on the roadmap (`docs/specs/SPEC-wi-custom-types.md`).
- `custom_fields` injects project-specific RDF attributes; values are discovered per project area,
  not hardcoded (see `docs/ARCHITECTURE.md` core vs adaptation).
- RM/QM today are read-only through these tools; write support is planned
  (`docs/specs/SPEC-rm-create-requirement.md`, `SPEC-qm-write.md`).
