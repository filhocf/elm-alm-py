# SPEC — Repositório-ouro / CI agêntico

**Status:** IN PROGRESS (G4 — núcleo feito; resto adiado) · **Release:** v0.4.0 · **RFC-mãe:** RFC-001 §5
**Padrão-ouro:** DAIA `materializacao/daia-produto-clonavel.md §Checklist` · **Classe:** gate executável

## Meta

Aplicar no elm-mcp (como PILOTO do checklist repo-ouro do DAIA) a maquinaria agêntica que faz o
processo viajar com o repositório — não depender do harness local do dono.

## Escopo (checklist repo-ouro, camadas 2 e 3)

Feito na v0.4.0:
- [x] **`.codebase-memory/graph.db.zst` versionado** — grafo viaja com o repo (quem clona navega sem reindexar).
- [x] **`tests-prove-fix`** — job de CI que roda os testes alterados da PR contra a base e exige que
  falhem sem a mudança (gate RED automatizado). Lógica em `scripts/ci/check_tests_prove_fix.sh`.
- [x] **SHA-pin** nas actions (checkout/setup-uv/setup-python/codeql/pypi-publish), tag no comentário.

Adiado até haver contribuidores além do dono (decisão 28/out — evitar over-engineering para repo de 1 dev):
- [ ] **Changelog atômico** (`changelog.d/`) — resolve conflito de merge no CHANGELOG entre PRs
  simultâneos; hoje PRs são sequenciais, o conflito não ocorre. Adotar quando houver fluxo multi-PR.
- [ ] **`links.yml`** — baixo custo; adiar junto, entra quando a doc crescer / houver contribuição externa.
- [ ] **Review-skill + `/review` (read-only) com Kiro headless** — valor real, mas depende de credencial
  de modelo como secret no CI (GitHub-hosted) + Kiro headless no runner. Pesado/arriscado para repo
  público agora. Reavaliar com self-hosted runner ou quando o fluxo justificar. **Sem** `/fix` automático.

## Decisão (Claudio, 28/out): SOMENTE `/review`, sem `/fix` automático
Quando o `/review` for implementado: apenas read-only (o agente analisa a PR e comenta os achados). A
correção **volta para o dev**, que resolve localmente e re-submete. **NÃO** implementar `/fix` com o
agente escrevendo no repo (nem push automático, nem commit).

## Critério de aceite (EARS)

- O sistema DEVE versionar `.codebase-memory/graph.db.zst`; QUANDO o repositório for clonado, o grafo DEVE vir junto (sem reindexação). [feito]
- QUANDO um PR alterar testes, o job `tests-prove-fix` DEVE rodá-los contra a base e DEVE falhar se eles não falharem sem a mudança. [feito]
- O sistema DEVE referenciar todas as actions do CI por SHA (não por tag móvel). [feito]
- ONDE houver fluxo multi-contribuidor, o sistema DEVE adotar changelog atômico e o workflow `/review` (read-only). [adiado]

## Gates
G0 → G3 (teste do script prove-fix) → G4 (workflows + scripts) → G5.

## Fontes
- **F3**: inventário CI do mms (`tests-prove-fix`, changelog.d, links, SHA-pin) 27/out.
- **F2**: fakeflix `cursor-pr-review.yml`/`cursor-fix.yml` (padrão /review,/fix).
