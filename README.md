# elm-alm-py

MCP server for **IBM Engineering Lifecycle Management (ELM)** — read-only access to DOORS Next (RM), RTC (CCM), and ETM (QM) via OSLC REST APIs.

Tested against ELM 7.0.3 (alm.dataprev.gov.br).

## Install

```bash
uv pip install -e .
```

## Configuration

### Option 1: Interactive login (recommended)

```bash
elm-alm-py login
```

Saves credentials to `~/.elm_creds.json` (password base64-encoded, chmod 600).

### Option 2: Environment variables

```bash
export ELM_URL=https://alm.dataprev.gov.br
export ELM_USER=claudio.filho
export ELM_PASSWORD=secret
```

## Usage

### As MCP server (stdio)

```bash
elm-alm-py
```

### MCP client configuration

```json
{
  "mcpServers": {
    "elm-alm": {
      "command": "elm-alm-py",
      "env": {
        "ELM_URL": "https://alm.dataprev.gov.br",
        "ELM_USER": "claudio.filho",
        "ELM_PASSWORD": "secret"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `list_projects(domain)` | List projects for RM/CCM/QM |
| `search_requirements(project, query?)` | OSLC query on RM requirements |
| `get_requirement(uri)` | Get single requirement by URI |
| `list_workitems(project, query?)` | OSLC query on CCM work items |
| `get_workitem(id)` | Get single work item by ID |
| `search_testcases(project, query?)` | OSLC query on QM test cases |
| `create_workitem(project, title, type?, description?, parent_id?, owner?)` | Create a work item (task/story) |
| `update_workitem(id, title?, description?)` | Update work item fields (ETag-based) |
| `add_child_workitem(parent_id, title, type?, description?, owner?)` | Create a child work item |

### Query syntax

The `query` parameter uses [OSLC query syntax](https://docs.oasis-open-projects.org/oslc-op/query/v3.0/oslc-query.html):

```
dcterms:title="My Requirement"
dcterms:modified>="2024-01-01"
```

## ELM 7.x Compatibility

Each domain uses a different OSLC variant:

| Domain | Application | API Pattern |
|--------|-------------|-------------|
| CCM | RTC (Work Items) | OSLC Core 2.0, JSON responses |
| RM | DOORS Next (Requirements) | Discovery 1.0, /views endpoint |
| QM | ETM (Test Cases) | OSLC Core 2.0, XML responses |

## Development

```bash
uv sync --group dev
uv run pytest tests/ -v --cov=elm_alm_py
uv run ruff check src/ tests/
```

## License

MIT
