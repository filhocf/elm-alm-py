# ELM ALM MCP Server — Specification

## Overview

Read-only MCP server providing access to IBM Engineering Lifecycle Management (ELM) via OSLC REST APIs.

## Architecture

IBM ELM exposes three domains through OSLC (Open Services for Lifecycle Collaboration):

| Domain | Application | Root Services |
|--------|-------------|---------------|
| RM | DOORS Next (Requirements) | `/rm/rootservices` |
| CCM | RTC (Change & Config Mgmt) | `/ccm/rootservices` |
| QM | ETM (Quality Management) | `/qm/rootservices` |

## Authentication

Jazz form-based authentication:

1. POST to `/auth/j_security_check` with `j_username` + `j_password`
2. Server returns session cookies (JSESSIONID, etc.)
3. All subsequent requests include cookies
4. Auth failure indicated by `X-com-ibm-team-repository-web-auth-msg` header

## OSLC Service Discovery

```
rootservices → ServiceProviderCatalog → ServiceProvider → QueryCapability → queryBase
```

1. Parse rootservices XML to find catalog URL
2. Parse catalog to list ServiceProviders (projects)
3. Parse ServiceProvider to find QueryCapability for resource type
4. Use queryBase URL with `oslc.where` parameter for queries

## Resource Types

- RM: `http://open-services.net/ns/rm#Requirement`
- CCM: `http://open-services.net/ns/cm#ChangeRequest`
- QM: `http://open-services.net/ns/qm#TestCase`

## Query Parameters

- `oslc.where` — filter expression (e.g., `dcterms:title="X"`)
- `oslc.select` — properties to return
- `oslc.pageSize` — results per page (default: 50)

## Constraints

- Read-only: no creation, modification, or deletion
- SSL verification disabled (internal certificates)
- Single-server configuration via environment variables
