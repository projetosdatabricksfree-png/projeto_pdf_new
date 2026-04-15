# Backlog de Produto — Iniciativa Auto-Remediação

Este documento mapeia os Épicos e User Stories para a evolução industrial do Graphic-Pro.

---

## 🏗️ Épico: Auto-Remediação Industrial (EP-01)
**Objetivo**: Transformar arquivos inválidos em "Print-Ready" (PDF/X-4) sem intervenção manual.
**Métricas de Sucesso**: 10/10 arquivos entregues no stress test final.

---

## 📅 Sprint A: Remediação Geométrica

### US-A01: BleedRemediator (mirror-edge)
**Como** sistema de remediação,  
**Quero** gerar sangria espelhando as bordas do conteúdo,  
**Para** corrigir automaticamente arquivos com erro G002 (sangria ausente).

**Critérios de Aceite:**
- [ ] Detetar erro G002.
- [ ] Espelhar 3mm da borda original.
- [ ] Garantir que a MediaBox seja expandida em 3mm por lado.
- [ ] Adicionar aviso em `quality_loss_warnings` caso haja texto na borda.

### US-A02: SafetyMarginRemediator (shrink-to-safe)
**Como** sistema de remediação,  
**Quero** escalar o conteúdo para 97%,  
**Para** garantir margem de segurança de 3mm em arquivos com erro E004.

**Critérios de Aceite:**
- [ ] Aplicar transformação `cm` centralizada.
- [ ] Verificar legibilidade (fonte mínima > 5pt).
- [ ] Registrar transformação no relatório final.

---

## 📅 Sprint B: Hardening de Cor e Transparência

### US-B01: TransparencyFlattener
**Como** motor de pré-impressão,  
**Quero** achatar grupos de transparência complexos,  
**Para** evitar erros de renderização em RIPs de offset/digital.

**Critérios de Aceite:**
- [ ] Utilizar Ghostscript com perfil de saída PDF 1.3.
- [ ] Preservar o DeviceCMYK original.
- [ ] Validar diferença visual via SSIM (Structural Similarity).

### US-B02: OutputIntent Injection
**Como** validador final,  
**Quero** injetar um perfil ICC (ISOcoated_v2) válido no arquivo,  
**Para** garantir conformidade PDF/X-4 mesmo em arquivos mal-formados.

---

## 📅 Sprint C: Auditoria Autorizativa (VeraPDF)

### US-C01: Integração VeraPDF CLI
**Como** arquiteto de qualidade,  
**Quero** rodar o validador VeraPDF em um container isolado,  
**Para** emitir um atestado industrial PDF/X-4 autorizativo.

**Critérios de Aceite:**
- [ ] Executar VeraPDF em container Docker dedicado.
- [ ] Parsear relatório JSON do VeraPDF para o banco de dados.
- [ ] Expôr atestado via endpoint `GET /api/v1/jobs/{id}/verapdf`.

---

## 🚦 Definition of Done (DoD) para toda Story

- [ ] Código revisado e sem violações de lint (`ruff`).
- [ ] Testes unitários passando com 100% de cobertura no remediador.
- [ ] Validação contra o batch de 10 PDFs reais de produção.
- [ ] Documentação técnica em `Documentacao/` atualizada.
- [ ] Nenhuma violação da **Rule 1 (Anti-OOM)** introduzida.

---

> [!NOTE]
> Prioridade das histórias segue o framework RICE, focando primeiro no maior impacto (Geometria - Sprint A).
