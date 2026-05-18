# MEMORY.md — elm-alm-py

## Estado Atual (18/mai/2026)

- **Versão**: 0.1.0 (7 commits, branch main)
- **Repo**: https://github.com/filhocf/elm-alm-py
- **Status**: Implementação base completa, não testado end-to-end contra ELM real (precisa VPN)

## Feito

- 6 tools: list_projects, search_requirements, get_requirement, list_workitems, get_workitem, search_testcases
- Auth: form-based Jazz com cookies (httpx AsyncClient singleton)
- Config: env vars + ~/.elm_creds.json (base64 password)
- CLI: `elm-alm-py login` (setup interativo) + `elm-alm-py serve` (MCP stdio)
- OSLC: discovery via rootservices → catalog → ServiceProvider → QueryCapability
- Namespaces: corrigidos para ELM 7.0.3 (v1 + fallback v2)
- Testes: 5 arquivos com respx mocking
- CI: GitHub Actions (lint + test multi-python)

## Pendente

- [ ] Testar end-to-end contra ELM real (precisa VPN — DNBSCDC289)
- [ ] Integrar no mcp.json local (substituir elm_poc antigo)
- [ ] Igualar nas 3 máquinas
- [ ] Formalizar CHANGELOG com releases

## Decisões

- Substituiu `elm_poc` (192 linhas, só CCM, baseado em elmclient) por implementação OSLC REST direta
- httpx em vez de requests (async nativo)
- FastMCP em vez de MCP SDK raw (menos boilerplate)
- Sem elmclient como dependência (era pesado e instável)
