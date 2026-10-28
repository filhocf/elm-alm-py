# SPEC — Credenciais via keyring do SO

**Status:** PLANNED (G0) · **Release:** v0.9.0 · **RFC-mãe:** RFC-001 §5 · **ADR:** (criar ADR-004 ao implementar)
**Pesquisa:** análise de segurança RFC-001 (resposta à pergunta "env var no Windows?") · **Classe:** segurança

## Meta

Guardar a senha do ELM no cofre do sistema operacional (keyring), eliminando senha em texto —
substituindo o `~/.elm_creds.json` base64 (que não é cifra) e evitando variável de ambiente como padrão.

## Decisão de segurança (fundamento)

- Variável de ambiente de usuário no Windows grava a senha **em texto** no registro (HKCU) e é herdada
  por todo processo filho → antipadrão. NÃO é o padrão recomendado.
- `~/.elm_creds.json` com base64 **não é cifra** e o `chmod 600` não se aplica no Windows.
- **keyring** (Windows Credential Manager / macOS Keychain / Secret Service) cifra pelo SO, escopo por
  usuário, API cross-plataforma → **padrão recomendado**.

## Escopo

- `login` grava a senha no keyring (lib `keyring`), não mais em arquivo base64.
- O server lê a senha do keyring.
- Migração: SE existir `~/.elm_creds.json`, o `login`/primeiro uso DEVE oferecer migrar para o keyring
  e então deprecar o base64.
- Fallback: `ELM_PASSWORD` por env continua aceito para headless/CI, COM aviso de que é menos seguro.

## Critério de aceite (EARS)

- QUANDO o usuário executar `login`, o sistema DEVE armazenar a senha no keyring do SO (não em texto/base64).
- QUANDO o server iniciar, o sistema DEVE ler a credencial do keyring.
- ONDE o keyring não existir (CI/headless), o sistema DEVE aceitar `ELM_PASSWORD` por env e DEVE avisar que é menos seguro.
- O sistema NÃO DEVE gravar a senha em texto nem em base64 no disco por padrão.

## Gates
G0 → ADR-004 (keyring over env var) → G3 → G4 → G5.

## Fontes
- **F1**: comportamento de `setx`/HKCU no Windows (senha em texto, herdada por processo filho).
- **F3**: RFC-001 §8.1 (tabela de opções de armazenamento).
