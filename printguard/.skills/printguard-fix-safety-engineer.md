# Skill: PrintGuard Fix Safety Engineer

## Missão
Implementar ou revisar fixes automáticos com foco absoluto em segurança, auditabilidade e preservação do original.

## Escopo
- IFixAction
- FixPlanner
- FixEngine
- FixContext
- Fixes seguros do MVP

## Quando usar
Use esta skill para:
- criar fix novo
- revisar fix existente
- avaliar se um fix pode entrar no MVP
- proteger pipeline de escrita do PDF

## Regras duras
1. Nunca sobrescrever o original.
2. Sempre escrever em arquivo temporário.
3. Só promover saída quando a escrita for validada.
4. Todo fix precisa ser auditável.
5. Todo fix precisa ter precondições claras.
6. Se o risco for visualmente sensível, o fix não entra como automático seguro no MVP.
7. Nenhum fix é considerado sucesso sem revalidação posterior.

## Checklist técnico
- [ ] implementa `IFixAction`
- [ ] possui `Id()` estável
- [ ] possui `CanApply()` confiável
- [ ] valida precondições
- [ ] não altera original
- [ ] usa escrita segura/atômica
- [ ] registra fix em `fixes_applied`
- [ ] falha de forma segura
- [ ] possui teste de integração
- [ ] possui caminho claro de revalidação

## Fixes típicos do MVP
- NormalizeBoxesFix
- RotatePageFix
- AttachOutputIntentFix
- ConvertRgbToCmykFix
- ConvertSpotToCmykFix
- RemoveWhiteOverprintFix
- RemoveLayersFix
- RemoveAnnotationsFix

## Perguntas obrigatórias antes de aprovar um fix
- altera visual do documento?
- pode degradar saída?
- depende de heurística fraca?
- exige julgamento humano?
- pode quebrar compatibilidade do PDF?
- é reversível conceitualmente?
- é seguro rodar em lote?

## Saída esperada
- decisão: seguro, arriscado ou fora do MVP
- fix implementado ou bloqueado com justificativa
