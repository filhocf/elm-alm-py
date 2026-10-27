# State: Migração mcp 2.x (#35)

## Status: REVIEW_FIXES_DONE

## Fases
- [x] PRD created (docs/PRD-mcp2x-migration.md)
- [x] SPEC approved (docs/SPEC-mcp2x-migration.md)
- [x] G0 — análise/blast radius
- [x] G3 — testes RED
- [x] G4 — implementação (migração + ToolError + coverage)
- [x] G5 — review (Tuvok: APROVA COM RESSALVAS, 2 P1 + P2)
- [x] G5 fixes — P1-a (wrap oslc→ToolError via decorator @tool), P1-b (gate CI 60→70), P2 (teste ETag)
- [ ] CI verde no PR (3.10–3.13, cov ≥70%)
- [ ] PR + merge
- [ ] Release v0.4.0 (tag → PyPI) — após OK do Claudio

## Decisões
- 2026-10-27: mcp 2.x API verificada na própria lib (2.3.0): MCPServer em
  mcp.server.mcpserver (mesma assinatura de FastMCP); ToolError em
  mcp.server.mcpserver.exceptions. Migração quase drop-in.
- 2026-10-27: ToolError adotado na FRONTEIRA (server.py). oslc.py permanece
  sem dependência do SDK MCP (desacoplado, testável).
- 2026-10-27: piso de versão mcp>=2.3,<3. Bump 0.3.0 → 0.4.0 fica para o release.
- 2026-10-27 (G5): review provou empiricamente que ValueError cru borbulhando de
  uma tool é reembrulhado em UnexpectedToolError e a MENSAGEM é descartada
  (cliente vê só "Error executing tool X"). Correção: decorator `@tool` em
  server.py traduz ValueError/RuntimeError→ToolError na borda, preservando a
  mensagem, sem acoplar oslc.py ao SDK. Gate CI subiu 60→70 (cov real 79%).

## Resultado
- 80 testes verdes, cobertura 79% (oslc.py 86%, server.py 68%).
- ruff latest (check+format) limpo. Fecha #13 (ToolError completo) e #12 (cov≥70 + gate 70).
