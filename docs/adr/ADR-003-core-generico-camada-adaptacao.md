# ADR-003: Core genérico (OSLC) + camada de adaptação por project area

> Status: **ACCEPTED** · 2026-10-27 · Guia as SPECs tenant-neutral / discovery / rm-write

## Contexto

O elm-mcp precisa servir qualquer servidor IBM ELM, mas a implementação cresceu com acoplamento a
um tenant concreto: default `project="MEU IMOVEL RURAL (MIR)"` em `add_child_workitem`, exemplos com
host e namespaces de um cliente específico no README/USAGE, lógica de campos customizados nos scripts
externos (jandaia). As propriedades de work item (filedAgainst, teamArea, plannedFor, campos custom,
tipos custom, estados de workflow) **variam por servidor e por PA**.

## Decisão

Separar em duas camadas:

- **Core (`elm_mcp`)** — genérico IBM ELM/OSLC. Namespaces IBM/Jazz (oslc, oslc_cm, oslc_rm,
  rtc_cm, rtc_ext, jazz_rm, nav, calm, dcterms, process). Discovery dinâmico. CRUD RM/CCM/QM. Workflow
  genérico. **Zero strings de tenant** (nenhum nome de empresa/PA/host fixo).
- **Camada de adaptação (perfil por PA)** — host do servidor, nome da PA, filedAgainst/teamArea/
  plannedFor concretos, campos obrigatórios customizados, tipos custom, mapa de estados, pastas RM.
  Descoberta via discovery (list_types/list_fields/inspect) e persistida num perfil — nunca no código.

Princípio: **o core descobre (shapes/campos); a adaptação fornece os valores concretos**.

## Consequências

- O pacote publicado é neutro e reutilizável por qualquer organização.
- Remover já o default MIR do core (vazamento de tenant) — `SPEC-tenant-neutral`.
- A camada de adaptação equivale ao `pa_<projeto>.json` do jandaia, mas consumida pelo MCP via
  discovery — `SPEC-discovery-tools`.
- Facilita o DAIA: a membrana usa o mesmo core com um perfil DTP, sem o core saber o que é "Dataprev".

## Fontes
- **F3**: `levantamento-interno-alm.md §E` (mapa de acoplamento de tenant: default MIR em server.py:347,
  namespaces com.dataprev/br.gov.dataprev nos exemplos jandaia, tipo editor.divida).
