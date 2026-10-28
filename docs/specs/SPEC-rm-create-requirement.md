# SPEC — RM create/update requirement (escrita no DOORS Next)

**Status:** DONE (G5) · **Release:** v0.5.0 · **RFC-mãe:** RFC-001 §5
**Pesquisa:** `pesquisa-apis-elm.md §2` · `levantamento-interno-alm.md §A.6/§B.7`
**Classe:** entregável de produto — maior gap da membrana DAIA

## Meta

Expor escrita de requisito no domínio RM (DOORS Next) via OSLC, fechando o gap nº 1 pedido pelo DAIA:
hoje o elm-mcp lê RM mas não cria/atualiza. O jandaia já faz via `publicar_elm.py` (requirementFactory,
`jazz_rm:primaryText` em XHTML, vínculo a pasta via `nav:parent`).

## Escopo

- Tool `create_requirement(project, title, content, folder=None, type=None, custom_fields=None)` —
  POST na requirementFactory do RM; conteúdo HTML sanitizado para XHTML em `jazz_rm:primaryText`.
- Tool `update_requirement(uri, title=None, content=None, custom_fields=None)` — PUT com ETag.
- Descoberta do shape do tipo de requisito via discovery (depende de `SPEC-discovery-tools`).
- Core genérico: nenhum tipo (HF/EL/ET/REG) hardcoded — vêm do perfil de adaptação / discovery.

### Decisão de MVP (G0, 28/out): escrita RM independe do discovery
O G0 (`G0-rm-write.md`) recomendou caminho RM **separado/aditivo** (não estender `create_resource`/
`_payload_to_rdfxml` do CCM — são o gargalo único da escrita CCM, risco de regressão alto). E:
`type → instanceShape` depende de `SPEC-discovery-tools`, que não está pronto. Decisão: o MVP de
escrita RM funciona **sem** shape (cria requisito base) e aceita `type`/`folder` como **URI opcional**;
quando o discovery existir, `type` por nome passa a resolver o shape. Não bloquear o write pelo discovery.

## Critério de aceite (EARS)

- QUANDO `create_requirement` for chamado com projeto, título e conteúdo, o sistema DEVE criar o
  requisito no RM e retornar sua URI e identificador.
- O sistema DEVE enviar o conteúdo como XHTML válido em `jazz_rm:primaryText`.
- ONDE um `folder` for informado, o sistema DEVE vincular o requisito à pasta (`nav:parent`).
- QUANDO `update_requirement` for chamado, o sistema DEVE usar PUT com `If-Match` (ETag); SE o ETag
  estiver obsoleto (412), ENTÃO o sistema DEVE sinalizar conflito com `ToolError` legível.
- O sistema NÃO DEVE conter tipos de requisito específicos de organização no código (vêm do perfil).

## Gates
G0 → G3 (testes RED com respx: factory, XHTML, folder, 412) → G4 → G5.

## Fontes
- **F3**: `levantamento-interno-alm.md §A.6` (publicar_elm.py: requirementFactory, primaryText, nav:parent).
- **F2**: `pesquisa-apis-elm.md §2` (OSLC RM create/update [VIA OSLC], viabilidade ALTA).
