# SPEC: Migração do elm-alm-py para MCP SDK 2.x

> PRD: `docs/PRD-mcp2x-migration.md` · Issue #35 (fecha #13, #12)

## Stack Técnico

- Python 3.10–3.13
- `mcp` SDK **2.x** (atual no PyPI: 2.3.0) — antes `>=1.9.0,<2`
- httpx (async), pydantic / pydantic-settings
- Testes: pytest + respx (mock HTTP), asyncio_mode=auto

## API 2.x — mudanças verificadas na própria lib (mcp 2.3.0)

| Item | mcp 1.x (atual) | mcp 2.x (alvo) |
|------|-----------------|----------------|
| Classe do servidor | `from mcp.server.fastmcp import FastMCP` | `from mcp.server.mcpserver import MCPServer` |
| Construtor | `FastMCP(name, instructions=...)` | `MCPServer(name, instructions=...)` — **mesma assinatura usada** |
| Decorator de tool | `@mcp.tool()` | `@mcp.tool()` — **idêntico** |
| Run | `mcp.run(transport="stdio")` | `mcp.run(transport="stdio")` — **idêntico** |
| ToolError | `mcp.server.fastmcp.exceptions.ToolError` | `mcp.server.mcpserver.exceptions.ToolError` |

Conclusão: a migração de API é **quase drop-in** (troca de nome de classe + caminho de import).
O trabalho substantivo é a **adoção de `ToolError`** e a **cobertura**.

## Arquitetura (sem mudança estrutural)

```
Client → MCPServer (stdio) → server.py (tools) → oslc.py → auth.py → ELM (OSLC XML/JSON)
```

`server.py` é a **fronteira MCP** (onde o cliente vê erros). `oslc.py`/`auth.py` são
camada interna. Decisão de erro:

- **server.py (fronteira):** erros de validação user-facing viram `ToolError`
  (mensagem legível ao cliente MCP). São os 5 `raise ValueError` atuais.
- **oslc.py (interna):** mantém `ValueError`/`RuntimeError` de domínio OSLC; quando
  borbulham até uma tool, a tool os converte em `ToolError` na borda (ou o próprio
  MCPServer serializa). Para os 6 raises de oslc.py que representam condição
  "não encontrei/ servidor recusou" e chegam ao usuário via tool, envolvemos a
  chamada na tool com tradução para `ToolError` **sem** poluir a camada OSLC com
  dependência do SDK MCP. Mantém `oslc.py` testável e desacoplado do transporte.

## Mudanças arquivo-a-arquivo

### `pyproject.toml`
- `"mcp>=1.9.0,<2"` → `"mcp>=2.3,<3"` (F3).

### `src/elm_alm_py/server.py`
- Import: `from mcp.server.mcpserver import MCPServer` + `from mcp.server.mcpserver.exceptions import ToolError`.
- `mcp = MCPServer("elm-alm-py", instructions=...)` (nome só muda a classe).
- Converter os 5 `raise ValueError` user-facing para `raise ToolError(...)`:
  - L22 invalid domain · L237 invalid type · L306 "At least one field" ·
    L341 invalid action · L351 missing ETag.
- Nas tools que chamam `oslc.*` e podem receber `ValueError`/`RuntimeError`
  "de usuário" (ex. project not found, no query capability), envolver em
  try/except e relançar como `ToolError` com a mesma mensagem.

### `src/elm_alm_py/oslc.py`
- **Sem** dependência do SDK MCP. Mantém os 6 raises de domínio
  (L71, L151, L161, L346 ValueError; L407 RuntimeError; L419 ValueError).
  A tradução para `ToolError` acontece na borda (server.py).

### `.github/workflows/ci.yml`
- `--cov-fail-under=60` → `--cov-fail-under=70` (F4), **após** a cobertura real ≥70%.

### Testes
- Atualizar `tests/` que asseveram `ValueError` em caminho user-facing para `ToolError`.
- Novos testes de `oslc.py` para subir cobertura (hoje ~67%): cobrir ramos de
  discovery não exercitados (linhas ~108–147, 163–217 do oslc.py — service provider
  lookup, query capability, creation factory por tipo).
- Teste de fumaça: `MCPServer` importa e instancia; `serve` não quebra no boot.

## Plano de testes para ≥70% (F4)

Cobertura atual: 69% total, `oslc.py` 67%. Faltam ~1–3 p.p. Alvos de teste no `oslc.py`:
- `get_catalog_url` ramos de cada domínio (rm/ccm/qm) com respostas mockadas (respx).
- `_find_query_capability` / creation factory: caminho de sucesso e de "não encontrado".
- `query_resources` com resposta XML (QM) vs JSON (CCM/RM).

## Regras de Negócio (invariantes)

1. As 12 tools mantêm nome, parâmetros e shape de retorno (F1 — compat).
2. Erro de input de tool → `ToolError` com mensagem legível (F2).
3. `serve` sobe em stdio sem `ModuleNotFoundError` (F1).
4. CI verde em 3.10–3.13 com cobertura ≥70% (F4).
5. `pyproject` sem o teto `<2` (F3).

## Riscos e Mitigações

- **Risco:** API 2.x diverge em detalhe não visto (serialização de erro, schema de tool).
  **Mitigação:** suíte de 59 testes + teste de fumaça de boot; rodar contra servidor ELM
  real antes de publicar (manual, fora do CI).
- **Risco:** `ToolError` muda a forma do erro que o cliente recebe (quebra consumidores).
  **Mitigação:** `ToolError` é o canal padrão do MCP para erro de tool — é melhoria, não
  regressão; documentar no CHANGELOG.
- **Risco:** cobertura não chega a 70% só com oslc.py.
  **Mitigação:** medir após novos testes; se faltar, cobrir ramos de erro de server.py.
- **Risco:** regressão silenciosa de tool.
  **Mitigação:** gate 5 (review) + diff de comportamento tool-a-tool.

## Versionamento

- Minor bump: `0.3.0` → `0.4.0` (nova linha de SDK, mudança de contrato de erro).
- CHANGELOG: seção `[0.4.0]` — Changed (mcp 2.x, ToolError), Removed (pin `<2`).
- Publicação PyPI via tag `v0.4.0` (workflow `publish.yml`, trusted publisher) — **após** OK.

## Gates (execução via dev-workflow)

- **G0** análise/blast radius (seven) — já parcialmente feito nesta SPEC.
- **G3** testes RED (rok) — testes que falham no estado atual e passam pós-migração.
- **G4** implementação (reg) — migração + ToolError + cobertura.
- **G5** review (tuvok) — diff, regressão, convenções.
