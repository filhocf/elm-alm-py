# SPEC — Repositório-ouro / CI agêntico

**Status:** PLANNED (G0) · **Release:** v0.5.0 · **RFC-mãe:** RFC-001 §5
**Padrão-ouro:** DAIA `materializacao/daia-produto-clonavel.md §Checklist` · **Classe:** gate executável

## Meta

Aplicar no elm-mcp (como PILOTO do checklist repo-ouro do DAIA) a maquinaria agêntica que faz o
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
  com Kiro headless. O agente analisa o diff e **comenta** os achados; a correção volta para o dev
  resolver localmente e re-submeter. **Sem** `/fix` automático (decisão 28/out).

## Decisão (Claudio, 28/out): SOMENTE `/review`, sem `/fix` automático
Implementar apenas o `/review` (read-only: o agente analisa a PR e comenta os achados). A correção
**volta para o dev**, que resolve na máquina local e re-submete. **NÃO** implementar `/fix` com o
agente escrevendo no repo (nem push automático, nem commit). Agente não corrige código sozinho agora.

## Critério de aceite (EARS)

- O sistema DEVE versionar `.codebase-memory/graph.db.zst`; QUANDO o repositório for clonado, o grafo DEVE vir junto (sem reindexação).
- QUANDO um PR alterar testes, o job `tests-prove-fix` DEVE rodá-los contra a base e DEVE falhar se eles não falharem sem a mudança.
- SE um PR tocar `src/` sem um fragmento `changelog.d/`, ENTÃO o CI DEVE barrá-lo.
- O sistema DEVE referenciar todas as actions do CI por SHA (não por tag móvel).
- QUANDO um comentário `/review` for postado num PR, o reviewer agêntico (Kiro) DEVE revisar o diff (read-only).

## Gates
G0 → G3 (teste do script prove-fix) → G4 (workflows + scripts) → G5.

## Fontes
- **F3**: inventário CI do mms (`tests-prove-fix`, changelog.d, links, SHA-pin) 27/out.
- **F2**: fakeflix `cursor-pr-review.yml`/`cursor-fix.yml` (padrão /review,/fix).
