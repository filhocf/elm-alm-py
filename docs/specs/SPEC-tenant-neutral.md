# SPEC — Tenant-neutral core

**Status:** PLANNED (G0) · **Release:** v0.5.0 · **RFC-mãe:** RFC-001 §3 · **ADR:** ADR-003
**Pesquisa:** `levantamento-interno-alm.md §E` · **Classe:** produto + narrativa

## Meta

O pacote `elm_alm_py` não cita nenhum cliente/empresa/PA/host concreto. Valores de tenant vivem só em
configuração/perfil, nunca no código ou na doc pública.

## Escopo (confirmado por grep)

- **Código:** remover o default `project="MEU IMOVEL RURAL (MIR)"` em `add_child_workitem`
  (server.py:347) — tornar `project` obrigatório (ou vir do perfil ativo). Trocar os exemplos em
  docstrings (server.py:154,256) por placeholder genérico (`"MY PROJECT (KEY)"`).
- **README.md:** remover `alm.dataprev.gov.br` e exemplos `com.dataprev.*`/`MIR`; usar
  `https://elm.example.com` e placeholders. Corrigir a inconsistência: README lista work item type
  `defect`, mas `TYPE_IDS` só tem task/story — alinhar (ou documentar como futuro em SPEC-wi-custom-types).
  Remover a seção "Known Limitations" que expõe detalhe interno impróprio para OSS.
- **docs/USAGE.md:** trocar todas as URLs `alm.dataprev.gov.br` e namespaces `com.dataprev.*` por genéricos.

## Critério de aceite

- `grep -rniE "dataprev|MEU IMOVEL|MIR" src/ README.md docs/USAGE.md` → 0 ocorrências (fora de exemplos
  explicitamente marcados como placeholder neutro).
- `add_child_workitem` sem default de PA; teste cobre a ausência de default.
- README coerente com o código (sem `defect` se não implementado).

## Gates
G0 → G3 (teste da obrigatoriedade de project) → G4 → G5.

## Fontes
- **F3**: `levantamento-interno-alm.md §E.1` (tabela de acoplamento); grep `dataprev` no core = só README/USAGE/docstrings.
