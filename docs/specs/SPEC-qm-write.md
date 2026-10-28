# SPEC — QM write (escrita no ETM: test case/plan/execution/result)

**Status:** PLANNED (G0) · **Release:** v0.8.0 · **RFC-mãe:** RFC-001 §5
**Pesquisa:** `pesquisa-apis-elm.md §3` · `levantamento-interno-alm.md §B.9/C.9`
**Classe:** entregável de produto — fecha o ciclo RM→QM→CM

## Meta

Escrita no domínio QM (ETM) via OSLC QM 2.1: criar os recursos de teste e vinculá-los ao IB/requisito.
Hoje o elm-mcp só busca (`search_testcases`).

## Escopo

- Tools para os 5 recursos OSLC QM: `create_test_plan`, `create_test_case`, `create_test_script`,
  `create_test_execution_record`, `create_test_result` (criar + ler).
- Vínculos: Test Case ↔ Requisito (`validatesRequirement`), Test Case ↔ TCER, Test Result ↔ WI
  (via `SPEC-oslc-links`).
- Para dados nativos do ETM que o OSLC não cobre (passos de script, campos nativos), registrar como
  limitação e apontar a ETM Reportable REST como caminho futuro (não nesta spec).

## Critério de aceite (EARS)

- QUANDO `create_test_case` for chamado, o sistema DEVE criar o recurso no QM e retornar sua URI.
- O sistema DEVE suportar criar os cinco recursos OSLC QM (plan/case/script/TCER/result).
- QUANDO um Test Case for vinculado a um requisito, o sistema DEVE registrar o link `validatesRequirement`.
- ONDE o ETM exigir campos nativos fora do OSLC, o sistema DEVE documentar a limitação (sem falhar silenciosamente).

## Gates
G0 → G3 (respx por recurso + vínculo) → G4 → G5. Depende de `SPEC-oslc-links`.

## Fontes
- **F2**: `pesquisa-apis-elm.md §3` (OSLC QM 2.1: os 5 recursos [VIA OSLC]; dados nativos via Reportable REST).
- **F3**: `levantamento-interno-alm.md §C.9` (Caso de Teste, execução, "Testado por").
