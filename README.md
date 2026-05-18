# elm-alm-py

MCP server for **IBM Engineering Lifecycle Management (ELM)** — read-only access to DOORS Next (RM), RTC (CCM), and ETM (QM) via OSLC REST APIs.

## Install

```bash
uv pip install -e .
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

## Configuration

Set environment variables:

```bash
export ELM_URL=https://www-elm.prevnet
export ELM_USER=claudio.filho
export ELM_PASSWORD=secret
```

Or create a `.env` file in the project root.

## Usage

### As MCP server (stdio)

```bash
elm-alm-py
```

### MCP client configuration

Add to your MCP client config (e.g. `~/.config/kiro/mcp.json`):

```json
{
  "mcpServers": {
    "elm": {
      "command": "elm-alm-py",
      "env": {
        "ELM_URL": "https://www-elm.prevnet",
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

### Query syntax

The `query` parameter uses [OSLC query syntax](https://docs.oasis-open-projects.org/oslc-op/query/v3.0/oslc-query.html):

```
dcterms:title="My Requirement"
dcterms:modified>="2024-01-01"
oslc_rm:implementedBy{dcterms:title="Feature X"}
```

## Development

```bash
uv sync --group dev
uv run pytest tests/ -v
uv run ruff check src/ tests/
```

## License

MIT
