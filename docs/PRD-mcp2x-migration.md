# PRD: Migração do elm-alm-py para MCP SDK 2.x

> Issue: #35 · Fecha também #13 (ToolError) e #12 (coverage → 70%)

## Problema

O elm-alm-py está preso ao MCP SDK 1.x por um pin defensivo (`mcp>=1.9.0,<2`,
do PR #34). O SDK 2.x removeu `mcp.server.fastmcp` (crash de boot — issue #33).
Enquanto ficarmos em 1.x:

- não recebemos correções/segurança nem novas capacidades do SDK;
- não podemos adotar o padrão de erro do 2.x (`ToolError`), que a auditoria (#13)
  pede para melhorar as mensagens de erro das tools ao cliente MCP;
- o pin acumula dívida e sinaliza "projeto parado" num produto que o roadmap
  trata como frente de evolução contínua (membrana DAIA).

## Personas

- **Primary:** agentes (Zero, T'Pol) e desenvolvedores que consomem o elm-alm-py
  como MCP server para ler/escrever no IBM ELM (RM/CCM/QM).
- **Secondary:** mantenedor (Claudio) e contribuidores externos, que precisam de um
  projeto no SDK atual para evoluir.

## Features

- [ ] **F1:** Migrar o servidor de `FastMCP` para `MCPServer` (mcp 2.x), preservando
  as 10 tools e o comportamento observável.
- [ ] **F2:** Adotar `ToolError` para erros user-facing nas tools (fecha audit #13),
  substituindo `ValueError`/`RuntimeError` nos 11 pontos atuais.
- [ ] **F3:** Remover o pin `<2` e fixar o piso em 2.x (`mcp>=2.3,<3`).
- [ ] **F4:** Elevar a cobertura para ≥70% (foco em `oslc.py`) e subir o gate do CI
  de 60 → 70 (fecha audit #12).

## Critérios de Aceitação (EARS)

- **Ubiquitous:** The system shall expose the same 10 MCP tools with unchanged names,
  parameters and return shapes after the migration.
- **Event-driven:** When a tool receives invalid input (invalid domain, unknown type,
  missing fields, invalid action), the system shall raise `ToolError` with a
  human-readable message.
- **Event-driven:** When `elm-alm-py serve` starts under mcp 2.x, the system shall boot
  without `ModuleNotFoundError` and serve over stdio.
- **State-driven:** While running the CI test matrix (Python 3.10–3.13), the system shall
  pass all tests with total coverage ≥ 70%.
- **Unwanted:** If a transport or protocol error occurs at startup, then the system shall
  fail with a clear error rather than a bare traceback.
- **Ubiquitous:** The `pyproject.toml` shall declare `mcp>=2.3,<3` and shall not contain
  the `<2` upper bound.

## Fora de Escopo

- Feature SDD/IARA (issue #29) — rastreada à parte.
- Novas tools ou mudança de contrato OSLC.
- Mudança de transporte (segue stdio).
- Reescrita de `cli.py` (excluído da cobertura, é código interativo).
