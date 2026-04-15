# Estratégia de Auto-Remediação — Roadmap QA

A iniciativa de Auto-Remediação visa transformar o Graphic-Pro de um validador passivo em um pipeline ativo de correção. A meta é atingir **10/10 arquivos entregues** no batch de referência de produção.

## 🔄 Mudança de Contrato Industrial

O projeto abandonou a antiga "Regra de Ouro" (bloquear entrega se houver perda de qualidade) em favor do modelo de **Entrega Garantida com Auditoria Transparente**.

| Característica | Antes | Depois |
|:---:|:---:|:---:|
| **Sucesso da Remediação** | `False` se houvesse degradação | `True` se a correção técnica completou |
| **Status Terminal** | `GOLD_REJECTED` | `GOLD_DELIVERED` ou `GOLD_DELIVERED_WITH_WARNINGS` |
| **Pilar Central** | Prevenção de degradação | **Rastreabilidade total** da degradação |

As perdas de qualidade (ex: upsampling de imagem, substituição de fonte) agora são registradas em `quality_loss_warnings` e apresentadas no relatório final, nunca impedindo a geração do `_gold.pdf`.

---

## 🗺️ Roadmap de Implementação (Sprints)

### Sprint A — Remediação Geométrica
**Foco**: Sangria e Margem de Segurança (Causa de ~80% das reprovações).
- **BleedRemediator**: Implementação de `mirror-edge` (espelhamento de bordas).
- **SafetyMarginRemediator**: Implementação de `shrink-to-safe` (escalonamento 97% do conteúdo).
- **Inversão de Contrato**: Mudança de lógica nos remediadores de Resolução e Fontes.

### Sprint B — Hardening de Cor e Transparência
**Foco**: Garantir CMYK FOGRA39 sólido.
- **TransparencyFlattener**: Aclatamento via Ghostscript (Modo PDF 1.3).
- **OutputIntent Injection**: Injeção robusta de perfil ICC (ISOcoated_v2).
- **RGB Residual Cleanup**: Conversão automática de objetos RGB remanescentes.

### Sprint C — Validação Industrial (VeraPDF)
**Foco**: Selo de garantia autoritativo.
- **Container VeraPDF**: Isolamento da JVM para auditoria PDF/X-4.
- **Loop de Re-Remediação**: Tentativa automática de correção baseada nas regras violadas do VeraPDF.
- **Atestado para Cliente**: Endpoint para download do laudo oficial VeraPDF (JSON/PDF).

---

## 🛠️ Lógicas de Correção Detalhadas

### 1. Mirror-Edge (Sangria Automática)
Quando a TrimBox é igual à MediaBox (sem sangria), o sistema:
1. Expande a MediaBox em 3mm por lado.
2. Extrai a borda do conteúdo original (3mm).
3. Espelha horizontalmente/verticalmente essas bordas.
4. Reposiciona ao redor do conteúdo original para criar o anel de sangria.

### 2. Shrink-to-Safe (Margem de Segurança)
Se elementos críticos (texto/logos) estão a menos de 3mm da linha de corte:
1. Aplica matriz de transformação `cm` (0.97).
2. Centraliza o conteúdo.
3. Verifica se a menor fonte resultará em < 5pt (limite de legibilidade); se sim, cancela e emite alerta.

---

> [!TIP]
> **Definição de Pronto (DoD)**: Toda story de remediação deve ser testada contra **arquivos PDF reais** do batch de produção, não apenas mocks sintéticos.
