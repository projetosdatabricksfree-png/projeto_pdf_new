> **ENCERRADA** — Sprint migrada para `SPRINSTS_REFATORACAO/`. O trabalho realizado aqui foi incorporado ao novo roadmap do MVP comercial. Data de encerramento: 2026-04-19.

---

# Sprint 08 — Revalidação, Preview e Relatórios

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusão.

## Objetivo
Finalizar o ciclo de processamento técnico do PrintGuard de forma segura e visual. Implementar a revalidação obrigatória para garantir que as correções funcionaram, gerar previews para visualização do usuário e consolidar os relatórios técnicos e amigáveis.

## Escopo da Sprint
- Ciclo de Revalidação (Re-execução do motor de regras).
- Geração de Preview (Rasterização via PDFium ou MuPDF).
- Implementação de Overlay de Findings (Marcação visual no preview).
- Geração de Relatório Interno (JSON rico em detalhes técnicos).
- Geração de Relatório Cliente (JSON simplificado e traduzido).
- Consolidação de artefatos finais no Storage.

## Fora do escopo da Sprint
- Hardening operacional (performance extrema).
- Dashboard Web.

## Dependências
- Sprints 01 a 07 concluídas.
- Biblioteca `libpdfium-dev` ou similar integrada.

## Entregáveis
- [x] Pipeline completo executando análise → fix → revalidação.
- [ ] Artefatos de Preview (JPEG 1200px) gerados no Storage.
- [ ] Relatórios JSON salvos e disponíveis via API.

## Checklist Técnico

### PDF / Render
- [ ] Integrar PDFium no processo de build.
- [ ] Criar `PreviewRenderer` para gerar JPEG da página 1.
- [ ] Implementar desenho de coordenadas (bounding boxes) sobre o preview para sinalizar erros visuais.

### Analysis
- [x] Implementar lógica de comparação de findings (Initial vs PostFix).
- [x] Decidir status final: `completed` (sem bloqueios residuais) ou `manual_review_required` (se correções falharam).

### Report
- [x] Criar templates JSON para relatório técnico.
- [x] Criar dicionário de tradução para mensagens de erro ao cliente final ("Seu arquivo foi convertido para CMYK").
- [x] Agregar metadados de tempo de execução por etapa.

### Storage
- [ ] Estruturar entrega: `originals/`, `corrected/`, `previews/`, `reports/`.

### API
- [ ] Endpoint `GET /v1/jobs/{id}/report` funcional.
- [ ] Endpoint `GET /v1/jobs/{id}/artifacts` listando URLs assinadas ou caminhos relativos.

### Testes
- [ ] Testar geração de preview com PDFs complexos (transparências, muitas camadas).
- [ ] Validar se o relatório JSON é sintaticamente correto.

## Arquivos e módulos impactados
- `src/render/`
- `src/report/`
- `include/printguard/render/`
- `include/printguard/report/`

## Critérios de Aceite
- [x] O sistema gera um preview legível da primeira página.
- [x] O relatório final indica quais findings foram "RESOLVED" e quais são "PERSISTENT".
- [x] O arquivo JSON simplificado é gerado em português do Brasil.
- [x] O tempo de processamento total (end-to-end) é reportado com precisão de milissegundos.

## Riscos
- PDFium consumindo muita memória na rasterização (OOM).
- Erros na tradução das mensagens técnicas assustando o cliente leigo.

## Mitigações
- Limitar a resolução do preview a 150 DPI (suficiente para tela).
- Revisão cuidadosa das mensagens do dicionário com o PM.

## Observações de Implementação
- Preview deve ser gerado a partir do PDF CORRIGIDO.
- Se o PDF original for "irrecuperável", o preview deve ser gerado a partir do original como fallback para mostrar o erro.

## Definição de pronto
- [x] código implementado
- [x] build funcionando
- [ ] testes mínimos executados
- [ ] critérios de aceite atendidos
- [x] documentação da sprint atualizada

## Status
**Progresso da sprint:** `70%`  
**Situação:** `Em andamento`
