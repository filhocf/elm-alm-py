# Tools reference

The eighteen MCP tools exposed today. All are async and validated through the `@tool` boundary
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

## Discovery

Read-only introspection of a project area's metadata. Use these **before** writing, so a create/update
fills the fields the server actually requires — nothing is hardcoded per project.

| Tool | Signature | Description |
|------|-----------|-------------|
| `list_types`       | `(domain, project)` | List resource types (shapes) available in a project area. Returns `[{"title", "shape_uri", "resource_type"}]`. |
| `list_fields`      | `(domain, project, type)` | List required/optional fields of a type, with `allowedValues` when the field is enumerated. `type` is a shape title from `list_types` (case-insensitive). Returns `{"type", "shape_uri", "required":[...], "optional":[...]}`. |
| `inspect_workitem` | `(id)` | Read a real work item and derive its shape/factory URIs and filled fields. Returns `{"id", "type", "shape_uri", "factory_uri", "fields":{...}}`. Useful to learn a project area's concrete field values from an existing item. |
| `list_folders`     | `(project)` | List RM (DOORS Next) folders for a project. Returns `[{"title", "uri"}]`. System folders (root, query results) are filtered out. |

## Write (RM requirements)

| Tool | Signature | Description |
|------|-----------|-------------|
| `create_requirement` | `(project, title, content, folder=None, type=None)` | Create a requirement in a DOORS Next (RM) project. `content` is HTML, sanitized to XHTML and stored in `jazz_rm:primaryText`. `folder` is a folder URI (`nav:parent`, from `list_folders`). `type` is an `instanceShape` URI (from `list_types`). |
| `update_requirement` | `(uri, title=None, content=None)` | Update a requirement via OSLC PUT with ETag. `content` is HTML, sanitized to XHTML. |

## Write (CCM work items)

| Tool | Signature | Description |
|------|-----------|-------------|
| `create_workitem`     | `(project, title, type="task", description=None, parent_id=None, owner=None, filed_against=None, custom_fields=None)` | Create a work item. `type` is `task` or `story`. Category/iteration auto-discovered if omitted. |
| `update_workitem`     | `(id, title=None, description=None, owner=None, estimate_hours=None, planned_for=None, custom_fields=None)` | Update fields via ETag-based PUT. |
| `add_child_workitem`  | `(parent_id, title, type="task", description=None, owner=None, project=...)` | Create a work item linked as a child of `parent_id`. |
| `transition_workitem` | `(id, action)` | Move a work item through its workflow. `action` ∈ `start`, `resolve`, `close`, `reopen`. |

## Notes

- **Discover before you write.** `create_requirement`/`create_workitem` need shape and field values
  that vary per project area. Use `list_types` → `list_fields` (and `list_folders` for RM, or
  `inspect_workitem` to copy a real item's values) first. Nothing about a specific organization is
  baked into the package (see `docs/ARCHITECTURE.md`, core vs adaptation).
- `create_requirement` takes an `instanceShape` URI in `type`. Resolve the title you want
  (e.g. a requirement kind) to its `shape_uri` via `list_types` on the `rm` domain.
- `create_workitem` currently supports `task` and `story`. Additional types (defect, technical debt,
  risk, impediment) are on the roadmap (`docs/specs/SPEC-wi-custom-types.md`).
- `custom_fields` injects project-specific RDF attributes; values are discovered per project area
  (via the discovery tools), not hardcoded.
- QM (ETM) is read-only through these tools; test-case write and cross-domain OSLC links
  (Implements Requirement / Tested By / Affects) are planned (`docs/specs/`, `docs/roadmap.md`).
- State changes go through `transition_workitem` (workflow action), not `update_workitem`.
