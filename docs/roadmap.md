# elm-alm-py — Roadmap

> O PLANO. Backlog de releases do elm-alm-py (MCP server para IBM ELM via OSLC).
> Cadeia de rastreabilidade: **Roadmap (este doc) → RFC (`docs/rfc/`) → SPECs atômicas
> (`docs/specs/`) → PRs**. Decisões transversais em `docs/adr/`. Pesquisa de fundamento em
> `conhecimentos-de-ia/ferramentas/elm-mcp/`.
> Não duplica estado: o estado de cada spec vive no cabeçalho da própria spec (Status/gate).

## Visão

Elevar o elm-alm-py de "cliente OSLC read + CRUD de work item" para o **middleware** entre o
processo agêntico (DAIA) e o ALM tradicional (IBM ELM), como projeto open-source de primeira linha
(tenant-neutro, instalável em um comando, gate agêntico no repo). Detalhe: `docs/rfc/RFC-001`.

## Legenda

Esforço 🟢 baixo · 🟡 médio · 🔴 alto. Status por spec no cabeçalho da spec (PLANNED/em gate/done).

## Releases

| Release | Tema | SPECs | Esf |
|---------|------|-------|-----|
| **v0.4.0** | Migração mcp 2.x (feita — falta taggear/publicar) | `_archive/SPEC-mcp2x-migration` | ✅ |
| **v0.5.0** | Profissionalização / repo-ouro | `SPEC-dead-code-cleanup`, `SPEC-docs-structure`, `SPEC-tenant-neutral`, `SPEC-repo-gold-ci` | 🟢 |
| **v0.6.0** | RM write + discovery (membrana agêntica P0) | `SPEC-rm-create-requirement`, `SPEC-discovery-tools` | 🟡 |
| **v0.7.0** | Rastreabilidade + tipos | `SPEC-oslc-links`, `SPEC-wi-custom-types` | 🟡 |
| **v0.8.0** | Teste + relatórios | `SPEC-qm-write`, `SPEC-reportbuilder-rs` | 🔴 |
| **v0.9.0** | Instalação first-class + credenciais | `SPEC-credential-keyring`, `SPEC-first-class-install` | 🟡 |
| **v1.0.0** | Quando o conjunto estiver sólido (decisão do Claudio) | — | — |

## Ordem de ataque

1. **v0.5.0 primeiro** — higiene destrava tudo (remove dead code, tenant-neutro, docs no padrão,
   gate agêntico no repo). Baixo risco, alto efeito de base. É o piloto do checklist repo-ouro do DAIA.
2. **v0.6.0** — `create_requirement` é o pedido nº 1 do DAIA (membrana); discovery habilita a camada
   de adaptação dinâmica por PA.
3. v0.7 → v0.9 na ordem da tabela; cada uma pode ser reordenada conforme necessidade do DAIA.

## Fora de escopo (limite da plataforma, não do roadmap)

- Criar iteração/sprint: a API OSLC CCM não permite (manual no EWM). O MCP só vincula (`plannedFor`).
- Acesso ao DB transacional do Jazz para relatórios: não suportado pela IBM (ver RFC-001 §relatórios).

## Fontes

- **F3**: levantamento interno + pesquisa de APIs em
  `conhecimentos-de-ia/ferramentas/elm-mcp/{levantamento-interno-alm,pesquisa-apis-elm}.md` (27/out/2026).
- **F3**: diagnóstico de código (codebase-memory) — 415 nós, `_find_creation_factory` sem chamador de produção.
