# SPEC — Instalação first-class (Kiro/OpenCode/Hermes, Windows)

**Status:** PLANNED (G0) · **Release:** v0.9.0 · **RFC-mãe:** RFC-001 §5
**Pesquisa:** `pesquisa-apis-elm.md` (contexto de uso) · **Classe:** entregável de produto / adoção

## Meta

Usuário leigo instala e configura o elm-mcp sem fricção, em qualquer um dos três harnesses, com foco
especial em Windows. "Clonar/instalar → tem o MCP funcionando".

## Escopo

- Distribuição por PyPI + execução via `uvx elm-alm-py` (zero clone, zero venv manual).
- Snippet único de configuração `mcpServers` que sirva Kiro, OpenCode e Hermes (documentado).
- Guia Windows em PowerShell nativo (sem WSL); `uvx` funciona no Windows.
- `login` guiado: URL → usuário → senha → testa conexão → grava (keyring, via `SPEC-credential-keyring`)
  com mensagem de erro clara.

## Critério de aceite (EARS)

- QUANDO o usuário rodar `uvx elm-alm-py`, o sistema DEVE iniciar o MCP server sem instalação manual de venv.
- O README DEVE conter um snippet `mcpServers` pronto para Kiro, OpenCode e Hermes.
- O guia de instalação DEVE cobrir Windows em PowerShell nativo (sem WSL).
- QUANDO o `login` guiado terminar, o sistema DEVE ter validado a conexão ao ELM e gravado a credencial
  no keyring; SE a conexão falhar, ENTÃO DEVE exibir erro claro (host/credencial).

## Gates
G0 → G3 (smoke de boot via uvx; teste do login guiado com mock) → G4 → G5. Depende de `SPEC-credential-keyring`.

## Fontes
- **F3**: convenção de distribuição `uvx` (orc-hestrator publica em PyPI e roda por entry point).
