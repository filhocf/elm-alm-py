# elm-mcp — Roadmap

> O PLANO. Backlog de releases do elm-mcp (MCP server para IBM ELM via OSLC).
> Cadeia de rastreabilidade: **Roadmap (este doc) → RFC (`docs/rfc/`) → SPECs atômicas
> (`docs/specs/`) → PRs**. Decisões transversais em `docs/adr/`. Pesquisa de fundamento em
> `conhecimentos-de-ia/ferramentas/elm-mcp/`.
> Não duplica estado: o estado de cada spec vive no cabeçalho da própria spec (Status/gate).

## Visão

Elevar o elm-mcp de "cliente OSLC read + CRUD de work item" para o **middleware** entre o
processo agêntico (DAIA) e o ALM tradicional (IBM ELM), como projeto open-source de primeira linha
(tenant-neutro, instalável em um comando, gate agêntico no repo). Detalhe: `docs/rfc/RFC-001`.

## Legenda

Esforço 🟢 baixo · 🟡 médio · 🔴 alto. Status por spec no cabeçalho da spec (PLANNED/em gate/done).

## Releases

| Release | Tema | SPECs | Esf |
|---------|------|-------|-----|
| **v0.4.0** (não publicada — engloba toda a base profissional) | mcp 2.x + rename + profissionalização / repo-ouro | migração mcp2x (feita) · `SPEC-dead-code-cleanup` · `SPEC-docs-structure` (feita) · `SPEC-tenant-neutral` · `SPEC-repo-gold-ci` · `SPEC-readme-profissional` · ADR-004 (nome) | 🟢 |
| **v0.5.0** | RM write + discovery (membrana agêntica P0) | `SPEC-rm-create-requirement`, `SPEC-discovery-tools` | 🟡 |
| **v0.6.0** | Rastreabilidade + tipos | `SPEC-oslc-links`, `SPEC-wi-custom-types` | 🟡 |
| **v0.7.0** | Teste + relatórios | `SPEC-qm-write`, `SPEC-reportbuilder-rs` | 🔴 |
| **v0.8.0** | Instalação first-class + credenciais | `SPEC-credential-keyring`, `SPEC-first-class-install` | 🟡 |
| **v1.0.0** | Quando o conjunto estiver sólido (decisão do Claudio) | — | — |

> **Renumeração (28/out):** a v0.4.0 não foi publicada no PyPI (só 0.1/0.2 estão lá), então ela
> absorve toda a base profissional (mcp2x + rename + higiene + repo-ouro + README) e só é publicada
> quando o repo estiver "primeira linha". As features sobem um degrau (RM write era v0.6, agora v0.5).

## Ordem de ataque

1. **Fechar a v0.4.0** antes de publicar: README profissional + dead-code + tenant-neutral no código
   + repo-gold-ci + ADR-004. Baixo risco, alto efeito de base. Piloto do checklist repo-ouro do DAIA.
2. **Publicar v0.4.0** no PyPI (tag `v0.4.0` → `publish.yml`) com o repo já profissional.
3. **v0.5.0** — `create_requirement` é o pedido nº 1 do DAIA (membrana); discovery habilita a camada
   de adaptação dinâmica por PA.
4. v0.6 → v0.8 na ordem da tabela; cada uma pode ser reordenada conforme necessidade do DAIA.

## Fora de escopo (limite da plataforma, não do roadmap)

- Criar iteração/sprint: a API OSLC CCM não permite (manual no EWM). O MCP só vincula (`plannedFor`).
- Acesso ao DB transacional do Jazz para relatórios: não suportado pela IBM (ver RFC-001 §relatórios).

## Fontes

- **F3**: levantamento interno + pesquisa de APIs em
  `conhecimentos-de-ia/ferramentas/elm-mcp/{levantamento-interno-alm,pesquisa-apis-elm}.md` (27/out/2026).
- **F3**: diagnóstico de código (codebase-memory) — 415 nós, `_find_creation_factory` sem chamador de produção.
