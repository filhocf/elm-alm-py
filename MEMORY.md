# MEMORY.md — elm-alm-py

## Estado Atual (18/mai/2026)

- **Versão**: 0.1.0 (10 commits, branch main)
- **Repo**: https://github.com/filhocf/elm-alm-py
- **Status**: ✅ Testado end-to-end contra ELM real

## Feito

- 6 tools: list_projects, search_requirements, get_requirement, list_workitems, get_workitem, search_testcases
- Auth: form-based Jazz com cookies (httpx AsyncClient singleton)
- Config: env vars + ~/.elm_creds.json (base64 password)
- CLI: `elm-alm-py login` (setup interativo) + `elm-alm-py serve` (MCP stdio)
- OSLC: discovery via rootservices → catalog → ServiceProvider → QueryCapability
- Namespaces: corrigidos para ELM 7.0.3 (Discovery 1.0 para RM, OSLC Core para CCM/QM)
- RM: endpoint /views com projectURL (DOORS Next não expõe QueryCapability padrão)
- QM: fallback XML quando JSON retorna 406
- CCM: derivação de /services a partir da URL do catalog
- Testes: 21 passando, coverage 62%
- CI: GitHub Actions (lint + test + coverage) + CodeQL + Dependabot + Publish
- Gemini Code Assist: ativo
- Conformidade DEVELOPMENT-STANDARDS.md: ✅

## Teste End-to-End (18/mai/2026, DNBSCDC289)

| Domínio | Projetos | Query |
|---------|:--------:|:-----:|
| CCM (RTC) | 7 | 50 work items MIR ✅ |
| RM (DOORS Next) | 3 | Requirements MIR ✅ |
| QM (ETM) | 2 | Test cases MIR ✅ |

## Pendente

- [ ] Integrar no mcp.json local (substituir elm_poc antigo)
- [ ] Igualar nas 3 máquinas (socrates, sirdata)
- [ ] Aumentar coverage (testes para novos paths RM/QM)
- [ ] Tag v0.1.0 + release PyPI
- [ ] Testar oslc.where queries (filtros)

## Decisões

- Substituiu `elm_poc` (192 linhas, só CCM, baseado em elmclient)
- httpx em vez de requests (async nativo)
- FastMCP em vez de MCP SDK raw
- Sem elmclient como dependência
- RM usa /views endpoint (Discovery 1.0, não OSLC Core QueryCapability)
- QM aceita só XML (fallback automático quando JSON dá 406)
- Coverage threshold 60% (cli.py excluído, código novo testado e2e)
- ELM URL configured via env var or ~/.elm_creds.json (no hardcoded default)
