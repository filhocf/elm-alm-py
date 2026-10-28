# SPEC — Docs structure (padrão adr/rfc/specs)

**Status:** IN PROGRESS (G4 — parte já aplicada) · **Release:** v0.5.0 · **RFC-mãe:** RFC-001 §5
**Referência:** orc-hestrator `docs/` · **Classe:** engenharia/documentação

## Meta

Docs do projeto no padrão OSS de primeira linha: `docs/{adr,rfc,specs}/` atômicos, roadmap como Plano,
ARCHITECTURE coerente com o código, legados arquivados.

## Escopo

- [x] Criar `docs/{adr,rfc,specs,_archive}/`.
- [x] Mover RFC-001 para `docs/rfc/`; arquivar migração mcp2x (PRD/SPEC/state) e SPEC/SPEC-WRITE
  legados em `docs/_archive/`.
- [x] `docs/roadmap.md` (Plano, releases v0.4→v0.9).
- [x] RFC-001 reescrita enxuta (visão, não big-bang) apontando specs.
- [x] ADR-001/002/003 retroativos.
- [x] `docs/ARCHITECTURE.md` novo (substitui o SPEC.md legado obsoleto), coerente com as 12 tools e a arquitetura core/adaptação.
- [x] `docs/CONVENTIONS.md` (rule vs practice, idioma Opção B, zero-tenant, EARS-PT) + `docs/TOOLS.md` (referência das 12 tools).
- [ ] Criar as demais specs atômicas (v0.6→v0.9) em estado PLANNED.

## Critério de aceite (EARS)

- A árvore `docs/` DEVE espelhar o padrão orc (adr/rfc/specs + docs de topo), sem doc obsoleto solto na raiz de `docs/`.
- O sistema DEVE conter `docs/ARCHITECTURE.md` descrevendo o CRUD atual (não "read-only").
- QUANDO um link markdown interno for quebrado, a verificação de links DEVE falhar (via `links` CI, quando existir).
- O sistema DEVE conter `docs/CONVENTIONS.md` e `docs/TOOLS.md`.

## Gates
Majoritariamente mecânico (G4 direto); review leve no fim.

## Fontes
- **F3**: estrutura `~/git/orc/orc/docs/{adr,rfc,specs}/` (referência); estado inicial dos docs do elm-mcp.
