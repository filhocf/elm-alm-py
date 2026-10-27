# State: Migração mcp 2.x (#35)

## Status: IN_PROGRESS

## Fases
- [x] PRD created (docs/PRD-mcp2x-migration.md)
- [x] SPEC approved (docs/SPEC-mcp2x-migration.md)
- [ ] G0 — análise/blast radius
- [ ] G3 — testes RED
- [ ] G4 — implementação (migração + ToolError + coverage)
- [ ] G5 — review
- [ ] CI verde (3.10–3.13, cov ≥70%)
- [ ] PR + merge
- [ ] Release v0.4.0 (tag → PyPI) — após OK do Claudio

## Decisões
- 2026-10-27: mcp 2.x API verificada na própria lib (2.3.0): MCPServer em
  mcp.server.mcpserver (mesma assinatura de FastMCP); ToolError em
  mcp.server.mcpserver.exceptions. Migração quase drop-in.
- 2026-10-27: ToolError adotado só na FRONTEIRA (server.py). oslc.py permanece
  sem dependência do SDK MCP (desacoplado, testável); tradução na borda.
- 2026-10-27: piso de versão mcp>=2.3,<3. Bump 0.3.0 → 0.4.0.

## Próximos Passos
1. G0/G3: testes RED (incl. boot smoke + ToolError nas tools).
2. G4: migração de import/classe, ToolError, novos testes de oslc.py.
3. Subir gate CI 60→70 só após cobertura real ≥70%.
