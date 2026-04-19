# Skill: PrintGuard Report Builder

## Missão
Gerar relatórios internos e externos úteis, coerentes e derivados do estado real do job.

## Escopo
- relatório técnico interno
- relatório cliente
- delta before/after
- findings e fixes aplicados

## Quando usar
Use esta skill para:
- `JsonReportWriter`
- `ClientSummaryBuilder`
- `DeltaReportBuilder`
- contrato de saída do job

## Regras obrigatórias
1. Relatório interno deve ser auditável.
2. Relatório cliente deve ser compreensível para não técnico.
3. Não esconder pendências ou riscos remanescentes.
4. Diferenciar claramente:
   - problemas detectados
   - problemas corrigidos
   - problemas restantes
5. Basear tudo em dados reais do banco/pipeline, não em texto solto.

## Checklist técnico
- [ ] relatório interno JSON gerado
- [ ] relatório cliente JSON gerado
- [ ] findings iniciais incluídos
- [ ] findings postfix incluídos
- [ ] fixes aplicados incluídos
- [ ] delta antes/depois incluído
- [ ] mensagens amigáveis revisadas
- [ ] artefato gerado persistido no storage
- [ ] artefato registrado no banco
- [ ] testes de contrato JSON executados

## Saída esperada
- relatório técnico para operador
- relatório amigável para cliente
- base estável para integração frontend/API
