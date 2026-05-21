# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [0.2.0] - 2026-05-21

### Added

- **Write operations** for CCM work items:
  - `create_workitem` — create task/story with parent, owner, description
  - `update_workitem` — update title/description via OSLC PUT with ETag
  - `add_child_workitem` — convenience wrapper for creating children
- OSLC CreationFactory discovery for CCM domain
- ETag-based optimistic locking on updates
- Error handling tests for HTTP 400/401/409/412

### Fixed

- RM (DOORS Next): support Discovery 1.0 namespace in catalog + /views query endpoint
- QM (ETM): fallback to XML when JSON returns 406
- CCM (RTC): derive /services endpoint from catalog URL (was failing on services.xml)
- Handle query_base URLs with existing query parameters (RM projectURL)

### Added

- AGENTS.md with domain-specific OSLC patterns documented
- MEMORY.md for session handoff
- CodeQL security scanning workflow
- Dependabot for pip + github-actions
- Publish workflow (PyPI trusted publisher on tag push)
- pytest-cov with 60% threshold (cli.py excluded)

## [0.1.0] - 2026-05-18

### Added

- Initial implementation: MCP server for IBM ELM via OSLC REST
- 6 tools: list_projects, search_requirements, get_requirement, list_workitems, get_workitem, search_testcases
- Jazz form-based authentication with cookie management
- OSLC service discovery (rootservices → catalog → ServiceProvider → QueryCapability)
- CLI with `login` (credential setup) and `serve` (MCP stdio) commands
- Auto-load credentials from `~/.elm_creds.json` with base64 decode
- Support for ELM 7.0.3 OSLC namespaces (v1 + v2 fallback)
- Comprehensive test suite with respx mocking (21 tests)
- CI: GitHub Actions (ruff lint + pytest on Python 3.10-3.13)
