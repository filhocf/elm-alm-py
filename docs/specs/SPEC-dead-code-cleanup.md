# SPEC — Dead code cleanup

**Status:** PLANNED (G0) · **Release:** v0.5.0 · **RFC-mãe:** RFC-001 §5
**Pesquisa:** diagnóstico codebase-memory (415 nós) · **Classe:** higiene de engenharia

## Meta

Remover código morto e sujeira confirmados por análise de grafo, reduzindo superfície sem alterar
comportamento observável.

## Escopo (confirmado por evidência)

- **`_find_creation_factory` (oslc.py:301-348)** — `trace_path(inbound)` mostra **0 chamadores de
  produção** (só 2 testes em `test_write.py` que testam a própria função morta). Remover a função + os
  2 testes (`test_find_creation_factory`, `test_find_creation_factory_by_type`).
- Confirmar, antes de remover, que `create_resource` não a usa por caminho dinâmico (grep + leitura).
- Sujeira de working tree: garantir `.coverage`, `.pytest_cache/`, `.ruff_cache/` fora (já no
  .gitignore; limpar local).
- `MEMORY.md` na raiz — resquício; avaliar mover para `docs/_archive/` ou remover (não é artefato OSS).

## Critério de aceite

- `_find_creation_factory` e seus 2 testes removidos; suíte segue verde (testes restantes passam).
- `trace_path`/grep confirmam nenhum outro símbolo com 0 chamadores de produção que seja removível.
- Cobertura não cai abaixo do gate (a remoção de código morto + seus testes tende a manter/subir %).

## Gates
G0 (esta spec) → G3 (garantir que nenhum teste de produção depende) → G4 (remover) → G5 (review).

## Fontes
- **F3**: codebase-memory `trace_path(_find_creation_factory, inbound)` = 2 callers, ambos testes.
