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
- [ ] `docs/ARCHITECTURE.md` novo (substitui o SPEC.md legado obsoleto que dizia "read-only"),
  coerente com as 12 tools e a arquitetura core/adaptação; validado contra o grafo.
- [ ] `docs/CONVENTIONS.md` (rule vs practice, estilo orc) + `docs/TOOLS.md` (referência das tools).
- [ ] Criar as demais specs atômicas (v0.6→v0.9) em estado PLANNED.

## Critério de aceite

- Árvore `docs/` espelha o padrão orc (adr/rfc/specs + topo). Nenhum doc solto obsoleto na raiz de docs.
- `ARCHITECTURE.md` descreve CRUD atual (não "read-only"). Links internos válidos (links-check).

## Gates
Majoritariamente mecânico (G4 direto); review leve no fim.

## Fontes
- **F3**: estrutura `~/git/orc/orc/docs/{adr,rfc,specs}/` (referência); estado inicial dos docs do elm-alm-py.
