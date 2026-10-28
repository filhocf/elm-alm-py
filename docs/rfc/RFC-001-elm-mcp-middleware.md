# RFC-001: elm-mcp como middleware entre o processo agêntico e o ALM tradicional

> Status: **ACCEPTED** (visão) · Autor: Claudio (via Zero) · 2026-10-27
> Plano/releases: `docs/roadmap.md` · SPECs derivadas: `docs/specs/` · Decisões: `docs/adr/`
> Pesquisa: `conhecimentos-de-ia/ferramentas/elm-mcp/{levantamento-interno-alm,pesquisa-apis-elm}.md`
>
> Esta RFC é a VISÃO (o porquê e o escopo macro). O COMO vive em SPECs atômicas — uma por
> entregável — listadas em §5. Não detalhar implementação aqui.

## 1. Problema

O projeto (publicado como `elm-mcp`; chamado `elm-alm-py` entre mai e out/2026) nasceu como cliente
OSLC read-only e cresceu organicamente até CRUD de work item CCM, sem roadmap, sem docs estruturados,
com acoplamento a um tenant específico e sem o gate agêntico que nossos projetos maduros (orc, mms)
têm. Ao mesmo tempo, o DAIA precisa dele como a
**membrana** entre o fluxo agêntico (gera specs, requisitos, testes) e o ALM corporativo (IBM ELM) —
e hoje ele cobre só parte desse papel. Há um gap de **produto** (o que o MCP sabe fazer) e de
**engenharia** (como o projeto é mantido).

## 2. Proposta

Evoluir o elm-mcp em duas frentes, por releases rastreáveis (`docs/roadmap.md`):

- **Produto:** fechar as capacidades que faltam para ser a membrana completa — escrita de requisito
  (RM), discovery dinâmico por PA, links de rastreabilidade, escrita de teste (QM), relatórios.
- **Engenharia:** torná-lo OSS de primeira linha — tenant-neutro, docs ADR/RFC/SPEC atômicos, gate
  agêntico no repo (checklist repo-ouro do DAIA), instalação em um comando, credenciais seguras.

## 3. Identidade (fatos que a narrativa deve refletir)

- **Não é fork.** Implementação própria sobre o protocolo **OSLC REST** (OASIS). Não usa a lib
  `elmclient` da IBM. Decisão: `docs/adr/ADR-001`.
- **Tenant-neutro.** O core (`elm_mcp`) não cita nenhum cliente/empresa. Valores concretos de
  servidor/PA/campos vivem numa **camada de adaptação** (perfil por project area), descoberta via
  discovery OSLC. Decisão: `docs/adr/ADR-003`.
- **mcp 2.x.** Server sobre `MCPServer` (não FastMCP). Decisão: `docs/adr/ADR-002`.

## 4. Arquitetura: core genérico + camada de adaptação

O core fala OSLC/ELM genérico (namespaces IBM/Jazz, discovery, CRUD RM/CCM/QM, links, reporting).
A camada de adaptação fornece o concreto por PA (host, nome da PA, campos obrigatórios customizados,
tipos custom, mapa de workflow, pastas RM) — descoberto por discovery e persistido num perfil, nunca
no código. Detalhe em `docs/adr/ADR-003` e `docs/specs/SPEC-tenant-neutral` / `SPEC-discovery-tools`.

## 5. SPECs derivadas (o COMO; uma por entregável)

| SPEC | Entregável | Release |
|------|-----------|---------|
| `SPEC-dead-code-cleanup` | Remover `_find_creation_factory` (0 chamadores de produção) + sujeira | v0.5.0 |
| `SPEC-docs-structure` | docs adr/rfc/specs + roadmap + ARCHITECTURE; limpar legados | v0.5.0 |
| `SPEC-tenant-neutral` | Tirar default MIR do core + limpar README/USAGE de tenant | v0.5.0 |
| `SPEC-repo-gold-ci` | `.codebase-memory` versionado, `tests-prove-fix`, changelog.d, SHA-pin, review-skill | v0.5.0 |
| `SPEC-rm-create-requirement` | `create_requirement`/`update_requirement` (RM write) | v0.6.0 |
| `SPEC-discovery-tools` | `list_types`/`list_fields`/`inspect_workitem`/`list_folders` | v0.6.0 |
| `SPEC-oslc-links` | Links cross-domínio (implementsRequirement, testedByTestCase, affects) | v0.7.0 |
| `SPEC-wi-custom-types` | Tipos de WI além de task/story (defeito/dívida/risco/impedimento) | v0.7.0 |
| `SPEC-qm-write` | Criar test case/plan/execution/result + vínculos (OSLC QM) | v0.8.0 |
| `SPEC-reportbuilder-rs` | Expor relatórios do Report Builder (RS) via Reportable REST/JRS | v0.8.0 |
| `SPEC-credential-keyring` | Credenciais via keyring do SO (não env var, não base64) | v0.9.0 |
| `SPEC-first-class-install` | `uvx` + snippet Kiro/OpenCode/Hermes + guia Windows | v0.9.0 |

## 6. Relatórios (restrição de arquitetura)

Caminho suportado: **Reportable REST** (por app, herda auth) > Report Builder/JRS > LQE/SPARQL >
Data Warehouse (fallback). **Nunca** o DB transacional (IBM desaconselha). O "RS" que o time de gestão
usa = relatórios montados no **Report Builder** → expor via REST, não tocar o banco. Detalhe:
`pesquisa-apis-elm.md §5` e `SPEC-reportbuilder-rs`.

## 7. Decisões

- **Nome:** migrado para `elm-mcp` (28/out) — distribuição PyPI, módulo `elm_mcp`, entry point `elm-mcp`
  e repositório `github.com/filhocf/elm-mcp`. Ambos os nomes (PyPI e GitHub) já eram do próprio autor
  (primeira versão de mai/2026); o repo antigo foi removido e o atual renomeado, com redirect do nome
  anterior. Registrar em ADR-004.
- **`/fix` agêntico:** DECIDIDO (28/out) — somente `/review` (read-only, comenta); a correção volta para
  o dev resolver localmente e re-submeter. Sem agente escrevendo no repo. Ver `SPEC-repo-gold-ci`.

## Fontes

- **F3**: `conhecimentos-de-ia/ferramentas/elm-mcp/levantamento-interno-alm.md` (ações jandaia/daia/PD,
  matriz de cobertura vs 12 tools) e `pesquisa-apis-elm.md` (capacidades OSLC/Reportable REST/reporting),
  ambos 27-29/out/2026.
- **F3**: diagnóstico codebase-memory do elm-mcp (415 nós; `_find_creation_factory` sem chamador de produção).
