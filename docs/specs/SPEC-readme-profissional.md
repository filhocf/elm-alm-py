# SPEC — README profissional

**Status:** DONE (G5) · **Release:** v0.4.0 · **RFC-mãe:** RFC-001 §5
**Referência:** README do orc-hestrator · **Classe:** apresentação / adoção

## Meta

README no padrão OSS de primeira linha: comunica o que é, por que existe e como usar em segundos —
não uma lista crua de tools.

## Escopo (feito)

- Banner + tagline + badges (PyPI, Python, License, CI).
- Seção "Why" (a ponte agente↔ALM) e "How it works" (diagrama de fluxo).
- Quick-start com `uvx elm-mcp` (uso real, não `uv pip install -e .` de dev).
- Config MCP correta (`uvx elm-mcp`, server name `elm`), exemplo de uso.
- Links para `docs/{TOOLS,USAGE,ARCHITECTURE,adr,roadmap,CONVENTIONS}`; status honesto.
- Zero tenant; tabela de tipos sem `defect` (código só tem task/story).

## Critério de aceite (EARS)

- O README DEVE conter badges de PyPI, versão de Python, licença e CI.
- O README DEVE explicar em que o projeto serve (seção "Why") antes da lista de tools.
- QUANDO um usuário seguir o quick-start, o sistema DEVE poder ser iniciado via `uvx elm-mcp`.
- O README NÃO DEVE conter string específica de organização nem exemplos que o código não suporta.

## Fontes
- **F3**: README do orc-hestrator (referência de padrão).
