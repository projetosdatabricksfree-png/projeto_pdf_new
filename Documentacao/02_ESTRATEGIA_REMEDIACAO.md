# Estratégia de Auto-Remediação — Roadmap QA

A iniciativa de Auto-Remediação visa transformar o Graphic-Pro de um validador passivo em um pipeline ativo de correção. A meta é atingir **10/10 arquivos entregues** no batch de referência de produção.

## 🔄 Mudança de Contrato Industrial (Objetivo Sprint A)

> **Estado atual do código:** A "Regra de Ouro" original ainda está ativa. `FontRemediator` rejeita W_COURIER_SUBSTITUTION com `_fail`. `ResolutionRemediator` falha quando DPI < 300 (não upsampla). O status terminal `GOLD_REJECTED` ainda é emitido.
>
> **Objetivo:** A Sprint A irá inverter esse contrato completamente.

| Característica | Código Atual (pré-Sprint A) | Após Sprint A |
|:---:|:---:|:---:|
| **Sucesso da Remediação** | `False` se houvesse degradação de qualidade | `True` se a operação técnica completou |
| **Status Terminal** | `GOLD_APPROVED` ou `GOLD_REJECTED` | `GOLD_DELIVERED` ou `GOLD_DELIVERED_WITH_WARNINGS` |
| **Pilar Central** | Prevenção de degradação (bloquear entrega) | **Rastreabilidade total** da degradação (entregar sempre) |
| **Courier** | Hard fail — job rejeitado | Aceito como fallback + warning no relatório |
| **DPI baixo** | Hard fail — job rejeitado | Upsample bicubic Ghostscript + warning |

Após a inversão, perdas de qualidade serão registradas em `quality_loss_warnings` e nunca bloquearão a geração do `_gold.pdf`.

---

## 🗺️ Roadmap de Implementação (Sprints)

### Sprint A — Remediação Geométrica ⏳ PENDENTE
**Foco**: Sangria e Margem de Segurança (causa de ~80% das reprovações no batch de produção).
- **BleedRemediator** *(a implementar)*: Lógica `mirror-edge` — espelha os últimos 3mm da borda para gerar sangria. Trata erro G002.
- **SafetyMarginRemediator** *(a implementar)*: Lógica `shrink-to-safe` — escala conteúdo a 97% via matriz pikepdf. Trata erro E004.
- **Inversão de Contrato** *(a implementar)*: `ResolutionRemediator` passa a upsamplar com Ghostscript bicubic em vez de `_fail`; `FontRemediator` aceita Courier como fallback com warning.
- **Novos statuses terminais** *(a implementar)*: `GOLD_DELIVERED` e `GOLD_DELIVERED_WITH_WARNINGS` substituem `GOLD_APPROVED`/`GOLD_REJECTED`.

### Sprint B — Hardening de Cor e Transparência ⏳ PENDENTE
**Foco**: Garantir CMYK FOGRA39 sólido em 100% dos arquivos.
- **TransparencyFlattener** *(a implementar)*: Achatamento via Ghostscript `-dCompatibilityLevel=1.3`. Trata erro E_TGROUP_CS_INVALID.
- **OutputIntent Injection robusto** *(a implementar)*: Injeção de ISOcoated_v2_300_eci.icc nos 4 estados inválidos possíveis. Trata E_OUTPUTINTENT_MISSING.
- **RGB Residual Cleanup** *(a implementar)*: Converte objetos RGB remanescentes para DeviceCMYK FOGRA39.

### Sprint C — Validação Industrial (VeraPDF) ⏳ PENDENTE
**Foco**: Substituir check pragmático por validador autoritativo PDF/X-4.
- **Container VeraPDF** *(a implementar)*: Docker service dedicado com JVM isolada, fila `queue:verapdf`.
- **Loop de Re-Remediação** *(a implementar)*: Mapeamento de regras VeraPDF para códigos de remediador conhecidos, com até 1 retry.
- **Atestado para Cliente** *(a implementar)*: Endpoints `GET /api/v1/jobs/{id}/verapdf` e `/verapdf.pdf`.

---

## 🛠️ Lógicas de Correção Planejadas (Sprint A)

> As seções abaixo descrevem o **design de implementação** das Sprint A. Nenhuma delas existe no código atual.

### 1. Mirror-Edge (Sangria Automática) — Sprint A
Quando a TrimBox é igual à MediaBox (sem sangria), o sistema planejado irá:
1. Expandir a MediaBox em 3mm por lado.
2. Extrair a borda do conteúdo original (3mm) via PyMuPDF pixmap.
3. Espelhar horizontalmente/verticalmente essas bordas via pyvips.
4. Reposicionar ao redor do conteúdo original para criar o anel de sangria.
5. Se texto/vetor for detectado nos últimos 3mm → fallback para scale-to-bleed 102%.

### 2. Shrink-to-Safe (Margem de Segurança) — Sprint A
Se elementos críticos (texto/logos) estão a menos de 3mm da linha de corte, o sistema planejado irá:
1. Aplicar matriz de transformação `cm` (0.97) no content stream via pikepdf.
2. Centralizar o conteúdo geometricamente.
3. Verificar se a menor fonte resultará em < 5pt; se sim, manter original e emitir alerta.

---

> [!TIP]
> **Definição de Pronto (DoD)**: Toda story de remediação deve ser testada contra **arquivos PDF reais** do batch de produção, não apenas mocks sintéticos.
