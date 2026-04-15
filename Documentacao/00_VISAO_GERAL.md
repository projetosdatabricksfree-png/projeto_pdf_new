# PreFlight Inspector — Visão Geral do Produto

O **PreFlight Inspector (Graphic-Pro)** é um sistema avançado de validação técnica e correção automática de arquivos PDF para a indústria gráfica. Ele foi projetado para atuar como um "gatekeeper" industrial, garantindo que arquivos de produção atendam aos rigorosos padrões da **Ghent Workgroup (GWG) 2022.1**.

## 🎯 Objetivo de Negócio

Eliminar a fricção entre o cliente (envio do arquivo) e a impressão (saída física), transformando o paradigma atual de "Detectar e Rejeitar" no novo padrão **"Upload to Print-Ready"**.

- **Minimização de Retrabalho**: Reduzir a necessidade de o cliente voltar ao Illustrator/AutoCAD para ajustes triviais.
- **Garantia Técnica**: Selo de conformidade GWG 2022.1 em todos os arquivos aprovados.
- **Eficiência Operacional**: Automação de correções geométricas e de cor sem intervenção humana.

---

## 🚀 Funcionalidades Principais

### 1. Auditoria Técnica Determinística
Ao contrário de ferramentas baseadas em heurísticas simples, o sistema utiliza agentes especializados para verificar:
- **Espaço de Cor**: Bloqueio de RGB/Lab e validação de DeviceCMYK.
- **Tipografia**: Garantia de 100% de fontes incorporadas.
- **Geometria**: Validação matemática de Bleed (Sangria), TrimBox e Margens de Segurança.

### 2. Auto-Remediação (Roadmap 2026)
Uma camada inteligente que corrige o arquivo detectado como inválido:
- **Mirror-Edge**: Gera sangria automaticamente espelhando as bordas.
- **Shrink-to-Safe**: Redimensiona o conteúdo para garantir margem de segurança.
- **Transparency Flattening**: Aclata transparências complexas para evitar erros de RIP.

### 3. Emissão de Atestado Industrial (VeraPDF)
Integração com o motor **VeraPDF**, o validador de referência da indústria, para gerar um laudo PDF/X-4 auditável que acompanha o arquivo final (`_gold.pdf`).

---

## 📈 Iniciativa "Zero Estresse" (Auto-Remediation)

Atualmente no **Sprint QA**, o projeto está evoluindo de um validador passivo para um pipeline ativo.

| Conceito | Antiga "Regra de Ouro" | Novo Paradigma Industrial |
|:---:|:---:|:---:|
| **Ação** | Rejeitar arquivos com falhas | Corrigir e entregar com auditoria |
| **Feedback** | "Corrija no Illustrator" | "Aqui está o PDF corrigido + laudo" |
| **Entrega** | Bloqueada em caso de erro | **Sempre entregue** (com alertas de degradação) |

---

> [!NOTE]
> Este documento é o ponto de entrada para stakeholders e novos desenvolvedores entenderem a proposição de valor do Graphic-Pro.
