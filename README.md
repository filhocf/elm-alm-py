# elm-mcp

MCP server for **IBM Engineering Lifecycle Management (ELM)** — read and write access to DOORS Next (RM), RTC/EWM (CCM), and ETM (QM) via OSLC REST APIs.

Independent implementation over the open OSLC REST protocol — **not a fork** of IBM software, and vendor-neutral (no organization-specific values in the package). Tested against ELM 7.0.3.

## Install

```bash
uv pip install -e .
```

## Configuration

### Option 1: Credentials file (recommended)

```bash
elm-mcp login
```

Saves to `~/.elm_creds.json`:
```json
{"url": "https://your-elm-server.example.com", "username": "user", "password": "base64encoded"}
```

### Option 2: Environment variables

```bash
export ELM_URL=https://your-elm-server.example.com
export ELM_USER=your_username
export ELM_PASSWORD=secret
```

## Usage

```bash
# As MCP server (stdio)
elm-mcp
```

### MCP client configuration

```json
{
  "mcpServers": {
    "elm-alm": {
      "command": "/path/to/.venv/bin/elm-mcp"
    }
  }
}
```

## Tools

### Read Operations

| Tool | Description |
|------|-------------|
| `list_projects(domain)` | List projects for RM/CCM/QM |
| `search_requirements(project, query?)` | OSLC query on RM requirements |
| `get_requirement(uri)` | Get single requirement by URI |
| `list_workitems(project, query?)` | OSLC query on CCM work items |
| `get_workitem(id)` | Get single work item by ID |
| `search_testcases(project, query?)` | OSLC query on QM test cases |

### Write Operations

| Tool | Description |
|------|-------------|
| `create_workitem(project, title, type?, ...)` | Create a work item (task/story/defect) |
| `update_workitem(id, title?, description?)` | Update work item fields (ETag-based) |
| `add_child_workitem(parent_id, title, ...)` | Create a child work item |

#### create_workitem parameters

| Parameter | Required | Description |
|-----------|:--------:|-------------|
| `project` | ✅ | Project name (e.g., "MY PROJECT (KEY)") |
| `title` | ✅ | Work item title |
| `type` | | "task" (default), "story", or "defect" |
| `description` | | HTML description |
| `parent_id` | | Parent work item ID (creates child link) |
| `owner` | | Username (e.g., "jdoe") |
| `filed_against` | | Category URI. Auto-discovered if not provided |
| `custom_fields` | | Dict of extra RDF fields (see below) |

#### custom_fields for project-specific attributes

Some RTC projects require custom fields. Pass them as a dict:

```python
custom_fields={
    "rtc_ext:com.company.team.workitem.attribute.customattr": {
        "rdf:resource": "https://elm.company.com/ccm/oslc/enumerations/{projectAreaId}/..."
    }
}
```

Values can be:
- `{"rdf:resource": "uri"}` — for URI/enumeration fields
- `"text"` — for literal text fields

## OSLC API Details

### Work Item Types (CCM)

| Type | RTC type ID | calm:id in services.xml |
|------|-------------|-------------------------|
| task | `task` | `requirementChangeRequest` |
| story | `com.ibm.team.apt.workItemType.story` | `planItem` |

### Key Fields

| Field | Namespace | Format |
|-------|-----------|--------|
| Title | `dcterms:title` | Text |
| Type | `rtc_cm:type` | `rdf:resource` URI |
| Category | `rtc_cm:filedAgainst` | `rdf:resource` (itemOid format) |
| Iteration | `rtc_cm:plannedFor` | `rdf:resource` URI |
| Owner | `dcterms:contributor` | `rdf:resource` `/jts/users/{login}` |
| Estimate | `rtc_cm:estimate` | Integer (milliseconds) |
| State | `rtc_cm:state` | `rdf:resource` URI |

### Content Types

- **Create (POST)**: `application/rdf+xml`
- **Read (GET)**: `application/json` (Accept header)
- **Update (PUT)**: `application/json` with `If-Match: {ETag}`

## Development

```bash
uv sync --group dev
uv run pytest tests/ -v --cov=elm_alm_py
uv run ruff check src/ tests/
```

## Notes

- Category auto-discovery picks the first category of the project; pass `filed_against` explicitly when there is more than one.
- OSLC CM 1.0 `services.xml` parsing is bypassed — the creation URL is constructed directly.

See [docs/USAGE.md](docs/USAGE.md) for query syntax and more examples.

## License

MIT
