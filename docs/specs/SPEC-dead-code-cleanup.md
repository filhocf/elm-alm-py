# SPEC — Dead code cleanup

**Status:** DONE (G5) · **Release:** v0.4.0 · **RFC-mãe:** RFC-001 §5
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

## Critério de aceite (EARS)

- **Ubíquo:** O sistema DEVE manter verde toda a suíte de testes após a remoção (os testes de produção remanescentes passam).
- **Dirigido a evento:** QUANDO `_find_creation_factory` e seus 2 testes forem removidos, o sistema NÃO DEVE conter nenhum símbolo com zero chamadores de produção que seja removível (confirmado por `trace_path`/grep).
- **Indesejado:** SE a remoção fizer a cobertura cair abaixo do gate do CI, ENTÃO a mudança DEVE ser revista antes do merge.
- **Ubíquo:** O working tree NÃO DEVE conter caches versionados (`.coverage`, `.pytest_cache/`, `.ruff_cache/`).

## Gates
G0 (esta spec) → G3 (garantir que nenhum teste de produção depende) → G4 (remover) → G5 (review).

## Fontes
- **F3**: codebase-memory `trace_path(_find_creation_factory, inbound)` = 2 callers, ambos testes.
