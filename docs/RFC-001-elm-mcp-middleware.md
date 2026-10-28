# RFC-001: elm-mcp como middleware entre o processo agêntico e o ALM tradicional

> Status: **DRAFT** · Autor: Claudio (via Zero) · Data: 2026-10-27
> Fontes de levantamento: `conhecimentos-de-ia/ferramentas/elm-mcp/levantamento-interno-alm.md`
> e `.../pesquisa-apis-elm.md` (pesquisa OSLC/IBM, com URLs).

## 1. Propósito

Elevar o `elm-mcp` (hoje `elm-alm-py`) de "cliente OSLC read + CRUD de work item" para o
**middleware** que conecta o processo **agêntico** (DAIA/iara) ao processo **tradicional** de
ALM (IBM ELM). O MCP passa a ser a *membrana* por onde a esteira agêntica lê contexto do ALM e
publica artefatos (requisitos, work items, testes, links de rastreabilidade) de volta.

## 2. Identidade do projeto (correção de narrativa)

- **NÃO é fork.** Histórico começa em `Initial commit` (18/mai/2026); implementação própria do
  zero sobre o protocolo **OSLC REST** (padrão aberto OASIS que o IBM ELM expõe). Não depende da
  lib `elmclient` da IBM — só `mcp`, `httpx`, `pydantic`.
- Formulação correta para README/AGENTS: *"MCP server leve para IBM ELM via OSLC REST.
  Implementação independente baseada no protocolo OSLC (não é fork do software da IBM)."*
- **Neutralidade de tenant:** o core do pacote `elm_alm_py` **não cita "dataprev"** (confirmado:
  0 ocorrências no código-fonte). Pendências de limpeza:
  - `server.py:347` — default `project="MEU IMOVEL RURAL (MIR)"` em `add_child_workitem`
    (vazamento de tenant — remover/tornar obrigatório).
  - `server.py:154,256` + `README.md` + `docs/USAGE.md` — exemplos com nome de PA, host
    `alm.dataprev.gov.br`, namespaces `com.dataprev.*`/`br.gov.dataprev.*`. Mover para a camada de
    adaptação / trocar por placeholders genéricos (`https://elm.example.com`, `"MY PROJECT (KEY)"`).

## 3. Arquitetura proposta: Core genérico + Camada de adaptação

```
┌─────────────────── elm_alm_py (CORE — genérico IBM ELM/OSLC) ────────────────────┐
│  auth (Jazz form) · discovery (rootservices→catalog→SP→factory/shape/queryBase)   │
│  OSLC CRUD: CM (work item) · RM (requisito) · QM (teste) · links · reporting      │
│  Namespaces IBM/Jazz genéricos: oslc, oslc_cm, oslc_rm, rtc_cm, rtc_ext, jazz_rm, │
│  nav, calm, dcterms, process. ZERO strings de tenant.                             │
└───────────────────────────────────────────────────────────────────────────────────┘
                 ▲ descobre shapes/campos          │ fornece valores concretos
┌────────────────┴──────────────── CAMADA DE ADAPTAÇÃO (perfil por PA) ─────────────┐
│  Perfil por project area: host do servidor, nome da PA, filedAgainst/teamArea/    │
│  plannedFor, campos obrigatórios customizados, tipos custom (ex. editor.divida),  │
│  mapa de estados de workflow, pastas RM, keywords de classificação.               │
│  Preenchido via discovery (listar-tipos/listar-campos/inspecionar), NÃO no código.│
└───────────────────────────────────────────────────────────────────────────────────┘
```

A camada de adaptação equivale ao `pa_<projeto>.json` do jandaia, mas consumida pelo MCP — e é onde
"dataprev"/MIR/URLs vivem. O core só sabe falar OSLC/ELM genérico.

## 4. Documentação (ação)

- **README.md / AGENTS.md:** reescrever declarando MCP leve, OSLC-based, não-fork, tenant-neutro.
  Remover `alm.dataprev.gov.br` e qualquer "Dataprev" (trocar por `elm.example.com`/placeholder).
- **docs/SPEC.md:** está obsoleto ("Read-only: no creation" — já há 12 tools com escrita). Atualizar
  para refletir CRUD atual + a arquitetura core/adaptação desta RFC.
- **docs/USAGE.md:** trocar todos os exemplos `alm.dataprev.gov.br`/`com.dataprev.*` por genéricos.
- **Documentação completa da ferramenta** (nova): referência de todas as tools + a camada de
  adaptação (como montar um perfil de PA via discovery). Sem o nome "dataprev".

## 5. Mapa de gaps → novas funcionalidades (do levantamento interno)

12 tools atuais cobrem leitura + CRUD de work item CCM. Gaps priorizados:

### P0 — fecham a membrana agêntica (pedido explícito do DAIA)
- **G1 `create_requirement` / `update_requirement` (RM)** — maior gap. O MCP lê RM mas não escreve;
  o jandaia já cria HF/EL/ET/REG via `publicar_elm.py` (requirementFactory, `jazz_rm:primaryText`
  XHTML, `nav:parent` folder). [VIA OSLC — viabilidade ALTA]
- **G2 Discovery exposto como tools** — `list_types`/`list_shapes`, `list_fields` (campos
  obrigatórios + `allowedValues`), `inspect_workitem`, `list_folders` (RM). Sem isto o MCP não
  preenche campos obrigatórios por PA dinamicamente (base da camada de adaptação). [VIA OSLC — ALTA]
- **G3 Links OSLC cross-domínio** — "Implementa Requisito" (`calm:implementsRequirement`),
  "Testado por" (`calm:testedByTestCase`), "Afeta". Fecham a matriz AC→código→teste→ALM (fase ⑨ do
  DAIA). [VIA OSLC — ALTA]

### P1 — ciclo de teste e tipos
- **G4 QM/ETM escrita** — criar Test Case / Test Plan / Test Execution Record / Test Result + vínculo
  ao IB. Hoje só `search_testcases`. [OSLC QM 2.1 — ALTA; ETM Reportable REST p/ dados nativos]
- **G5 Tipos de WI além de task/story** — Defeito, Dívida Técnica, Risco, Impedimento (via shape
  dinâmico, não hardcode). [VIA OSLC — ALTA]

### P2 — orquestração, relatórios e conveniência
- **G6 Publicar planejamento em lote** (IB+Tarefas por sprint/marco, dedup) — orquestração sobre
  `create_workitem`. [composição — MÉDIA]
- **G7 Relatórios** — ver §7. [Reportable REST — ALTA; JRS/LQE — MÉDIA]
- **G8 Conveniência** — `setup_from_url` (extrai server+PA+id de URL do browser),
  `test_publication` (cria+apaga WI para validar perfil). [MÉDIA]

### Fora de escopo (limite da plataforma)
- Criar iteração/sprint: OSLC CCM **não** permite; é manual no EWM. O MCP só vincula (`plannedFor`).

## 6. Mapa das ações do processo (resumo)

- **jandaia/alm (tradicional):** 18 ações — discovery, listar-tipos/campos/pastas, ler/criar/atualizar
  WI, criar/atualizar requisito RM, classificar IB, inspecionar WI, publicar planejamento em lote.
- **DAIA/iara (agêntico):** trata ALM como *membrana* — lê IB para gerar spec, publica US/IB/requisito
  via MCP, fecha rastreabilidade (grava IDs/links de volta). Pedido nº 1 ao MCP: `create_requirement`.
- **PD-Dataprev (corporativo):** Gestão de Backlog (criar/priorizar/refinar IB), Planejar Iteração
  (t.1427), Detalhar IB (t.1719), criar Tarefa, vincular Requisito, registrar Teste/Defeito, fechar IB.
  (Detalhe e evidência arquivo:linha no levantamento interno.)

## 7. Relatórios (decisão de arquitetura)

Pesquisa confirmou: **não acessar o banco transacional do Jazz** (IBM/Ralph Schoon desaconselha
explicitamente; quebra em upgrade; sem gate de permissão). Ordem recomendada para o MCP:

1. **Reportable REST API por aplicação (EWM/DN/ETM)** — caminho primário: read-only, seleção de
   campos + paginação, **herda a autenticação e o controle de acesso por role da aplicação**, sem
   instalar a stack JRS, e expõe dados que o OSLC esconde (approvals, SCM, build). [ALTA]
2. **Report Builder (JRS) via REST/URL** — quando o relatório for cross-application. [MÉDIA-ALTA]
3. **LQE/SPARQL** — só para dado versionado/near-real-time. [MÉDIA]
4. **Data Warehouse via SQL/JDBC** — fallback de reporting apenas; o DW não contém todo o dado e
   não aplica permissão por PA. **Nunca** o DB transacional. [BAIXA-MÉDIA]

## 8. Instalação "first-class" (Kiro / OpenCode / Hermes) + Windows

Meta: usuário leigo instala e configura credenciais sem fricção. Propostas:
- **Distribuição:** publicar no PyPI (já há `publish.yml`) e executar via `uvx elm-alm-py`
  (zero clone, zero venv manual). Documentar o bloco `mcpServers` pronto para Kiro/OpenCode/Hermes.
- **Windows:** instruções PowerShell nativas; evitar dependência de WSL. `uvx` funciona no Windows.
- **Setup de credenciais guiado:** comando `elm-alm-py login` interativo (já existe) + um modo que
  valida a conexão e dá mensagem clara de erro. Considerar um mini-wizard (URL → usuário → senha →
  testa → grava).
- **Config de MCP padronizada:** um snippet único que sirva aos 3 harnesses.

### 8.1 Armazenamento de credenciais — análise (responde à pergunta sobre "variável de ambiente no Windows")

**Recomendação: NÃO usar variável de ambiente para a senha como padrão.** Análise:

| Opção | Segurança | Praticidade (leigo) | Veredito |
|-------|-----------|---------------------|----------|
| Variável de ambiente de **usuário** (Windows `setx`) | **Fraca** — persiste em texto no registro (HKCU\Environment), herdada por TODO processo filho, aparece em dumps/subprocess, fácil de vazar em logs. `setx` grava plaintext. | Média (precisa reabrir shell) | **Evitar como padrão** |
| Variável de ambiente só-da-sessão | Média (não persiste) | Ruim (seta toda vez) | Não |
| Arquivo `~/.elm_creds.json` (hoje, base64 + chmod 600) | Baixa-média — base64 **não é cifra**; no Windows o `chmod 600` não se aplica (ACL diferente) | Boa | Melhorar |
| **Keyring do SO** (Windows Credential Manager / macOS Keychain / Secret Service) via lib `keyring` | **Forte** — cifrado pelo SO, escopo por usuário, API uniforme cross-plataforma | Boa (transparente após login) | **Recomendado** |

**Por que a variável de ambiente é pior do que te disseram:** no Windows, senha em env var de
usuário fica **em claro** no registro e é **herdada por todo processo filho** — qualquer tool que o
agente rodar enxerga a senha. É um antipadrão de segurança reconhecido (equivale a secret em
plaintext com escopo amplo). O argumento "é melhor que arquivo" só vale contra um arquivo mal
protegido; perde para o cofre do SO.

**Proposta:**
1. **Padrão: `keyring`** — guarda a senha no **Windows Credential Manager** (e Keychain/Secret
   Service nas outras plataformas). `elm-alm-py login` grava via keyring; o server lê via keyring.
   Transparente para o usuário leigo, cifrado pelo SO, sem senha em texto em lugar nenhum.
2. **Fallback explícito:** se não houver keyring (ambiente headless/CI), aceitar `ELM_PASSWORD` por
   env **com aviso** de que é menos seguro — mas não como caminho recomendado ao usuário final.
3. **Migrar** o `~/.elm_creds.json` base64 para keyring (deprecar o base64, que não é proteção).

## 9. Plano de execução (specs/gates por incremento)

Cada item vira uma SPEC + gates (G0→G5), como a migração mcp 2.x:

1. **INC-1 (higiene/narrativa):** remover default MIR do core; limpar README/AGENTS/USAGE/SPEC.md de
   "dataprev"; declarar não-fork; atualizar SPEC.md. (baixo risco, rápido)
2. **INC-2 (adaptação):** formalizar a camada de perfil por PA + discovery como tools (G2).
3. **INC-3 (RM write):** `create_requirement`/`update_requirement` (G1) — maior valor p/ DAIA.
4. **INC-4 (rastreabilidade):** links OSLC cross-domínio (G3).
5. **INC-5 (QM write):** test case/plan/execution/result (G4) + tipos de WI (G5).
6. **INC-6 (instalação):** keyring + uvx + snippets Kiro/OpenCode/Hermes + guia Windows (§8).
7. **INC-7 (relatórios):** Reportable REST (G7).

## 10. Decisões em aberto (precisam do Claudio)
- **"RS"**: a pesquisa não achou produto ELM canônico com essa sigla. Mais provável = **Rhapsody
  Model Manager** (API Reportable REST + OSLC AM); pode ser "Reporting/JRS" ou "Root Services".
  **Confirmar o que você quis dizer com RS.**
- Ordem dos incrementos (sugiro INC-1 → INC-3 → INC-2, priorizando o `create_requirement` do DAIA).
- Nome final do projeto (`elm-alm-py` no PyPI vs `elm-mcp`).
