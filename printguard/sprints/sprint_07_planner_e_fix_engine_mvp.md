> **ENCERRADA** — Sprint migrada para `SPRINSTS_REFATORACAO/`. O trabalho realizado aqui foi incorporado ao novo roadmap do MVP comercial. Data de encerramento: 2026-04-19.

---

# Sprint 07 — Planner de Fixes e Fix Engine MVP

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusão.

## Objetivo
Implementar a capacidade de auto-correção do PrintGuard. O sistema deve decidir quais problemas podem ser corrigidos com segurança e aplicar as alterações no arquivo PDF usando QPDF e LittleCMS2.

## Escopo da Sprint
- Implementação do `FixPlanner` (Lógica de decisão: o que corrigir vs o que sinalizar).
- Implementação do `FixEngine` (Orquestrador de escritas no PDF).
- Fix: `NormalizeBoxesFix` (Ajuste de Media/Trim/Bleed).
- Fix: `AttachOutputIntentFix` (Anexar perfil ICC CMYK padrão).
- Fix: `ConvertRgbToCmykFix` (Conversão de espaço de cor usando LittleCMS2).
- Fix: `RemoveWhiteOverprintFix` (Segurança contra "branco que não imprime").

## Fora do escopo da Sprint
- Fixes de risco alto (Embed Fonts, Flatten Transparency).
- Revalidação pós-fix (S08).
- Geração de previews.

## Dependências
- Sprints 01 a 06 concluídas.
- Biblioteca `liblcms2-dev` instalada.

## Entregáveis
- [x] `FixPlanner` gerando lista de `IFixAction` baseada em `Findings`.
- [x] `FixEngine` gerando um novo arquivo PDF (artefato `.corrected.pdf`).
- [ ] Tabela `fixes_applied` populada com o histórico de intervenções.

## Checklist Técnico

### Common
- [ ] Integrar LittleCMS2 no CMake.
- [ ] Carregar perfil ICC padrão (ex: Fogra39 ou Coated GRACoL) como recurso do sistema.

### Fix
- [x] Implementar `NormalizeBoxesFix`: modificar dicionário `/Type /Page` na QPDF.
- [ ] Implementar `ConvertColorFix`: iterar sobre streams de imagem e cores vetoriais para converter RGB -> CMYK usando matrizes ICC.
- [ ] Implementar `MetadataFix`: remover anotações indesejadas conforme configuração.

### Worker
- [ ] Orquestrar etapa "Fixing" no pipeline principal.
- [x] Garantir que o PDF original não seja sobrescrito (Atomic Write).

### Testes
- [x] Validar integridade do PDF gerado (abrir no Acrobat ou Preview).
- [ ] Comparar cores de um PDF RGB convertido para CMYK (verificar se não houve inversão ou degradação absurda).

### Operação
- [ ] Monitorar CPU durante conversão de cor ( LittleCMS2 pode saturar o core).

## Arquivos e módulos impactados
- `src/fix/`
- `src/pdf/fixes/`
- `include/printguard/fix/`
- `resources/profiles/` (adicionar arquivos ICC)

## Critérios de Aceite
- [x] O sistema corrige um arquivo sem BleedBox criando uma baseada no MediaBox.
- [ ] O sistema converte DeviceRGB para DeviceCMYK anexando o OutputIntent correto.
- [ ] O progresso do job é atualizado para 70% após conclusão dos fixes.
- [x] Um novo arquivo PDF é criado no storage com o sufixo `.corrected.pdf`.

## Riscos
- Conversão de cor lenta em PDFs com muitas imagens de alta resolução.
- Corrupção da estrutura do PDF ao remover objetos/anotações.

## Mitigações
- Implementar timeout rígido por operação de fix.
- Usar validação estrutural da QPDF (`check()`) após cada escrita.

## Observações de Implementação
- Manter o PDF original em modo "Read Only" para o motor de fixes.
- Registrar no log exatamente quais objetos foram alterados (por ID de objeto QPDF se possível).

## Definição de pronto
- [x] código implementado
- [x] build funcionando
- [x] testes mínimos executados
- [ ] critérios de aceite atendidos
- [x] documentação da sprint atualizada

## Status
**Progresso da sprint:** `50%`  
**Situação:** `Em andamento`
