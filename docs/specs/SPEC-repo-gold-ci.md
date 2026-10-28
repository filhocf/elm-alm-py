# SPEC — Repositório-ouro / CI agêntico

**Status:** PLANNED (G0) · **Release:** v0.5.0 · **RFC-mãe:** RFC-001 §5
**Padrão-ouro:** DAIA `materializacao/daia-produto-clonavel.md §Checklist` · **Classe:** gate executável

## Meta

Aplicar no elm-alm-py (como PILOTO do checklist repo-ouro do DAIA) a maquinaria agêntica que faz o
processo viajar com o repositório — não depender do harness local do dono.

## Escopo (checklist repo-ouro, camadas 2 e 3)

- [ ] **`.codebase-memory/graph.db.zst` versionado** — commitar o grafo (já gerado com `persistence:true`);
  tirar do .gitignore se estiver. Quem clona navega sem reindexar.
- [ ] **`tests-prove-fix`** — job de CI que roda os testes alterados da PR contra a base e exige que
  falhem sem a mudança (gate RED automatizado). Lógica em `scripts/ci/`, testada.
- [ ] **Changelog atômico** — `changelog.d/<n>.<cat>.md` por PR que toca `src/`; `changelog.yml` valida.
- [ ] **SHA-pin** nas actions do CI (`actions/checkout@<sha>`, não `@v4` móvel).
- [ ] **`links.yml`** — links markdown internos por PR, externos em cron.
- [ ] **Review-skill no repo** (`.agents/skills/pr-review/SKILL.md`) + workflow `/review` (read-only)
  com Kiro headless. **`/fix` fica para decisão** (push automático vs commit que exige re-review —
  RFC-001 §7); começar só com `/review`.

## Decisão pendente (RFC-001 §7)
`/fix` com push automático (fakeflix) **ou** commit que exige re-review. Recomendação do Zero:
conservador (re-review) primeiro; testar o automático aqui por ser repo de baixo custo.

## Critério de aceite

- `.codebase-memory/graph.db.zst` no git; `git clone` traz o grafo.
- `tests-prove-fix` verde num PR real (e provado que reprova um teste que não pega a mudança).
- Um PR que toca `src/` sem fragmento de changelog é barrado por `changelog.yml`.
- Actions todas com SHA. `/review` por comentário funciona com Kiro.

## Gates
G0 → G3 (teste do script prove-fix) → G4 (workflows + scripts) → G5.

## Fontes
- **F3**: inventário CI do mms (`tests-prove-fix`, changelog.d, links, SHA-pin) 27/out.
- **F2**: fakeflix `cursor-pr-review.yml`/`cursor-fix.yml` (padrão /review,/fix).
