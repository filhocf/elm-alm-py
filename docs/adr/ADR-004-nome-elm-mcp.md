# ADR-004: Nome do projeto — elm-mcp

> Status: **ACCEPTED** (implementado, PR #40, v0.4.0) · 2026-10-28

## Contexto

O projeto foi publicado como `elm-alm-py` entre mai e out/2026. O nome é pouco descritivo (o sufixo
`-py` não agrega; "alm" repete "elm") e não comunica que é um **MCP server**. O autor já tinha
publicado uma primeira versão sob o nome `elm-mcp` (PyPI v0.1-0.2 e repo GitHub, mai/2026), depois
abandonada em favor do `elm-alm-py`. Verificado (28/out): tanto o pacote PyPI `elm-mcp` quanto o repo
`github.com/filhocf/elm-mcp` eram do próprio autor — nome disponível, sem bloqueio de terceiros.

## Decisão

Renomear o projeto para **`elm-mcp`** em todas as camadas:

- Distribuição PyPI: `elm-mcp`.
- Módulo Python: `elm_mcp` (`src/elm_mcp/`).
- Entry point / comando CLI: `elm-mcp`.
- Repositório GitHub: `filhocf/elm-mcp` (o antigo `elm-alm-py` redireciona).
- Diretório local de trabalho: `~/git/elm-mcp`.

O repo arquivado antigo (`elm-mcp` v0.1-0.2) foi **removido** pelo autor para liberar o nome; o repo
ativo foi renomeado `elm-alm-py` → `elm-mcp`, com o redirect automático do GitHub preservando links.

## Consequências

- Nome descritivo e alinhado ao propósito (MCP server para ELM).
- **BREAKING** para quem instalava `elm-alm-py`: o pacote PyPI muda de nome; a numeração salta para
  `0.4.0` sob o novo nome.
- A narrativa de origem fica preservada (RFC §1 e CHANGELOG do fix #33) — não se reescreve história.
- Versões antigas `elm-mcp` 0.1/0.2 no PyPI são de outra tentativa; a linha viva recomeça em 0.4.0.

## Fontes
- **F3**: verificação de disponibilidade (PyPI `/pypi/elm-mcp/json` e `gh api repos/filhocf/elm-mcp`,
  28/out) — ambos do autor. PR #40 (merge 67b8f8d) executou o rename; 80 testes verdes.
