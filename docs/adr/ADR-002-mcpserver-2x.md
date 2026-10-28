# ADR-002: Migrar para MCP SDK 2.x (MCPServer), não permanecer em FastMCP 1.x

> Status: **ACCEPTED** (implementado, PR #38, v0.4.0) · 2026-10-27

## Contexto

O mcp 2.x removeu `mcp.server.fastmcp` (crash de boot — issue #33). O PR #34 pinou `mcp<2` como
paliativo, prendendo o projeto à linha 1.x e bloqueando a adoção de `ToolError` (audit #13).

## Decisão

Migrar para **`MCPServer`** (`mcp.server.mcpserver`), remover o teto `<2` (pin `mcp>=2.3,<3`), e
adotar `ToolError` (`mcp.server.mcpserver.exceptions`) para erros user-facing. A tradução de erros de
domínio (ValueError/RuntimeError do `oslc.py`) para `ToolError` acontece num decorator `@tool` na
**fronteira** (server.py); `oslc.py` permanece sem dependência do SDK MCP.

## Consequências

- Server no SDK atual; destrava evolução e correções de segurança do SDK.
- Mensagem de erro chega legível ao cliente (sem o wrap, o MCPServer engole a mensagem em
  `UnexpectedToolError` — provado empiricamente no G5 da migração).
- API verificada compatível: `MCPServer(name, instructions=...)`, `.tool()`, `.run(transport="stdio")`.

## Fontes
- **F3**: PR #38 (merge e92af98); migração validada com 80 testes + cobertura 79%; prova empírica do
  UnexpectedToolError no review G5 (Tuvok).
