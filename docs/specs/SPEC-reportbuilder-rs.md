# SPEC — Relatórios (Report Builder / RS) via REST

**Status:** PLANNED (G0) · **Release:** v0.8.0 · **RFC-mãe:** RFC-001 §6
**Pesquisa:** `pesquisa-apis-elm.md §5` · **Classe:** entregável de produto — pedido do time de gestão

## Meta

Expor, para agentes/gestão, os **relatórios já montados no Report Builder** (o que o solicitante
chamou de "RS"), sem tocar o banco do ALM. O time de gestão tem vários relatórios e quer acessá-los
pelo MCP.

## Escopo

- Tool `list_reports()` — lista os relatórios disponíveis no Report Builder (JRS).
- Tool `run_report(report_id, format="json")` — executa um relatório existente e devolve o resultado
  (CSV/XML/JSON) via o endpoint REST/URL do relatório.
- Alternativa/futuro: `reportable_query(...)` sobre a **Reportable REST** por aplicação (read-only,
  herda auth/permissão da app) — para relatórios ad-hoc sem depender da stack JRS instalada.

## Restrições (de arquitetura, não negociáveis)

- O sistema NÃO DEVE acessar o banco transacional do Jazz (IBM desaconselha; sem gate de permissão;
  quebra em upgrade).
- Ordem de preferência de fonte: Report Builder (JRS) REST → Reportable REST por app → LQE/SPARQL →
  Data Warehouse (só fallback). Ver RFC-001 §6.

## Critério de aceite (EARS)

- QUANDO `list_reports` for chamado, o sistema DEVE retornar os relatórios do Report Builder acessíveis ao usuário.
- QUANDO `run_report` for chamado com um id válido, o sistema DEVE retornar o resultado no formato pedido.
- O sistema NÃO DEVE emitir consultas diretas ao banco transacional do ELM.
- SE o Report Builder não estiver disponível no ambiente, ENTÃO o sistema DEVE sinalizar com `ToolError` claro.

## Decisão em aberto
Confirmar com o time de gestão o endpoint/padrão dos relatórios do Report Builder no ambiente-alvo
(URL por relatório, autenticação) — levantar na implementação.

## Gates
G0 → G3 (mock do endpoint de relatório) → G4 → G5.

## Fontes
- **F2**: `pesquisa-apis-elm.md §5` (JRS = Report Builder + DCC + LQE; Reportable REST; DW; DB direto NÃO suportado).
