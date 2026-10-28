# ADR-001: Implementação OSLC própria, não fork nem lib da IBM

> Status: **ACCEPTED** (retroativo — decisão de origem, mai/2026) · 2026-10-27

## Contexto

Para falar com o IBM ELM há três caminhos: (a) forkar/embutir a lib oficial `elmclient` (Python,
IBM), (b) usar um SDK Java/Plain Java do Jazz, (c) implementar direto o protocolo **OSLC REST**
(padrão aberto OASIS que o ELM expõe).

## Decisão

Implementar **direto sobre OSLC REST**, do zero, sem depender de `elmclient` nem do SDK Jazz.
Dependências do core: só `mcp`, `httpx`, `pydantic`.

## Consequências

- **Não é fork.** O histórico começa em `Initial commit` (18/mai/2026); código autoral.
- Leve e portável (sem JVM, sem lib pesada da IBM); roda via `uvx`.
- Pagamos o custo de implementar discovery/auth/parse OSLC nós mesmos — mas ganhamos controle total
  e um pacote tenant-neutro.
- A narrativa pública (README/AGENTS) deve declarar: "MCP leve para IBM ELM via OSLC, implementação
  independente — não é fork do software da IBM".

## Fontes
- **F3**: `git log --reverse` do projeto, hoje elm-mcp (Initial commit 18/mai); `pyproject.toml` (deps = mcp/httpx/pydantic, sem elmclient).
