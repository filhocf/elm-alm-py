# SPEC — Discovery tools (shapes, campos, pastas, inspeção)

**Status:** DONE (PR #45, gates G0→G5) · **Release:** v0.5.0 · **RFC-mãe:** RFC-001 §4/§5 · **ADR:** ADR-003
**Pesquisa:** `levantamento-interno-alm.md §A.2/A.3/A.4/A.11` · **Classe:** base da camada de adaptação

## Meta

Expor como tools MCP o discovery OSLC que hoje vive só nos scripts jandaia, permitindo que a camada de
adaptação por project area seja preenchida dinamicamente (não hardcoded). É o que habilita o core a
preencher campos obrigatórios por PA.

## Escopo

- `list_types(domain, project)` — lista shapes/tipos (CreationFactory → resourceShape).
- `list_fields(domain, project, type)` — campos obrigatórios/opcionais de um tipo, com `allowedValues`.
- `inspect_workitem(id)` — lê um WI real e deriva factories/shapes/campos (base para montar o perfil).
- `list_folders(project)` — pastas (folders) do RM.

## Critério de aceite (EARS)

- QUANDO `list_types` for chamado para um domínio/projeto, o sistema DEVE retornar os tipos disponíveis
  com o URI do resourceShape de cada um.
- QUANDO `list_fields` for chamado para um tipo, o sistema DEVE retornar os campos obrigatórios e
  opcionais com seus `allowedValues` (quando enumerados).
- QUANDO `inspect_workitem` for chamado, o sistema DEVE retornar os campos preenchidos do WI e os
  shapes/factories associados, suficientes para montar um perfil de adaptação.
- O sistema DEVE operar de forma genérica (sem conhecer campos de organização específica).

## Gates
G0 → G3 (respx mockando catalog/shape/allowedValues por domínio) → G4 → G5.

## Fontes
- **F3**: `levantamento-interno-alm.md §A.2/A.4/A.11` (listar-tipos/listar-campos/inspecionar no jandaia).
- **F2**: `pesquisa-apis-elm.md §1/§CCM` (shapes + allowedValues [VIA OSLC]).
