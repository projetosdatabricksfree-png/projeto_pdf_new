# PreFlight Inspector — GWG 2022 Certified Pipeline

![GWG Compliance](https://img.shields.io/badge/GWG_2022-Compliant-brightgreen)
![Status](https://img.shields.io/badge/Status-Production_Ready-blue)
![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-orange)

## 📌 Visão Geral

O **PreFlight Inspector** é um sistema avançado de validação técnica de arquivos PDF para a indústria gráfica, projetado especificamente para atender aos rigorosos padrões da **Ghent Workgroup (GWG) 2022.1**. 

Diferente de sistemas baseados puramente em heurísticas, este projeto utiliza uma arquitetura de **Múltiplos Agentes Especializados** para decompor a complexidade de arquivos gráficos em camadas de auditoria técnica determinística, garantindo o "Selo de Garantia GWG".

---

## 🚀 Funcionalidades Principais (Conformidade GWG 2022)

O sistema executa uma bateria de testes alinhados com a especificação **GWG 2022.1 Prepress**, focando em:

### 🎨 Gerenciamento de Cores e Tinta
- **Verificação de TAC (Total Area Coverage)**: Limites automáticos de 320%/300% (Couchê) e 260% (Não-Couchê) via amostragem profunda com `pyvips`.
- **Validação de Espaço de Cor**: Bloqueio rigoroso de elementos RGB, Lab ou Espaços de Cor Calibrados (CalRGB/ICCBased) no Nível 1.
- **Overprint Mode (OPM)**: Auditoria de estados gráficos (`ExtGState`) para garantir OPM=1 em elementos com overprint ativo, evitando erros de RIP.

### 🖋️ Tipografia e Fontes
- **Embedding 100%**: Verificação de que todas as fontes (incluindo Type1 e subsets) estão incorporadas, prevenindo substituições por Courier/Arial no RIP.

### 📐 Geometria e Camadas Técnicas
- **ISO 19593-1 (Processing Steps)**: Detecção automática de facas de corte e acabamentos através de metadados técnicos e OCGs (Optional Content Groups).
- **Detecção de Sangria (Bleed)**: Validação matemática entre `TrimBox` e `BleedBox` para garantir a segurança no corte.

---

## 🏗️ Arquitetura do Sistema

O pipeline é orquestrado por agentes autônomos que garantem escalabilidade e isolamento de falhas:

1.  **Agente Diretor (API)**: Recebe os jobs e gerencia o ciclo de vida.
2.  **Agente Gerente (Router)**: Classifica o produto (Papelaria, Editorial, Corte Especial) via geometria.
3.  **Agentes Operários (Workers)**: Executam as ferramentas técnicas específicas (V-Checks).
4.  **Agente Especialista (Probing)**: Realiza inspeção profunda quando a geometria do arquivo é ambígua.
5.  **Agente Validador (Final Auditor)**: Consolida todos os dados técnicos e emite o veredito final com o **Selo GWG**.

---

## ⚙️ Como Executar

O projeto é totalmente containerizado para garantir paridade entre ambientes:

```bash
# Subir infraestrutura (Redis + API + Workers + Frontend)
docker-compose up -d --build

# Executar diagnóstico de conformidade GWG interno
docker exec projeto_validador-worker-1 python3 scripts/diagnostico_gwg.py
```

### Endpoints Principais:
- **API**: `http://localhost:8001/api/v1`
- **Dashboard**: `http://localhost:5173`

---

## 📊 Relatórios e Diagnóstico

O sistema gera laudos em JSON (para integração) e PDF (para o cliente final), incluindo:
- **Resumo Executivo**: Aprovado / Reprovado / Aprovado com Ressalvas.
- **Badge de Conformidade**: `GWG_2022_COMPLIANT` ou `NON_COMPLIANT`.
- **Mapeamento de Erros**: Identificação das páginas e elementos que violam as normas.

---

## 🛠️ Tecnologias Utilizadas
- **Backend**: Python 3.11, FastAPI, Celery.
- **Processamento PDF**: Ghostscript (Auditoria Profunda), PyMuPDF (Manipulação), ExifTool (Metadados).
- **Processamento de Imagem**: `pyvips` (Anti-OOM e análise de TAC).
- **Interface**: React, Vite, TailwindCSS.

---

## 📈 Conformidade GWG Suite 5.0
Este sistema é testado diariamente contra a **Ghent PDF Output Suite 5.0**, garantindo que as lógicas de overprint, transparência e separação de cores estejam sempre sincronizadas com as melhores práticas mundiais da indústria gráfica.

---
*Este projeto é parte da iniciativa de automação técnica para gráficas modernas.*
