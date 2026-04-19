# PrintGuard — PRD Completo  
## Sistema SaaS de Preflight e Auto-Correção de PDF para Gráficas Digitais

**Versão:** 1.0.0  
**Status:** Baseline para implementação  
**Última revisão:** Abril de 2026  
**Classificação:** Documento interno — equipe fundadora, engenharia e produto  

---

## Índice Geral

1. [Título do Produto](#1-título-do-produto)
2. [Resumo Executivo](#2-resumo-executivo)
3. [Visão do Produto](#3-visão-do-produto)
4. [Problema de Mercado](#4-problema-de-mercado)
5. [ICP — Ideal Customer Profile](#5-icp--ideal-customer-profile)
6. [Personas](#6-personas)
7. [Principais Dores do Usuário](#7-principais-dores-do-usuário)
8. [Proposta de Valor](#8-proposta-de-valor)
9. [Objetivos do Produto](#9-objetivos-do-produto)
10. [Não Objetivos](#10-não-objetivos)
11. [Premissas de Infraestrutura](#11-premissas-de-infraestrutura)
12. [Restrições Operacionais da VPS](#12-restrições-operacionais-da-vps)
13. [Escopo do MVP](#13-escopo-do-mvp)
14. [Escopo Pós-MVP](#14-escopo-pós-mvp)
15. [Jornadas do Usuário](#15-jornadas-do-usuário)
16. [Fluxo Ponta a Ponta do Sistema](#16-fluxo-ponta-a-ponta-do-sistema)
17. [Arquitetura de Alto Nível](#17-arquitetura-de-alto-nível)
18. [Arquitetura Detalhada por Módulo](#18-arquitetura-detalhada-por-módulo)
19. [Arquitetura Enxuta para 2 vCPU / 8 GB RAM](#19-arquitetura-enxuta-para-2-vcpu--8-gb-ram)
20. [Blueprint do Repositório](#20-blueprint-do-repositório)
21. [Modelo de Domínio](#21-modelo-de-domínio)
22. [Modelo de Dados](#22-modelo-de-dados)
23. [Pipeline de Execução do Job](#23-pipeline-de-execução-do-job)
24. [Engine de Análise](#24-engine-de-análise)
25. [Catálogo Inicial de Regras](#25-catálogo-inicial-de-regras)
26. [Engine de Correção](#26-engine-de-correção)
27. [Catálogo Inicial de Fixes](#27-catálogo-inicial-de-fixes)
28. [Matriz Finding → Correção](#28-matriz-finding--correção)
29. [Política de Segurança das Correções](#29-política-de-segurança-das-correções)
30. [Fixes Seguros vs. Fixes Arriscados](#30-fixes-seguros-vs-fixes-arriscados)
31. [Revalidação Pós-Correção](#31-revalidação-pós-correção)
32. [Sistema de Presets](#32-sistema-de-presets)
33. [Sistema de Validation Profiles](#33-sistema-de-validation-profiles)
34. [Estratégia de Color Management](#34-estratégia-de-color-management)
35. [Estratégia de Renderização e Preview](#35-estratégia-de-renderização-e-preview)
36. [Estratégia de Fila e Processamento Assíncrono em VPS Pequena](#36-estratégia-de-fila-e-processamento-assíncrono-em-vps-pequena)
37. [Persistência e Storage](#37-persistência-e-storage)
38. [Relatórios Internos e Externos](#38-relatórios-internos-e-externos)
39. [Contratos de API](#39-contratos-de-api)
40. [Modelo de Orquestração](#40-modelo-de-orquestração)
41. [Observabilidade](#41-observabilidade)
42. [Segurança](#42-segurança)
43. [Multi-Tenancy](#43-multi-tenancy)
44. [Escalabilidade](#44-escalabilidade)
45. [Performance e Benchmarks](#45-performance-e-benchmarks)
46. [Estratégia de Testes](#46-estratégia-de-testes)
47. [Riscos Técnicos](#47-riscos-técnicos)
48. [Trade-offs Arquiteturais](#48-trade-offs-arquiteturais)
49. [Roadmap por Milestones](#49-roadmap-por-milestones)
50. [Critérios de Aceite do MVP](#50-critérios-de-aceite-do-mvp)
51. [KPIs de Produto](#51-kpis-de-produto)
52. [KPIs Técnicos](#52-kpis-técnicos)
53. [Modelo de Monetização](#53-modelo-de-monetização)
54. [Estratégia de Rollout](#54-estratégia-de-rollout)
55. [Open Questions](#55-open-questions)
56. [Conclusão Executiva](#56-conclusão-executiva)

---

## 1. Título do Produto

# PrintGuard

**Subtítulo:** Motor SaaS de Preflight e Auto-Correção de PDF para Gráficas Digitais  
**Tagline:** *Arquivos prontos para impressão. Automaticamente.*

---

## 2. Resumo Executivo

PrintGuard é um SaaS com núcleo em C++20 que recebe arquivos PDF, executa análise técnica de pré-impressão (preflight), aplica correções automáticas quando seguro, revalida o resultado, gera previews e entrega ao usuário um conjunto completo de artefatos: o PDF original preservado, o PDF corrigido, um relatório técnico rico e um relatório amigável para o cliente final.

O produto é desenhado especificamente para o ecossistema de **gráficas digitais** — impressão sob demanda, gráficas rápidas online, bureaus de impressão digital — e não para o contexto mais restritivo e regulado da gráfica industrial offset tradicional. Essa distinção é fundamental: as tolerâncias são diferentes, os clientes são diferentes e o nível de automação viável é muito maior.

O MVP foi arquitetado para operar em produção real em uma **VPS Hostinger de entrada** (2 vCPU, 8 GB RAM, 100 GB NVMe), sem GPU, sem cluster, sem Kubernetes, sem microsserviços desnecessários. A decisão arquitetural central é **monólito modular de processo único** com processamento assíncrono controlado, concorrência limitada e storage em filesystem local na fase inicial. A stack é C++20 + PostgreSQL + filesystem local (evoluindo para MinIO/S3) com fila baseada em polling de tabela PostgreSQL no MVP, sem RabbitMQ.

O produto resolve um problema real e caro: arquivos incorretos geram reimpressões, atrasos, disputas com clientes e perda de margem. O sistema cria valor tanto para a gráfica (redução de custo operacional, menos revisão manual) quanto para o cliente final (recebe feedback imediato e arquivo corrigido em vez de e-mail de erro dois dias depois).

---

## 3. Visão do Produto

### Visão de Longo Prazo

Todo arquivo enviado para impressão digital passa automaticamente por uma camada de inteligência técnica que detecta e corrige o que pode ser corrigido, sinaliza o que precisa de atenção humana e entrega ao cliente confiança de que seu arquivo está correto — tudo isso antes de qualquer impressão acontecer.

### Posicionamento

PrintGuard não é uma ferramenta de certificação de conformidade GWG (Ghent Workgroup) para offset industrial. Não é uma solução enterprise para rotativas de grande porte. É uma plataforma de automação pragmática para um mercado que historicamente recebeu pouca atenção de software especializado: as gráficas digitais de pequeno e médio porte, os bureaus de impressão sob demanda, as gráficas online.

### Diferencial Central

A combinação de três pilares:
- **Automação real**: o sistema corrige, não apenas reporta.
- **Segurança da correção**: o sistema só corrige automaticamente quando tem alta confiança de que não vai degradar o resultado.
- **Custo de operação viável**: roda em infraestrutura barata, não exige DevOps especializado.

### Onde o produto quer estar em 3 anos

Ser a camada de preflight default integrada em plataformas de e-commerce gráfico (Hotmart Gráfica, Printi, gráficas regionais com portal próprio), oferecida como API e como SaaS white-label.

---

## 4. Problema de Mercado

### O Custo Real do Arquivo Errado

Na gráfica digital, um arquivo com problema de impressão gera uma cadeia de custos que raramente é contabilizada de forma centralizada, mas que é sistematicamente presente:

1. **Tempo de operador**: alguém precisa abrir o arquivo, identificar o problema, tentar corrigir manualmente ou comunicar ao cliente.
2. **Atraso na produção**: o job fica em espera enquanto cliente e gráfica trocam e-mails.
3. **Reimpressão**: se o erro não for detectado antes da impressão, a gráfica arca com material, tinta e tempo de máquina.
4. **Disputa com cliente**: "a arte estava assim no meu computador" é uma das frases mais frequentes do setor.
5. **Imagem da gráfica**: clientes que recebem produtos com cores erradas, textos cortados ou sangria faltando raramente voltam.

### Por Que Digital é Diferente de Industrial

O contexto de gráfica digital muda fundamentalmente o que é relevante checar e o que pode ser corrigido automaticamente:

| Aspecto | Offset Industrial | Digital (Inkjet/Laser/Toner) |
|---|---|---|
| Exigência de cor | CMYK obrigatório, FOGRA rígido | RGB frequentemente aceito, sRGB impresso razoavelmente |
| Sangria | Crítica, mínimo 3mm obrigatório | Importante mas tolerâncias variam |
| Resolução mínima | 300 DPI absoluto | 150-300 DPI dependendo do produto e distância de visualização |
| Overprint | Problema sério em litho | Menos crítico na maioria dos equipamentos digitais |
| Transparência | Flatten obrigatório para RIP offset | Maioria dos RIPs digitais modernos lidam bem |
| Fontes | Embed obrigatório sem exceção | Embed obrigatório, mas outline é fallback viável |
| TAC (Total Area Coverage) | Rígido, geralmente 300% | Varia por equipamento, 280-320% |
| Certificação | GWG, PDF/X-1a ou PDF/X-4 | Não exigida na maioria das gráficas digitais |

Essa diferença é o coração do produto: as regras devem ser calibradas para digital, não copiadas do mundo industrial.

### Tamanho do Mercado

O mercado de impressão digital no Brasil movimenta bilhões de reais por ano. Apenas no segmento de gráficas rápidas e impressão sob demanda, estima-se que há milhares de operações — de grandes plataformas como Printi até centenas de gráficas regionais com portais próprios. Não há solução de preflight automatizado acessível e nativa para esse segmento no mercado nacional. As soluções existentes são:

- **Ferramentas desktop** (Acrobat Pro + plugins, Pitstop Server): caras, instalação local, não integráveis facilmente a fluxos web.
- **Soluções enterprise** (Enfocus, Callas pdfToolbox): licenciamento de cinco dígitos, complexidade de implementação que não se encaixa em gráficas pequenas.
- **Validação manual**: o padrão atual na maioria das gráficas de médio porte.

Há uma lacuna real de mercado para uma solução como API/SaaS, acessível, automatizada e com preço proporcional ao volume.

---

## 5. ICP — Ideal Customer Profile

O cliente ideal do PrintGuard no MVP é:

**Perfil primário — Gráfica Digital com Portal Web:**
- Empresa com 3 a 30 funcionários
- Recebe entre 20 e 500 arquivos por dia via upload no próprio portal ou e-mail
- Já tem algum processo de revisão de arquivo, mas ele é manual ou semi-manual
- Sente o custo de reimpressão e atraso como dor recorrente
- Tem um desenvolvedor ou consegue contratar integração via API
- Está em busca de automação sem precisar montar equipe de pré-impressão especializada

**Perfil secundário — Plataforma de E-commerce Gráfico:**
- Plataformas com volume alto de uploads de clientes leigos
- Necessidade de validação automática antes de aceitar pagamento ou enviar para produção
- Interesse em white-label ou integração via API com relatório embutido no fluxo de pedido

**Perfil terciário — Bureau de Impressão / Reprografia Digital:**
- Atende designers e agências
- Recebe arquivos de múltiplas fontes e origens com variação de qualidade alta
- Tem operador dedicado mas sobrecarregado

---

## 6. Personas

### 6.1 — Marcos, Dono de Gráfica Digital

- **Idade:** 38 anos
- **Operação:** Gráfica digital com 8 funcionários, atende empresas locais e tem um portal de pedidos básico
- **Volume:** ~80 arquivos recebidos por dia, 30% precisam de algum tipo de intervenção
- **Dor principal:** "Meu operador passa metade do dia corrigindo arquivo de cliente"
- **O que quer:** Menos retrabalho, menos e-mail trocado com cliente, menos impressão errada
- **Medo:** Automação que corrija algo errado e gere uma impressão pior do que o arquivo original
- **Comportamento tecnológico:** Não é desenvolvedor, mas tem alguém de TI de confiança
- **Métrica de sucesso:** Redução do tempo de operador em arquivo por mês

### 6.2 — Fernanda, Operadora de Pré-Impressão

- **Idade:** 29 anos
- **Função:** Responsável por revisar todos os arquivos antes de liberar para impressão
- **Volume:** Processa 40-80 arquivos por dia manualmente
- **Dor principal:** Tarefas repetitivas (verificar sangria, checar resolução, converter cor) que poderiam ser automáticas
- **O que quer:** Uma ferramenta que já entregue o relatório pronto e o arquivo corrigido, deixando para ela apenas os casos que realmente precisam de julgamento humano
- **Medo:** Perder controle sobre o que foi alterado no arquivo do cliente
- **Comportamento tecnológico:** Usa Acrobat Pro, conhece nomenclatura técnica, vai ler relatórios detalhados
- **Métrica de sucesso:** Número de arquivos que ela não precisa tocar manualmente

### 6.3 — Rafael, Designer Freelancer

- **Idade:** 26 anos
- **Função:** Designer que entrega arquivos para gráficas em nome dos seus clientes
- **Volume:** 5-20 arquivos por semana
- **Dor principal:** Atraso de produção quando o arquivo é rejeitado pela gráfica com feedback pouco claro ("arquivo com problemas")
- **O que quer:** Saber antes de enviar se o arquivo está OK, e receber um feedback compreensível quando não está
- **Medo:** Não entender o que a gráfica está pedindo para corrigir
- **Comportamento tecnológico:** Usa Adobe CC, familiaridade média com conceitos de impressão
- **Métrica de sucesso:** Zero rejeição de arquivo ao enviar para gráfica

### 6.4 — Carla, Cliente Final Leiga

- **Idade:** 44 anos
- **Função:** Proprietária de pequeno negócio, encomenda cartão de visita e flyer no portal online
- **Volume:** 2-4 pedidos por ano
- **Dor principal:** Enviou um arquivo, recebeu um e-mail técnico incompreensível, não sabe o que fazer
- **O que quer:** Uma resposta clara em português simples sobre o que está errado e, idealmente, que a gráfica corrija sozinha
- **Medo:** Pagar e receber algo feio ou errado
- **Comportamento tecnológico:** Usa Canva, Word ou recebe arquivo de um sobrinho designer
- **Métrica de sucesso:** Processo de pedido sem fricção, confiança no resultado

---

## 7. Principais Dores do Usuário

| Persona | Dor | Frequência | Impacto |
|---|---|---|---|
| Dono de gráfica | Reimpressão por arquivo errado | Semanal | Alto — custo direto |
| Dono de gráfica | Operador sobrecarregado com revisão | Diário | Alto — custo de pessoal |
| Operador | Tarefas repetitivas de revisão manual | Diário | Médio — produtividade |
| Operador | Falta de rastreabilidade do que foi alterado | Por job | Médio — risco jurídico |
| Designer | Feedback vago de rejeição pela gráfica | Por projeto | Médio — atraso de entrega |
| Designer | Não sabe checar arquivo sem Acrobat Pro | Por projeto | Médio — dependência de ferramenta |
| Cliente leigo | Não entende mensagem técnica de erro | Por pedido | Alto — abandono de pedido |
| Cliente leigo | Recebe produto final com defeito de impressão | Por pedido | Alto — perda de confiança |

---

## 8. Proposta de Valor

### Para a Gráfica Digital

> "Pare de pagar operador para olhar arquivo e comece a pagar operador para supervisionar exceções."

PrintGuard automatiza a triagem e correção de até 80% dos problemas mais comuns em arquivos enviados por clientes leigos. O sistema entrega:
- Redução do tempo de pré-impressão manual em até 70% nos casos comuns
- Auditoria completa de cada intervenção feita no arquivo
- Relatório técnico para o operador revisar casos complexos
- Relatório amigável para encaminhar diretamente ao cliente

### Para o Designer

> "Saiba antes de enviar."

O designer pode usar a API ou a interface web para validar o arquivo antes de enviar à gráfica, recebendo feedback claro sobre o que precisa ser ajustado e, quando possível, o arquivo já corrigido para baixar diretamente.

### Para o Cliente Final Leigo

> "Envie seu arquivo. Nós cuidamos do resto."

O cliente final não precisa entender nada de preflight. O sistema detecta os problemas, corrige os que pode, e quando não consegue, explica em português simples o que precisa ser feito, com exemplos visuais.

---

## 9. Objetivos do Produto

### Objetivos de Negócio

1. Lançar MVP comercialmente viável em 90 dias de desenvolvimento
2. Conseguir as primeiras 5 gráficas pagantes como clientes piloto em 30 dias após lançamento
3. Atingir 50 tenants ativos em 6 meses
4. Gerar receita recorrente suficiente para cobrir infraestrutura e desenvolvimento em 4 meses

### Objetivos de Produto

1. Processar um PDF completo (até 20 páginas, 50 MB) em menos de 60 segundos em condições normais de operação na VPS descrita
2. Detectar os 15 problemas mais frequentes em arquivos de gráfica digital com taxa de falso negativo abaixo de 5%
3. Corrigir automaticamente e com segurança pelo menos 8 desses problemas sem intervenção humana
4. Gerar preview de primeira página com qualidade suficiente para visualização de overlay de problemas
5. Nunca corromper o PDF original — o arquivo recebido é sempre preservado intacto

### Objetivos Técnicos

1. Rodar de forma estável em VPS Hostinger 2 vCPU / 8 GB RAM / sem GPU
2. Manter uptime acima de 99% (excluindo janelas de manutenção programada)
3. Processar no máximo 2 jobs leves simultaneamente (ou 1 job pesado) com fila controlada
4. Garantir que nenhum job individual consuma mais de 1,5 GB de RAM
5. Ter cobertura de testes unitários acima de 80% nos módulos críticos (rules, fixes, planner)

---

## 10. Não Objetivos

O que PrintGuard **não é e não pretende ser** no MVP e no horizonte de produto descrito neste documento:

1. **Não é uma ferramenta de certificação GWG ou ISO 15930** (PDF/X). Não estamos construindo um verificador de conformidade para offset industrial certificado.

2. **Não é um RIP (Raster Image Processor)**. O sistema não processa arquivos para impressão direta; ele valida e corrige arquivos para que cheguem ao RIP da gráfica em melhores condições.

3. **Não é um editor de PDF de uso geral**. O escopo de edição é estritamente limitado a correções de preflight com lógica determinística e auditável.

4. **Não substitui o julgamento artístico**. O sistema não decide se o layout é bonito, se as cores são adequadas ao conceito visual ou se o conteúdo está correto do ponto de vista criativo.

5. **Não é um sistema de aprovação de conteúdo**. Não valida conteúdo textual, não checa grafia, não avalia imagens quanto ao conteúdo (nudez, direitos autorais, etc.).

6. **Não tem OCR ou extração de texto semântico** no escopo atual.

7. **Não suporta outros formatos além de PDF** no MVP (sem suporte a EPS, AI, INDD, TIFF, etc. como entrada primária).

8. **Não cria provas de cor calibradas** (soft proofing). Gera preview funcional para visualização de overlay, não para prova de cor crítica.

9. **Não oferece autoscaling automático** ou arquitetura distribuída no MVP. Isso é explicitamente fora do escopo até que haja volume e receita que justifiquem.

10. **Não opera como ferramenta desktop**. É exclusivamente SaaS/API.

---

## 11. Premissas de Infraestrutura

As premissas a seguir são fixas no escopo deste PRD e devem ser assumidas como verdade pela equipe de engenharia ao tomar decisões arquiteturais:

| Premissa | Detalhe |
|---|---|
| Plataforma de hospedagem | Hostinger VPS |
| vCPU | 2 núcleos virtuais (compartilhados) |
| RAM | 8 GB |
| Armazenamento | 100 GB NVMe SSD |
| Largura de banda | 8 TB/mês |
| GPU | Não disponível |
| IP fixo | Sim (VPS Hostinger inclui) |
| SO | Ubuntu 22.04 LTS ou Debian 12 |
| Cluster | Não — servidor único |
| Kubernetes | Fora do escopo no MVP |
| Orquestrador de containers | Docker Compose (opcional, como conveniência de deploy, não como camada de produção obrigatória) |
| Banco de dados | PostgreSQL 15+ local na própria VPS |
| Broker de mensagens | Não usado no MVP — fila via PostgreSQL |
| Object storage | Filesystem local organizado no MVP, com abstração para S3/MinIO no futuro |
| CDN | Não no MVP (arquivos servidos diretamente pelo backend) |

---

## 12. Restrições Operacionais da VPS

Esta seção define as restrições operacionais que o sistema deve respeitar para funcionar de forma estável na infraestrutura descrita. Todas as decisões de arquitetura devem ser lidas à luz dessas restrições.

### 12.1 — Memória

Com 8 GB de RAM total e considerando SO, PostgreSQL, processo de API e worker:

| Componente | Alocação estimada de RAM |
|---|---|
| Sistema operacional + overhead | ~800 MB |
| PostgreSQL (com configuração conservadora) | ~1.0–1.5 GB (shared_buffers 256 MB, effective_cache_size 2 GB) |
| Processo API (REST, sem worker) | ~150–300 MB |
| Worker (processo de preflight por job) | ~1.0–2.0 GB por job ativo |
| Buffers de I/O do kernel | ~800 MB–1 GB reservado implicitamente |
| Margem de segurança | ~500 MB |

**Conclusão:** O sistema pode processar **1 job pesado por vez com segurança**. Com PDFs pequenos (<5 páginas, <10 MB), 2 jobs simultâneos são viáveis, mas exigem monitoramento. O worker deve ter **limite rígido de memória por job** (ex.: 1.5 GB via `ulimit` ou cgroup).

### 12.2 — CPU

2 vCPUs compartilhados impõem limitações sérias. A política de concorrência deve ser:

- **Máximo 1 job de análise+correção+preview simultâneo** no MVP conservador
- Threads internas ao job: até 2 threads por operação (parseamento, renderização)
- Proibido: pool de threads ilimitado, paralelismo agressivo de múltiplos jobs
- O processo de API pode responder a requisições HTTP simultaneamente sem impactar o worker (API é leve — só persiste dados e consulta status)

### 12.3 — Disco

100 GB NVMe com a seguinte política de uso estimado:

| Uso | Estimativa |
|---|---|
| SO + binários + dependências | ~5 GB |
| PostgreSQL (dados + WAL) | ~5–10 GB |
| Uploads de arquivos (storage local) | ~40–60 GB (com política de limpeza) |
| Logs rotacionados | ~2–5 GB |
| Binários de build, cache, tmp | ~5 GB |
| Margem de segurança | ~15 GB |

**Política de retenção de arquivos obrigatória:** arquivos de jobs antigos (>30 dias ou configurável por tenant) devem ser removidos automaticamente. Implementar job de limpeza (cleaner daemon ou cron job) como parte do MVP.

### 12.4 — Rede

8 TB de largura de banda mensal é generoso para o volume inicial. Não é uma restrição crítica no MVP. Upload de arquivos grandes deve ter limite de tamanho por request para evitar saturação de I/O.

### 12.5 — Limites Operacionais Definidos para o MVP

| Item | Limite | Motivo | Impacto se exceder | Ação do sistema |
|---|---|---|---|---|
| Tamanho máximo do PDF | 80 MB | Memória: parse de PDF grande consome proporcional à estrutura do doc | Job pode consumir >2 GB RAM | Rejeitar com `rejected_by_limits`, código `FILE_TOO_LARGE` |
| Número máximo de páginas | 40 páginas | Parse + análise por página + preview | Timeout e memória | Rejeitar com `rejected_by_limits`, código `PAGE_COUNT_EXCEEDED` |
| Timeout de parse | 30 segundos | PDFs malformados podem travar parser | Job preso indefinidamente | Matar processo, marcar job como `failed`, code `PARSE_TIMEOUT` |
| Timeout de análise | 60 segundos | Análise de muitas regras em arquivo grande | CPU 100% prolongado | Interromper análise, marcar parcial, enviar para `manual_review_required` |
| Timeout de correção | 90 segundos | Fix de cor ou transparência pode ser lento | CPU 100% prolongado | Abortar fixes restantes, revalidar com o que foi feito, notificar |
| Timeout de preview | 30 segundos | Rasterização de PDF complexo | CPU 100% prolongado | Pular preview, completar job sem preview, notificar |
| Jobs simultâneos | 1 pesado / 2 leves | Memória e CPU | OOM ou deadlock | Fila — novo job entra em espera |
| Tamanho de upload por request | 100 MB | I/O e timeout de HTTP | Request travado | Rejeitar com 413 no nível da API |
| Tempo máximo de job na fila | 24 horas | SLA razoável | Job esquecido | Mover para `failed` com razão `queue_timeout` |
| Retenção de arquivos | 30 dias | Espaço em disco | Disco cheio | Limpeza automática com notificação |

---

## 13. Escopo do MVP

O MVP deve ser completo o suficiente para ser vendido comercialmente e útil para os primeiros clientes piloto. Não é uma demo — é um produto funcional com as arestas mais importantes aparadas.

### O que está no MVP

**Processamento central:**
- Recebimento de PDF via upload (API REST)
- Criação e gestão de jobs
- Parse de PDF usando QPDF (estrutura) + PDFium ou MuPDF (rendering)
- Execução do pipeline completo: análise → plano → correção → revalidação → preview → relatório
- Geração de PDF corrigido como artefato separado
- Preview JPEG da primeira página (com e sem overlay de problemas)
- Relatório JSON interno completo
- Relatório JSON simplificado para o cliente

**Regras de análise (Milestone 1):**
- Tamanho e geometria da página (MediaBox, TrimBox, BleedBox)
- Sangria (bleed) — presença e suficiência
- Espaço de cor (CMYK vs RGB, Output Intent)
- Resolução de imagens rasterizadas
- Número de páginas vs. preset

**Fixes seguros (Milestone 2):**
- NormalizeBoxesFix
- RotatePageFix
- AttachOutputIntentFix
- ConvertRgbToCmykFix
- ConvertSpotToCmykFix
- RemoveWhiteOverprintFix
- RemoveLayersFix
- RemoveAnnotationsFix

**Presets:**
- business_card (cartão de visita)
- flyer_a5
- invitation_10x15
- sticker_square
- poster_a3

**Validation Profiles:**
- digital_print_lenient
- digital_print_standard
- bw_fast_print

**Infraestrutura:**
- PostgreSQL local com fila por polling
- Filesystem local com abstração para storage
- Worker de processamento single-instance com controle de concorrência
- API REST com autenticação por API key
- Multi-tenancy lógico por tenant_id
- Logs estruturados (JSON para arquivo, rotacionados)
- Healthcheck endpoint
- Deploy via systemd (ou Docker Compose opcional)

### Tabela de Features do MVP

| Feature | Descrição | Valor para o cliente | Complexidade | Prioridade | Impacto na infra |
|---|---|---|---|---|---|
| Upload de PDF | Recebe PDF via POST multipart/form-data | Ponto de entrada do produto | Baixa | P0 | Baixo — I/O de rede |
| Criação de job | Persiste job no banco, enfileira para worker | Rastreabilidade | Baixa | P0 | Baixo |
| Parse de PDF | Extrai estrutura lógica usando QPDF | Base de todo o sistema | Alta | P0 | Médio — CPU/RAM |
| Análise de geometria | Verifica boxes, tamanho, orientação | Detecta maior categoria de erro | Média | P0 | Baixo |
| Análise de cor | Detecta RGB, espaço de cor, Output Intent | Segundo maior problema em digital | Alta | P0 | Médio |
| Análise de resolução | Detecta imagens abaixo do DPI mínimo do preset | Impacto visual direto | Média | P0 | Médio — analisa pixels |
| Análise de sangria | Verifica BleedBox vs TrimBox vs tamanho real | Corte incorreto é erro comum | Média | P0 | Baixo |
| Fix: normalizar boxes | Ajusta MediaBox/TrimBox/BleedBox inconsistentes | Corrige maioria dos erros de geometria | Média | P0 | Baixo |
| Fix: rotacionar página | Corrige orientação incorreta | Cartão de visita de pé/deitado | Baixa | P0 | Baixo |
| Fix: Output Intent | Adiciona perfil ICC ao PDF quando ausente | Melhora reprodutibilidade de cor | Baixa | P0 | Baixo |
| Fix: RGB → CMYK | Converte espaço de cor com LittleCMS2 | Reduz surpresas de cor na impressão | Alta | P1 | Alto — CPU intensivo |
| Fix: Spot → CMYK | Converte cores spot para CMYK equivalente | Relevante para gráficas sem spot | Média | P1 | Médio |
| Fix: remover overprint branco | Remove overprint em objetos brancos | Erro silencioso comum | Baixa | P1 | Baixo |
| Fix: remover layers | Flatten de layers opcionais | PDF com layers causa problemas em RIP | Baixa | P1 | Baixo |
| Fix: remover anotações | Remove comentários e anotações PDF | Anotações aparecem em impressão em alguns RIPs | Baixa | P1 | Baixo |
| Revalidação pós-fix | Executa regras novamente após correções | Garante que fix não criou novo problema | Alta | P0 | Médio |
| Preview página 1 | JPEG 1200px da primeira página | Visualização rápida do resultado | Alta | P1 | Alto — rasterização |
| Overlay de problemas | Preview com marcação visual dos findings | UX diferenciada | Alta | P1 | Médio |
| Relatório interno JSON | Findings, fixes, evidências, metadados | Debug, auditoria, operador | Média | P0 | Baixo |
| Relatório cliente JSON | Versão amigável sem jargão técnico | Comunicação com cliente final | Média | P1 | Baixo |
| Status de job | Endpoint para polling de status | Integração com frontend | Baixa | P0 | Baixo |
| Download de artefatos | URLs para PDF original, corrigido, relatórios | Entrega de valor final | Baixa | P0 | Baixo — I/O de disco |
| Multi-tenancy | Isolamento lógico por tenant_id | SaaS — múltiplos clientes | Baixa | P0 | Baixo |
| Autenticação por API key | Segurança básica | Controle de acesso | Baixa | P0 | Baixo |
| Presets de produto | Configuração de tamanho e exigências por produto | UX — cliente seleciona produto | Baixa | P0 | Baixo |
| Validation profiles | Diferentes níveis de rigor de validação | Flexibilidade comercial | Baixa | P0 | Baixo |
| Fila com polling PostgreSQL | Gestão de fila sem RabbitMQ | Simplicidade operacional | Média | P0 | Baixo |
| Controle de concorrência | Limita jobs simultâneos | Estabilidade da VPS | Média | P0 | Baixo |
| Limpeza automática de arquivos | Remove artefatos antigos | Gestão de disco | Baixa | P0 | Baixo |
| Healthcheck | Endpoint `/health` | Monitoramento | Baixa | P0 | Nulo |
| Logs estruturados | JSON logs com nível e contexto | Observabilidade | Baixa | P0 | Baixo |

---

## 14. Escopo Pós-MVP

### Fase 2 (3-6 meses após MVP)

**Fixes de risco médio:**
- EmbedFontsFix — embedding de fontes faltantes
- OutlineFontsFix — conversão de texto em outlines como fallback
- FlattenTransparencyFix — rasterização segura de transparências
- TacReductionFix — redução de cobertura total de tinta
- NormalizeBlackFix — normalização de preto puro vs. preto rico
- SafeBleedExpansionFix — expansão conservadora de sangria faltante

**Regras adicionais:**
- Detecção de overprint em objetos coloridos (não apenas brancos)
- Análise de transparência complexa
- Detecção de fontes não embarcadas
- Análise de TAC por região
- Verificação de color intent de imagens

**Produto:**
- Interface web para operadores (não apenas API)
- Modo de revisão manual com aprovação de fixes arriscados
- Webhook de notificação (job concluído, erro)
- Integração com e-mail (notificação automática ao cliente)
- Dashboard de métricas por tenant

### Fase 3 (6-12 meses)

**Capacidades avançadas:**
- RecenterArtworkFix — reposicionamento de artwork fora da área segura
- White-label para integração em portais de gráficas
- SDK JavaScript/Python para integração simplificada
- Suporte a batch upload (múltiplos PDFs em uma operação)
- SLA configurável por tenant (prioridade de fila)
- Suporte a segunda VPS (horizontal scaling com balanceamento simples)

**Possível evolução de infra:**
- Migração para MinIO para object storage
- Separação opcional do worker em processo/servidor dedicado
- Cache de ICC profiles e presets em memória

### Fora do Escopo por Enquanto

- Suporte a EPS, AI, INDD como formato de entrada
- OCR e extração de texto semântico
- Prova de cor calibrada (soft proofing)
- Certificação GWG
- Parser PDF próprio (always use QPDF)
- GPU rendering
- Kubernetes e orquestração distribuída
- Machine learning para detecção de problemas

---

## 15. Jornadas do Usuário

### 15.1 — Jornada: Gráfica Integra PrintGuard ao Portal de Pedidos

```
1. Dono de gráfica assina conta PrintGuard (tenant criado)
2. Recebe API key
3. Desenvolvedor integra endpoint de upload no fluxo de pedido:
   - Cliente faz upload de arquivo no portal
   - Portal chama PrintGuard API com o PDF + preset escolhido
   - PrintGuard retorna job_id
4. Portal exibe spinner "Analisando seu arquivo..."
5. Portal faz polling em /jobs/{id}/status até completed ou failed
6. Quando completed:
   - Portal exibe preview do arquivo com indicação visual de problemas
   - Exibe relatório amigável: "Seu arquivo foi otimizado. 2 ajustes foram feitos automaticamente."
   - Botão: "Baixar arquivo corrigido" ou "Continuar com arquivo original"
7. Cliente confirma e pedido segue para fila de impressão
8. Operador tem acesso ao relatório técnico interno para revisar casos suspeitos
```

### 15.2 — Jornada: Designer Valida Arquivo Antes de Enviar

```
1. Designer acessa interface web do PrintGuard (ou usa CLI/SDK)
2. Faz upload do PDF com o preset do produto que vai imprimir
3. Recebe feedback em <60 segundos:
   - Lista de problemas encontrados
   - O que foi corrigido automaticamente
   - O que ainda precisa de atenção manual
4. Baixa o PDF corrigido
5. Envia o arquivo corrigido para a gráfica com confiança
```

### 15.3 — Jornada: Operador Revisa Job em Manual Review

```
1. Job chega em status manual_review_required
2. Operador acessa painel interno (fase 2) ou consulta API diretamente
3. Vê o relatório técnico com:
   - Findings detalhados
   - Fixes que foram aplicados
   - Fixes que não foram aplicados e por quê
   - Preview com overlay de problemas
4. Operador decide:
   a. Aprovar fixes arriscados adicionais → sistema reabre pipeline com flag
   b. Rejeitar job e comunicar ao cliente com mensagem personalizada
   c. Marcar como aprovado manualmente, bypassando as pendências
```

---

## 16. Fluxo Ponta a Ponta do Sistema

O fluxo abaixo descreve a sequência completa desde o upload do arquivo até a entrega dos artefatos. Cada etapa é um estado discreto e rastreável no banco de dados.

```
┌─────────────────────────────────────────────────────────────────┐
│  1. UPLOAD                                                      │
│  Cliente chama POST /v1/jobs com PDF + preset + profile         │
│  API valida parâmetros, verifica limites de tamanho             │
│  Armazena PDF original em storage (filesystem local)            │
│  Cria job no banco com status = "uploaded"                      │
│  Retorna job_id imediatamente (HTTP 202)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  2. ENFILEIRAMENTO                                               │
│  Worker daemon verifica tabela jobs (SELECT FOR UPDATE SKIP)    │
│  Busca jobs em status "uploaded" ou "queued"                    │
│  Verifica slot de concorrência disponível                       │
│  Se slot livre: move job para "parsing"                         │
│  Se não: job permanece em "queued"                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  3. PARSE                                                       │
│  Worker carrega PDF do storage                                  │
│  QPDF: valida estrutura e linearidade                           │
│  Extrai: número de páginas, boxes, metadados, recursos          │
│  LittleCMS2: identifica perfis ICC embarcados                   │
│  Constrói DocumentModel em memória                              │
│  Status → "analyzed" (análise começa imediatamente)             │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  4. ANÁLISE                                                     │
│  Status → "analyzing"                                           │
│  RuleEngine executa cada IRule em sequência                     │
│  Cada regra produz 0..N Findings                                │
│  Findings persistidos na tabela findings (phase = "initial")    │
│  RuleEngine agrega resultado: nenhum blocking / tem blocking     │
│  Status → "planning_fixes"                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  5. PLANEJAMENTO DE FIXES                                       │
│  FixPlanner recebe findings, preset e validation profile        │
│  Para cada finding: verifica se há IFixAction disponível        │
│  Filtra fixes permitidos pelo validation profile                │
│  Ordena ações por prioridade e dependência                      │
│  Separa: fixes automáticos seguros / fixes que exigem review    │
│  Se todos os blocking errors têm fix seguro disponível:         │
│    → Status "fixing"                                            │
│  Se há blocking error sem fix ou com fix arriscado:             │
│    → Parte dos fixes seguros e marca "manual_review_required"   │
│  Status → "fixing"                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  6. CORREÇÃO                                                    │
│  FixEngine executa FixActions na ordem do plano                 │
│  Cada fix: opera sobre FixContext (wrapper de QPDF handle)      │
│  Fixes são atômicos por operação (write-on-complete)            │
│  Resultado de cada fix persistido em fixes_applied              │
│  Ao final: PDF corrigido salvo em storage como novo blob        │
│  Status → "revalidating"                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  7. REVALIDAÇÃO                                                 │
│  Mesmo RuleEngine executado sobre o PDF corrigido               │
│  Findings do PDF corrigido persistidos (phase = "postfix")      │
│  Compara findings inicial vs. pós-fix                           │
│  Verifica se algum blocking error persiste                      │
│  Verifica se novo problema foi introduzido                      │
│  Status → "rendering_preview"                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  8. PREVIEW                                                     │
│  PDFium (ou MuPDF): rasteriza página 1 do PDF corrigido         │
│  Gera JPEG com 1200px de largura (max)                          │
│  Gera overlay PNG com marcações de findings visuais             │
│  Salva ambos no storage                                         │
│  Status → "generating_reports"                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  9. RELATÓRIOS                                                  │
│  ReportEngine monta relatório JSON interno (rico)               │
│  ReportEngine monta relatório JSON cliente (simplificado)       │
│  Ambos salvos no storage e referenciados em artifacts           │
│  Status → "completed" (ou "manual_review_required")             │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  10. ENTREGA                                                    │
│  API expõe: GET /v1/jobs/{id}/status                            │
│  GET /v1/jobs/{id}/artifacts                                    │
│  GET /v1/jobs/{id}/report                                       │
│  URLs de download para cada artefato                            │
│  Tenant pode verificar resultado e baixar artefatos             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 17. Arquitetura de Alto Nível

### Decisão Arquitetural Central: Monólito Modular

**Contexto:** O sistema poderia ser arquitetado como microsserviços (API separada, worker separado, renderizador separado) ou como monólito modular onde múltiplos processos ou componentes internos coexistem em uma única base de código coesa.

**Decisão:** Monólito modular de processo, com separação lógica em módulos independentes mas executados no mesmo processo ou como processos distintos na mesma máquina.

**Motivo:** Uma VPS de 2 vCPU / 8 GB não tem recursos suficientes para múltiplos serviços com overhead de rede e processo. Microsserviços adicionariam latência, complexidade operacional, necessidade de service discovery, circuit breakers e monitoramento distribuído — tudo desnecessário no estágio atual. O monólito modular permite refatoração futura para separação de processos sem reescrita completa.

**Impacto:** Implantação simples, operação previsível, debugging direto, sem overhead de rede entre componentes.

**Risco:** Coupling indesejado entre módulos se a disciplina de interfaces não for mantida.

**Mitigação:** Interfaces C++ explícitas (`IRule`, `IFixAction`, `IStorage`, `IQueue`) com implementações independentes. Módulos compilados como bibliotecas estáticas separadas. Testes unitários por módulo.

### Diagrama de Componentes

```
┌─────────────────────────── VPS Única ────────────────────────────────┐
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  printguard-api (processo systemd)                            │    │
│  │  ├─ HTTP Server (lightweight, ex: cpp-httplib ou Crow)        │    │
│  │  ├─ AuthMiddleware (API key validation)                       │    │
│  │  ├─ JobController (criar, consultar, listar)                  │    │
│  │  ├─ ArtifactController (download de artefatos)               │    │
│  │  └─ StorageClient (abstração → local filesystem)              │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                              │ PostgreSQL IPC                         │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  printguard-worker (processo systemd)                         │    │
│  │  ├─ QueuePoller (SELECT jobs WHERE status = queued)           │    │
│  │  ├─ ConcurrencyGuard (limite de slots ativos)                 │    │
│  │  ├─ Pipeline Orchestrator                                     │    │
│  │  │   ├─ PdfLoader (QPDF)                                      │    │
│  │  │   ├─ RuleEngine → [IRule...]                               │    │
│  │  │   ├─ FixPlanner                                            │    │
│  │  │   ├─ FixEngine → [IFixAction...]                           │    │
│  │  │   ├─ ColorEngine (LittleCMS2)                              │    │
│  │  │   ├─ PreviewRenderer (PDFium / MuPDF)                      │    │
│  │  │   └─ ReportEngine                                          │    │
│  │  └─ StorageClient                                             │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                              │                                        │
│  ┌─────────────────┐   ┌─────────────────────────────────────────┐   │
│  │  PostgreSQL 15  │   │  Local Filesystem Storage               │   │
│  │  (localhost)    │   │  /var/printguard/storage/               │   │
│  │  jobs           │   │  ├─ originals/                          │   │
│  │  findings       │   │  ├─ corrected/                          │   │
│  │  fixes_applied  │   │  ├─ previews/                           │   │
│  │  artifacts      │   │  └─ reports/                            │   │
│  │  tenants        │   └─────────────────────────────────────────┘   │
│  │  api_keys       │                                                  │
│  └─────────────────┘                                                  │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 18. Arquitetura Detalhada por Módulo

### 18.1 — Módulo `common/`

Utilitários compartilhados entre todos os outros módulos. Não tem dependência de nenhum módulo de domínio.

**Responsabilidades:**
- Tipos de dados fundamentais (Result<T, E>, Optional patterns)
- Logging estruturado (JSON lines, com nível configurável)
- Configuração (leitura de variáveis de ambiente + arquivo de configuração)
- Hashing (SHA-256 para checksums de artefatos)
- UUID generation
- Utilitários de string e filesystem
- Medição de tempo (profiling interno)

**Decisão:** Usar `spdlog` para logging (header-only, zero overhead quando abaixo do nível configurado). Usar `nlohmann/json` para serialização JSON. Ambas são bibliotecas C++ consagradas, leves e sem dependências problemáticas.

### 18.2 — Módulo `domain/`

Estruturas de dados centrais do domínio. Zero dependência de bibliotecas externas.

```cpp
// domain/types.hpp

namespace PrintGuard {

enum class Severity {
    Info,
    Warning,
    ErrorFixable,
    ErrorBlocking
};

enum class Fixability {
    None,           // Impossível corrigir automaticamente
    Partial,        // Correção parcial disponível
    AutomaticSafe,  // Correção automática com risco mínimo
    AutomaticRisky  // Correção automática com risco moderado — requer aprovação no perfil conservador
};

struct Finding {
    std::string code;           // ex: "CLR001"
    std::string title;          // ex: "Espaço de cor RGB detectado"
    std::string description;    // descrição técnica
    Severity severity;
    Fixability fixability;
    std::string category;       // "color", "geometry", "resolution", "font", "transparency"
    std::optional<int> pageIndex; // null = problema global, N = página específica
    std::vector<std::string> evidence; // evidências textuais coletáveis
    std::string userMessage;    // mensagem amigável para relatório de cliente
};

struct FixAction {
    std::string id;          // ex: "ConvertRgbToCmykFix"
    std::string description;
    int priority;            // menor = executa primeiro
    bool risky;              // se true, exige perfil permissivo ou aprovação manual
    std::vector<std::string> dependsOn; // IDs de outros fixes que devem rodar antes
};

struct FixPlan {
    std::vector<FixAction> actions;
    std::vector<std::string> skippedFixes; // fixes possíveis mas não permitidos pelo profile
    bool hasBlockingUnresolved;
    std::vector<std::string> unresolvedFindingCodes;
};

struct JobLimits {
    size_t maxFileSizeBytes;
    int maxPageCount;
    int parseTimeoutSeconds;
    int analysisTimeoutSeconds;
    int fixTimeoutSeconds;
    int previewTimeoutSeconds;
};

} // namespace PrintGuard
```

### 18.3 — Módulo `pdf/`

Abstração sobre QPDF para operações estruturais no PDF. Isola o resto do sistema da API do QPDF.

**Responsabilidades:**
- Carregar PDF de stream ou arquivo
- Expor acesso a páginas, recursos, metadados
- Extrair informações de boxes (MediaBox, TrimBox, BleedBox, ArtBox, CropBox)
- Detectar espaços de cor de objetos
- Detectar imagens e sua resolução efetiva
- Detectar fontes e status de embedding
- Executar writes seguros (via QPDF write API)
- Validar integridade estrutural do PDF após escrita

**Estrutura do DocumentModel:**

```cpp
// pdf/document_model.hpp

struct PageGeometry {
    double mediaWidthMm;
    double mediaHeightMm;
    double trimWidthMm;
    double trimHeightMm;
    double bleedTopMm;
    double bleedRightMm;
    double bleedBottomMm;
    double bleedLeftMm;
    int rotationDegrees;
    bool hasTrimBox;
    bool hasBleedBox;
};

struct ImageResource {
    std::string xObjectRef;
    int widthPx;
    int heightPx;
    double effectiveDpi;
    std::string colorSpace;  // "DeviceRGB", "DeviceCMYK", "DeviceGray", etc.
    bool isJpeg;
    bool isMask;
};

struct FontResource {
    std::string fontName;
    std::string fontType;  // "Type1", "TrueType", "OpenType", "CIDFont"
    bool isEmbedded;
    bool isSubset;
};

struct ColorResource {
    std::string type; // "DeviceRGB", "DeviceCMYK", "DeviceGray", "Separation", "ICCBased"
    std::string iccProfileName; // se ICCBased
};

struct PageModel {
    int index;
    PageGeometry geometry;
    std::vector<ImageResource> images;
    std::vector<FontResource> fonts;
    std::vector<ColorResource> colorSpaces;
    bool hasTransparency;
    bool hasLayers;
    bool hasAnnotations;
    bool hasOverprint;
};

struct DocumentModel {
    int pageCount;
    std::vector<PageModel> pages;
    std::optional<std::string> outputIntentProfileName;
    std::string pdfVersion;
    bool isLinearized;
    bool hasEncryption;
    bool hasAcroForm;
    size_t fileSizeBytes;
};
```

### 18.4 — Módulo `color/`

Abstração sobre LittleCMS2 para operações de gerenciamento de cor.

**Responsabilidades:**
- Carregar perfis ICC do filesystem (cache em memória durante vida do processo)
- Criar transformações de cor (sRGB → CMYK, DeviceRGB → CMYK, Spot → CMYK equivalente)
- Executar conversão de pixels de imagem
- Reportar gamut warnings (quando cor RGB não tem equivalente CMYK próximo)
- Gerenciar rendering intent (Perceptual para fotos, Relative Colorimetric para gráficos planos)

**Decisão sobre Rendering Intent:** Para o MVP, usar **Perceptual** como padrão para imagens fotográficas e **Relative Colorimetric** para elementos gráficos (texto, vetores). O preset pode sobrescrever esse padrão. Não expor ao usuário final essa configuração no MVP — aplicar o default sem perguntar.

**Pools de transformação:** Transformações lcms2 são caras de criar (parsing do perfil ICC). Criar pool de transformações reutilizáveis por vida do job, não por objeto. Cache de perfis ICC por nome de arquivo.

### 18.5 — Módulo `analysis/`

Motor de análise (Rule Engine).

```cpp
// analysis/rule_engine.hpp

struct RuleContext {
    const DocumentModel& document;
    const ProductPreset& preset;
    const ValidationProfile& profile;
};

class IRule {
public:
    virtual ~IRule() = default;
    virtual std::string Id() const = 0;
    virtual std::string Category() const = 0;
    virtual std::vector<Finding> Evaluate(const RuleContext& ctx) const = 0;
};

class RuleEngine {
public:
    explicit RuleEngine(std::vector<std::unique_ptr<IRule>> rules);
    std::vector<Finding> RunAll(const RuleContext& ctx) const;
    std::vector<Finding> RunCategory(const RuleContext& ctx, 
                                      const std::string& category) const;
};
```

**Contrato de implementação de uma regra:**

- Regra é uma classe imutável — não tem estado. Pode ser compartilhada entre threads.
- `Evaluate()` é `const` — garante thread safety por design.
- Regra não modifica o DocumentModel nem o PDF.
- Regra não faz I/O.
- Regra reporta findings com evidências específicas (ex: "página 3: imagem xObj_15 com 72 DPI, esperado ≥150 DPI").

### 18.6 — Módulo `fix/`

Motor de correção (Fix Engine) e planner.

```cpp
// fix/fix_engine.hpp

struct FixContext {
    QPDF& pdf;                     // handle QPDF para escrita
    DocumentModel& document;       // modelo mutável (atualizado após cada fix)
    const ProductPreset& preset;
    const ValidationProfile& profile;
    ColorEngine& colorEngine;      // acesso para conversões
    std::vector<FixAppliedRecord>& appliedFixes; // audit trail
};

class IFixAction {
public:
    virtual ~IFixAction() = default;
    virtual std::string Id() const = 0;
    virtual bool CanApply(const FixContext& ctx, const Finding& finding) const = 0;
    virtual void Apply(FixContext& ctx, const Finding& finding) const = 0;
};
```

**FixPlanner:**

O planner decide, dado o conjunto de findings e o validation profile:
1. Quais fixes estão disponíveis para cada finding
2. Se o fix é permitido (safe vs. risky, validação do profile)
3. A ordem correta de execução (topological sort por dependências)
4. Quais findings vão ficar sem correção automática

```cpp
// fix/fix_planner.hpp

class FixPlanner {
public:
    FixPlan BuildPlan(
        const std::vector<Finding>& findings,
        const ValidationProfile& profile,
        const std::map<std::string, IFixAction*>& availableFixes
    ) const;

private:
    std::vector<FixAction> TopologicalSort(
        const std::vector<FixAction>& actions) const;
};
```

**Princípio de ordenação de fixes (prioridade definida):**

```
Priority 1: RotatePageFix, NormalizeBoxesFix          // geometria primeiro
Priority 2: RemoveLayersFix, RemoveAnnotationsFix      // simplificação estrutural
Priority 3: AttachOutputIntentFix                      // cor intent antes de conversão
Priority 4: RemoveWhiteOverprintFix                    // overprint antes de converter cor
Priority 5: ConvertSpotToCmykFix                       // spot antes de RGB (spot pode depender do espaço de cor)
Priority 6: ConvertRgbToCmykFix                        // conversão de cor principal
```

**Por que essa ordem importa:**
- Normalizar boxes primeiro garante que fixes de cor e resolução operam nas dimensões corretas.
- Remover layers antes de converter cor evita que layers ocultas sejam convertidas desnecessariamente.
- Remover overprint branco antes da conversão de cor: overprint em RGB pode criar problema diferente quando convertido para CMYK.
- Spot antes de RGB: algumas cores spot são especificadas em RGB alternativo; converter spot primeiro e depois RGB garante consistência.

### 18.7 — Módulo `render/`

Geração de preview usando PDFium ou MuPDF.

**Escolha de biblioteca de rendering:**

| Critério | PDFium | MuPDF |
|---|---|---|
| Licença | BSD/Apache (Google) | AGPL (livre) + comercial |
| Qualidade de renderização | Excelente (base do Chrome) | Excelente |
| Facilidade de integração | Build mais complexo | CMake mais simples |
| Suporte a transparência | Bom | Excelente |
| Uso em produção | Amplíssimo | Amplíssimo |
| Performance em CPU | Bom | Bom |

**Decisão:** Usar **MuPDF** no MVP pela integração CMake mais simples e licença AGPL adequada para SaaS (o serviço usa MuPDF internamente, não distribui como produto embutido). Se houver necessidade de embedding em produto distribuível no futuro, reavaliar licença comercial do MuPDF ou migrar para PDFium.

**Estratégia de renderização:**

```cpp
// render/preview_renderer.hpp

struct PreviewOptions {
    int targetWidthPx;     // padrão: 1200px
    float jpegQuality;     // padrão: 0.85
    bool generateOverlay;  // se true, gera imagem overlay com highlights
    int pageIndex;         // padrão: 0 (primeira página)
};

struct PreviewResult {
    std::vector<uint8_t> jpegData;           // preview JPEG da página
    std::optional<std::vector<uint8_t>> overlayPngData; // overlay com marcações
};

class PreviewRenderer {
public:
    PreviewResult Render(
        const std::string& pdfPath,
        const PreviewOptions& opts,
        const std::vector<Finding>& findingsToOverlay
    ) const;
};
```

**Restrições de renderização no MVP:**
- Apenas a **primeira página** é renderizada por padrão
- Renderização de outras páginas disponível como operação sob demanda (não no pipeline padrão do MVP)
- Resolução máxima de preview: 1200px de largura (suficiente para visualização web)
- JPEG com qualidade 85% (balance entre tamanho e qualidade visual)
- Overlay desenhado em C++ puro sobre o bitmap (sem dependências adicionais): retângulos coloridos com bordas semitransparentes sobre as regiões problemáticas
- Timeout rígido de 30s via `std::future` com `wait_for`

### 18.8 — Módulo `report/`

Geração de relatórios em JSON.

**Dois formatos de relatório:**

**Relatório Interno (técnico/audit):**
- Todos os findings com evidências brutas
- Todos os fixes tentados (sucesso e falha)
- Findings de pré e pós-correção
- Tempo de execução de cada etapa
- Checksums do arquivo original e corrigido
- Configuração usada (preset, validation profile)
- Versão do software e regras

**Relatório de Cliente (amigável):**
- Resumo executivo em português simples ("Seu arquivo tinha 3 ajustes necessários. Corrigimos 2 automaticamente.")
- Lista de problemas em linguagem não técnica
- Lista do que foi corrigido
- Lista do que ainda precisa de atenção (com instrução clara de como corrigir)
- Preview disponível para visualização

### 18.9 — Módulo `queue/`

Fila baseada em PostgreSQL.

```cpp
// queue/postgres_queue.hpp

class PostgresQueue {
public:
    // Tenta adquirir próximo job disponível com lock
    // Usa SELECT ... FOR UPDATE SKIP LOCKED para evitar double-processing
    std::optional<JobDescriptor> TryDequeue(int workerId);
    
    // Atualiza status do job (thread-safe via transação)
    void UpdateStatus(const std::string& jobId, JobStatus status);
    
    // Marca job como failed com motivo
    void MarkFailed(const std::string& jobId, const std::string& reason);
    
    // Retorna job para fila (ex: após crash do worker)
    void Requeue(const std::string& jobId);
    
    // Conta jobs ativos por status
    int CountActiveJobs() const;
};
```

**Polling strategy:**
- Worker faz polling a cada 2 segundos quando a fila está vazia
- Quando há job para processar: inicia imediatamente, sem espera
- `SELECT ... FOR UPDATE SKIP LOCKED` é a query central — garante que dois workers não peguem o mesmo job
- Não há busy-wait — `std::this_thread::sleep_for(2s)` entre polls quando vazio

### 18.10 — Módulo `storage/`

Abstração de storage com implementação local no MVP.

```cpp
// storage/istorage.hpp

class IStorage {
public:
    virtual ~IStorage() = default;
    
    // Salva bytes com uma chave (path lógico)
    virtual std::string Put(const std::string& key, 
                             const std::vector<uint8_t>& data) = 0;
    
    // Recupera bytes pela chave
    virtual std::vector<uint8_t> Get(const std::string& key) = 0;
    
    // Retorna URL ou path para download direto
    virtual std::string GetDownloadUrl(const std::string& key) = 0;
    
    // Remove artefato pelo key
    virtual void Delete(const std::string& key) = 0;
    
    // Verifica existência
    virtual bool Exists(const std::string& key) = 0;
};

// Implementação MVP: filesystem local
class LocalFileStorage : public IStorage { ... };

// Implementação futura: S3/MinIO
class S3Storage : public IStorage { ... };
```

**Layout de chaves no filesystem local:**

```
/var/printguard/storage/
├── {tenant_id}/
│   ├── originals/
│   │   └── {job_id}/original.pdf
│   ├── corrected/
│   │   └── {job_id}/corrected.pdf
│   ├── previews/
│   │   ├── {job_id}/preview_p0.jpg
│   │   └── {job_id}/overlay_p0.png
│   └── reports/
│       ├── {job_id}/report_internal.json
│       └── {job_id}/report_client.json
```

---

## 19. Arquitetura Enxuta para 2 vCPU / 8 GB RAM

Esta seção descreve em detalhe como o sistema deve se comportar dentro das restrições reais da VPS.

### 19.1 — Processos em Execução

O sistema opera com **dois processos principais** gerenciados pelo systemd:

```
printguard-api.service   — servidor HTTP, apenas API REST, sem processamento de PDF
printguard-worker.service — worker de pipeline, sem HTTP
```

Ambos conectam ao mesmo PostgreSQL local e ao mesmo filesystem de storage.

**Por que dois processos separados:**
- Se o worker tiver OOM (arquivo muito grande), não mata a API
- API responde a consultas de status enquanto worker processa
- Reinício do worker não interrompe requests HTTP em andamento
- Permite restart independente via systemd

### 19.2 — Controle de Concorrência

```cpp
// orchestration/concurrency_guard.hpp

class ConcurrencyGuard {
public:
    explicit ConcurrencyGuard(int maxHeavyJobs, int maxLightJobs);
    
    enum class JobWeight { Light, Heavy };
    
    // Tenta adquirir slot de processamento
    // Retorna false se não há slot disponível
    bool TryAcquireSlot(const std::string& jobId, JobWeight weight);
    
    // Libera slot após job concluído
    void ReleaseSlot(const std::string& jobId);
    
    // Classifica job com base em tamanho e número de páginas
    static JobWeight ClassifyJob(size_t fileSizeBytes, int pageCount);
};
```

**Política de classificação:**
- Job **Light**: ≤5 MB E ≤5 páginas
- Job **Heavy**: qualquer coisa acima disso

**Política de slots:**
- MVP: 1 slot heavy OU 2 slots light (nunca heavy + light simultâneos)
- Configurável via variável de ambiente `WORKER_MAX_HEAVY=1`, `WORKER_MAX_LIGHT=2`

### 19.3 — Timeouts e Processo Filho

Para garantir que um job pesado não trave o worker indefinidamente, cada pipeline de job roda em uma `std::thread` com timeout monitorado:

```cpp
// Pseudo-código de orchestração com timeout
auto future = std::async(std::launch::async, [&]() {
    return RunJobPipeline(jobDescriptor);
});

auto status = future.wait_for(std::chrono::seconds(totalTimeout));

if (status == std::future_status::timeout) {
    // Timeout atingido — não há como matar a thread em C++ padrão de forma segura
    // Estratégia: usar fork() no Linux para processo filho isolado
    // O processo filho pode ser killed com SIGKILL sem corromper o worker pai
}
```

**Estratégia de isolamento por fork:**

Para jobs de preflight, o worker usa `fork()` + `waitpid()` com timeout para isolar o processamento. O processo filho executa o pipeline completo. Se exceder o timeout, o pai manda `SIGKILL`. Essa abordagem:
- Garante que OOM de um job não derruba o worker
- Garante que timeouts são respeitados
- Permite atualização de status no banco pelo processo pai (filho atualiza via pipe ou banco diretamente)
- É uma técnica Unix clássica e confiável

**Alternativa para MVP mais simples:** Usar apenas `std::thread` com flag de cancelamento cooperativa em pontos de checkpointing do pipeline. Menos robusto contra OOM mas mais simples de implementar. **Decisão: usar fork() desde o início para robustez real.**

### 19.4 — Configuração do PostgreSQL para VPS Pequena

```ini
# /etc/postgresql/15/main/postgresql.conf — configuração conservadora para 8 GB

shared_buffers = 256MB          # 256MB é suficiente — kernel cache faz o resto
effective_cache_size = 2GB      # hint para planner
work_mem = 16MB                 # por operação de sort/hash (múltiplas por query)
maintenance_work_mem = 128MB    # para VACUUM e CREATE INDEX
max_connections = 20            # API + worker + admin — não exagerar
wal_buffers = 16MB
checkpoint_completion_target = 0.9
random_page_cost = 1.1          # NVMe SSD — cost model para random access
log_min_duration_statement = 500  # log queries acima de 500ms

# Para fila com polling: sem necessidade de pg_notify no MVP
```

**Pool de conexões:** Usar pool simples de 5 conexões no worker (libpq ou pqxx com pool próprio). API usa pool de 10 conexões. Total: 15-18 conexões — dentro do `max_connections = 20` com folga.

---

## 20. Blueprint do Repositório

```
preflight-cpp/
├── CMakeLists.txt                    # Build root — define targets, versão, opções
├── cmake/
│   ├── CompilerWarnings.cmake        # -Wall, -Wextra, -Werror, warnings tratadas como erros
│   ├── Sanitizers.cmake              # ASAN, UBSAN para builds de debug/CI
│   ├── Dependencies.cmake            # FetchContent ou find_package para deps externas
│   └── Version.cmake                 # Versionamento semântico injetado no binário
├── docs/
│   ├── architecture.md               # Este PRD e diagramas de componentes
│   ├── rule-catalog.md               # Documentação detalhada de cada regra
│   ├── fix-engine.md                 # Documentação do planner e cada fix
│   ├── api-contracts.md              # Especificação completa da REST API
│   └── presets.md                    # Documentação dos presets e como criar novos
├── third_party/                      # Dependências vendored (se não via FetchContent)
│   ├── qpdf/                         # QPDF para manipulação estrutural de PDF
│   ├── mupdf/                        # MuPDF para renderização
│   ├── lcms2/                        # LittleCMS2 para gerenciamento de cor
│   ├── nlohmann_json/                # nlohmann/json para serialização
│   ├── spdlog/                       # Logging estruturado
│   ├── libpq/                        # Driver PostgreSQL (ou libpqxx)
│   └── cpp-httplib/                  # Servidor HTTP leve (header-only)
├── config/
│   ├── presets/
│   │   ├── business_card.json        # Cartão de visita: 90x50mm, 3mm bleed, CMYK
│   │   ├── flyer_a5.json             # Flyer A5: 148x210mm, 3mm bleed
│   │   ├── invitation_10x15.json     # Convite 10x15cm
│   │   ├── sticker_square.json       # Adesivo quadrado personalizado
│   │   └── poster_a3.json            # Poster A3: 297x420mm
│   ├── validation_profiles/
│   │   ├── digital_print_lenient.json    # Permissivo: RGB permitido, baixa resolução aceita
│   │   ├── digital_print_standard.json   # Padrão: CMYK preferido, 150 DPI mín
│   │   └── bw_fast_print.json            # P&B rápido: escala de cinza, 120 DPI mín
│   └── color/
│       ├── sRGB.icc                  # Perfil fonte para conversões RGB→CMYK
│       ├── FOGRA39.icc               # Perfil CMYK para offset coated (referência)
│       └── GRACoL2013.icc            # Perfil CMYK para digital coated
├── src/
│   ├── common/                       # Logger, config, util, tipos básicos
│   │   ├── logger.cpp / logger.hpp
│   │   ├── config.cpp / config.hpp
│   │   ├── result.hpp                # Result<T,E> type
│   │   └── uuid.cpp / uuid.hpp
│   ├── domain/                       # Structs e enums de domínio puro
│   │   ├── types.hpp                 # Finding, FixAction, FixPlan, Severity, Fixability
│   │   ├── product_preset.hpp        # ProductPreset + loader de JSON
│   │   └── validation_profile.hpp   # ValidationProfile + loader de JSON
│   ├── pdf/                          # Abstração sobre QPDF
│   │   ├── document_model.hpp        # DocumentModel, PageModel, ImageResource, etc.
│   │   ├── pdf_loader.cpp            # Carrega PDF, constrói DocumentModel
│   │   └── pdf_writer.cpp            # Escreve PDF corrigido (wrapper QPDF write)
│   ├── color/                        # Abstração sobre LittleCMS2
│   │   ├── color_engine.hpp
│   │   ├── color_engine.cpp          # Transformações, cache de perfis
│   │   └── icc_profile_loader.cpp   # Carrega .icc do filesystem
│   ├── analysis/                     # Rule Engine + implementações de regras
│   │   ├── rule_engine.hpp / .cpp
│   │   ├── rules/
│   │   │   ├── geometry_rules.cpp    # PageSizeRule, BleedRule, BoxConsistencyRule
│   │   │   ├── color_rules.cpp       # ColorSpaceRule, OutputIntentRule
│   │   │   ├── resolution_rules.cpp  # ImageResolutionRule
│   │   │   └── structure_rules.cpp   # LayersRule, AnnotationsRule, EncryptionRule
│   ├── fix/                          # Fix Planner + Fix Engine + implementações
│   │   ├── fix_planner.hpp / .cpp
│   │   ├── fix_engine.hpp / .cpp
│   │   └── fixes/
│   │       ├── normalize_boxes_fix.cpp
│   │       ├── rotate_page_fix.cpp
│   │       ├── attach_output_intent_fix.cpp
│   │       ├── convert_rgb_to_cmyk_fix.cpp
│   │       ├── convert_spot_to_cmyk_fix.cpp
│   │       ├── remove_white_overprint_fix.cpp
│   │       ├── remove_layers_fix.cpp
│   │       └── remove_annotations_fix.cpp
│   ├── render/                       # Preview renderer
│   │   ├── preview_renderer.hpp / .cpp   # MuPDF wrapping
│   │   └── overlay_painter.cpp           # Desenha retângulos de finding no bitmap
│   ├── report/                       # Geração de relatórios JSON
│   │   ├── report_engine.hpp / .cpp
│   │   ├── internal_report_builder.cpp
│   │   └── client_report_builder.cpp
│   ├── storage/                      # Abstração de storage
│   │   ├── istorage.hpp
│   │   ├── local_file_storage.cpp    # MVP: filesystem local
│   │   └── s3_storage.cpp            # Fase 2: S3/MinIO (stub no MVP)
│   ├── persistence/                  # Acesso ao PostgreSQL
│   │   ├── job_repository.cpp        # CRUD de jobs
│   │   ├── finding_repository.cpp    # CRUD de findings
│   │   ├── fix_repository.cpp        # CRUD de fixes_applied
│   │   ├── artifact_repository.cpp   # CRUD de artifacts
│   │   └── db_pool.cpp               # Connection pool simples
│   ├── orchestration/                # Pipeline orchestrator
│   │   ├── pipeline_orchestrator.hpp / .cpp
│   │   ├── concurrency_guard.hpp / .cpp
│   │   └── job_descriptor.hpp
│   ├── queue/                        # Fila PostgreSQL
│   │   ├── postgres_queue.hpp / .cpp
│   │   └── queue_poller.hpp / .cpp
│   ├── cli/                          # Ferramenta de linha de comando (dev/ops)
│   │   └── main_cli.cpp              # printguard-cli: processar PDF local sem API
│   └── worker/                       # Entrypoint do processo worker
│       └── main_worker.cpp           # Loop principal do worker
├── api/                              # Processo da API REST
│   ├── main_api.cpp                  # Entrypoint do servidor HTTP
│   ├── middleware/
│   │   ├── auth_middleware.cpp       # Validação de API key
│   │   └── rate_limit_middleware.cpp # Rate limiting por tenant (futuro)
│   └── controllers/
│       ├── job_controller.cpp        # POST /jobs, GET /jobs/:id, GET /jobs/:id/status
│       └── artifact_controller.cpp  # GET /jobs/:id/artifacts/:kind
├── include/                          # Headers públicos para uso entre sub-projetos
├── tests/
│   ├── unit/
│   │   ├── rules/                    # Testes de cada regra isolada
│   │   ├── fixes/                    # Testes de cada fix isolado
│   │   ├── planner/                  # Testes do FixPlanner
│   │   └── report/                   # Testes dos report builders
│   ├── integration/
│   │   ├── pipeline/                 # Testes de pipeline completo com PDFs reais
│   │   └── api/                      # Testes de API HTTP
│   └── golden/
│       ├── pdfs/                     # PDFs de teste com problemas conhecidos
│       └── expected/                 # JSONs de referência de relatórios esperados
├── benchmarks/
│   ├── parse_bench.cpp               # Benchmark de parsing por tamanho de PDF
│   ├── analysis_bench.cpp            # Benchmark de análise
│   └── convert_bench.cpp             # Benchmark de conversão de cor
└── scripts/
    ├── setup_postgres.sh             # Cria banco, schema, roles
    ├── deploy.sh                     # Deploy na VPS
    ├── run_worker.sh                 # Start do worker com variáveis de ambiente
    ├── run_api.sh                    # Start da API
    ├── cleanup_old_jobs.sh           # Limpeza de jobs antigos (usado via cron)
    └── healthcheck.sh                # Script de healthcheck externo
```

---

## 21. Modelo de Domínio

### Entidades Centrais

```
┌────────────────┐         ┌──────────────────┐       ┌──────────────────┐
│    Tenant      │◄────────│       Job        │──────►│  ProductPreset   │
│ (gráfica/user) │  1:N    │ (job de preflight│  M:1  │ (cartão visita,  │
│                │         │  de um PDF)      │       │  flyer, etc.)    │
└────────────────┘         └──────────────────┘       └──────────────────┘
                                   │  1:N                       
                                   │                            
                    ┌──────────────┼──────────────────┐
                    │              │                  │
              ┌─────▼──────┐ ┌────▼──────┐ ┌────────▼───────┐
              │  Finding   │ │FixApplied │ │   Artifact     │
              │ (problema  │ │ (correção │ │ (PDF original, │
              │  detectado)│ │  aplicada)│ │  corrigido,    │
              └────────────┘ └───────────┘ │  preview,      │
                                           │  relatório)    │
                                           └────────────────┘

                    ┌──────────────────────┐
                    │  ValidationProfile   │
                    │ (lenient, standard,  │
                    │  bw_fast_print)      │
                    └──────────────────────┘
```

### Regras de Negócio do Domínio

1. **Um Job sempre tem um PDF original preservado.** O arquivo recebido nunca é sobrescrito.
2. **Um Job pode ter zero ou um PDF corrigido.** Se não houver nenhuma correção aplicada, o PDF corrigido pode ser o mesmo que o original (ou ausente).
3. **Findings são imutáveis após criação.** A análise pós-fix cria novos findings marcados com `phase = "postfix"`.
4. **Um Fix só é aplicado se `CanApply()` retornar true.** Fix que não pode ser aplicado é registrado como skipped em `fixes_applied` com `success = false`.
5. **O status do Job é monotônico.** Um job não volta de `completed` para `fixing`. A única exceção é `manual_review_required` que pode ser aprovado para continuar.
6. **Tenant é sempre obrigatório.** Não há acesso a artefatos sem tenant_id.

---

## 22. Modelo de Dados

### Schema PostgreSQL

```sql
-- Tenants (gráficas/clientes do SaaS)
CREATE TABLE tenants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    plan            TEXT NOT NULL DEFAULT 'starter',  -- 'starter', 'professional', 'enterprise'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

-- API Keys por tenant
CREATE TABLE api_keys (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key_hash        TEXT NOT NULL UNIQUE,  -- SHA-256 da API key — nunca store a key em claro
    name            TEXT,                 -- ex: "Chave de produção"
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at    TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);

-- Jobs de preflight
CREATE TABLE jobs (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL REFERENCES tenants(id),
    product_preset_id       TEXT NOT NULL,        -- ex: "business_card" (chave do JSON de preset)
    validation_profile_id   TEXT NOT NULL,        -- ex: "digital_print_standard"
    status                  TEXT NOT NULL DEFAULT 'uploaded',
    -- Enum lógico: uploaded | queued | parsing | analyzing | planning_fixes |
    --              fixing | revalidating | rendering_preview | generating_reports |
    --              completed | failed | manual_review_required | rejected_by_limits
    original_blob_key       TEXT,                 -- path no storage
    corrected_blob_key      TEXT,
    original_filename       TEXT,                 -- nome original do arquivo
    original_size_bytes     BIGINT,
    page_count              INT,
    error_code              TEXT,                 -- código de erro se status = failed
    error_detail            TEXT,                 -- detalhe técnico do erro
    worker_id               INT,                  -- ID do worker que pegou o job
    picked_at               TIMESTAMPTZ,          -- quando o worker pegou o job
    completed_at            TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_jobs_tenant_id ON jobs(tenant_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at);
-- Index composto para o polling do worker:
CREATE INDEX idx_jobs_queue_poll ON jobs(status, created_at) WHERE status IN ('uploaded', 'queued');

-- Findings (resultados da análise)
CREATE TABLE findings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    phase           TEXT NOT NULL CHECK (phase IN ('initial', 'postfix')),
    code            TEXT NOT NULL,         -- ex: "CLR001"
    category        TEXT NOT NULL,         -- "color", "geometry", "resolution", etc.
    severity        TEXT NOT NULL,         -- "Info", "Warning", "ErrorFixable", "ErrorBlocking"
    fixability      TEXT NOT NULL,
    page_index      INT,                   -- NULL = global
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    user_message    TEXT,                  -- mensagem para relatório de cliente
    evidence_json   JSONB,                 -- array de strings com evidências
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_findings_job_id ON findings(job_id);
CREATE INDEX idx_findings_job_phase ON findings(job_id, phase);

-- Fixes aplicados
CREATE TABLE fixes_applied (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    fix_id          TEXT NOT NULL,         -- ex: "ConvertRgbToCmykFix"
    finding_code    TEXT NOT NULL,         -- código do finding que motivou o fix
    risky           BOOLEAN NOT NULL DEFAULT FALSE,
    success         BOOLEAN NOT NULL,
    details_json    JSONB,                 -- resultado detalhado do fix
    duration_ms     INT,                   -- tempo de execução em ms
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_fixes_job_id ON fixes_applied(job_id);

-- Artefatos gerados
CREATE TABLE artifacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    kind            TEXT NOT NULL,
    -- 'original_pdf', 'corrected_pdf', 'preview_jpg', 'overlay_png',
    -- 'report_internal', 'report_client'
    blob_key        TEXT NOT NULL,         -- path no storage
    checksum_sha256 TEXT,                  -- SHA-256 do arquivo
    size_bytes      BIGINT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_artifacts_job_id ON artifacts(job_id);

-- Métricas de pipeline por job (para observabilidade)
CREATE TABLE job_timings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    stage           TEXT NOT NULL,         -- "parse", "analyze", "fix", "revalidate", "preview", "report"
    started_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,
    duration_ms     INT GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (ended_at - started_at)) * 1000
    ) STORED
);
```

### Diagrama de Relacionamentos Simplificado

```
tenants ──< api_keys
tenants ──< jobs ──< findings
                ──< fixes_applied
                ──< artifacts
                ──< job_timings
```

---

## 23. Pipeline de Execução do Job

### Estados do Job e Transições

```
                         ┌──────────────────────────────┐
                         │         rejected_by_limits   │◄──── Upload com arquivo > limite
                         └──────────────────────────────┘

uploaded ──► queued ──► parsing ──► analyzing ──► planning_fixes
                                                       │
                                          ┌────────────┤
                                          │            │
                                          ▼            ▼
                                       fixing     manual_review_required
                                          │
                                          ▼
                                    revalidating
                                          │
                                          ▼
                                  rendering_preview
                                          │
                                          ▼
                                  generating_reports
                                          │
                               ┌──────────┴──────────┐
                               ▼                     ▼
                           completed              failed
```

### Definição de Cada Estado

| Estado | Quem define | O que acontece | Pode regredir? |
|---|---|---|---|
| `uploaded` | API | PDF recebido e salvo no storage, job criado no banco | Não |
| `queued` | Worker (ao não ter slot disponível) | Job aguarda slot de processamento | Não |
| `parsing` | Worker | QPDF carrega e valida estrutura do PDF | Não |
| `analyzing` | Worker | RuleEngine executa todas as regras | Não |
| `planning_fixes` | Worker | FixPlanner monta o FixPlan | Não |
| `fixing` | Worker | FixEngine executa ações do plano | Não |
| `revalidating` | Worker | RuleEngine executa novamente no PDF corrigido | Não |
| `rendering_preview` | Worker | MuPDF rasteriza primeira página | Não |
| `generating_reports` | Worker | ReportEngine produz relatórios JSON | Não |
| `completed` | Worker | Todos os artefatos disponíveis | Não |
| `failed` | Worker | Erro não recuperável em alguma etapa | Não |
| `manual_review_required` | Worker ou operador | Há findings bloqueantes sem fix automático disponível | Pode avançar via ação manual |
| `rejected_by_limits` | API (no momento do upload) | Arquivo excede limites de tamanho ou páginas | Não |

### Tratamento de Erros e Retries

**Política de retry:**
- Erros de rede/banco: retry automático até 3 vezes com backoff exponencial (1s, 2s, 4s)
- Erros de parsing (PDF malformado): sem retry — marcar como `failed` imediatamente
- Erros de correção (fix falhou): continuar com os outros fixes, registrar falha do fix específico
- Timeout de etapa: sem retry — marcar etapa como falha, avançar para próxima ou mover para `failed` / `manual_review_required`
- Crash do worker (OOM, SIGKILL): jobs em `parsing`, `analyzing`, `fixing` etc. voltam para `queued` via job de reconciliação

**Job de reconciliação (cleanup daemon):**

```sql
-- Jobs presos em estados transitórios por mais de 30 minutos = worker morreu
UPDATE jobs
SET status = 'queued', picked_at = NULL, worker_id = NULL, updated_at = NOW()
WHERE status IN ('parsing', 'analyzing', 'planning_fixes', 'fixing', 'revalidating', 'rendering_preview', 'generating_reports')
  AND picked_at < NOW() - INTERVAL '30 minutes';
```

Esse cleanup roda como um cron job a cada 5 minutos (ou via thread dedicada no worker).

---

## 24. Engine de Análise

### Princípios do Rule Engine

1. **Isolamento**: cada regra é uma unidade testável independente. `Evaluate()` é `const` e puro.
2. **Sem efeito colateral**: regras não modificam o documento nem o banco.
3. **Evidências específicas**: cada finding deve ter evidências que permitam ao operador entender exatamente onde está o problema (página, objeto, dimensão, valor encontrado vs. esperado).
4. **Categorização clara**: cada regra pertence a uma categoria (geometry, color, resolution, font, transparency, structure).
5. **Configurável por preset**: regras recebem o preset como contexto e ajustam seus critérios (ex: mínimo de DPI varia por produto).

### Estrutura do RuleContext

```cpp
struct ValidationProfile {
    std::string id;
    std::string name;
    bool requireCmyk;               // false no lenient
    bool treatRgbAsBlocking;        // false no lenient, true no standard
    bool allowSpotColors;
    bool allowTransparency;
    bool allowAnnotations;
    bool allowLayers;
    int minDpiOverride;             // 0 = usa o do preset
    bool autoFixEnabled;            // false = apenas detecta, não corrige
    bool allowRiskyFixes;           // false no MVP por default, true em modo permissivo
    std::vector<std::string> disabledRules;   // regras desabilitadas neste perfil
    std::vector<std::string> disabledFixes;   // fixes desabilitados neste perfil
};
```

### Fluxo Interno do RuleEngine

```cpp
std::vector<Finding> RuleEngine::RunAll(const RuleContext& ctx) const {
    std::vector<Finding> allFindings;
    
    for (const auto& rule : rules_) {
        // Pula regras desabilitadas pelo validation profile
        if (ctx.profile.IsRuleDisabled(rule->Id())) continue;
        
        auto findings = rule->Evaluate(ctx);
        
        // Aplica ajustes de severidade por perfil
        for (auto& f : findings) {
            f.severity = ctx.profile.AdjustSeverity(f.code, f.severity);
        }
        
        allFindings.insert(allFindings.end(), 
                           findings.begin(), findings.end());
    }
    
    return allFindings;
}
```

---

## 25. Catálogo Inicial de Regras

### Tabela de Regras do MVP

| Código | Nome da Regra | Categoria | Severidade Padrão | Auto-fix Disponível? | Custo Computacional | Observações |
|---|---|---|---|---|---|---|
| GEO001 | PageSizeRule | geometry | ErrorFixable | Sim (NormalizeBoxesFix) | Baixo | Compara TrimBox com dimensões do preset |
| GEO002 | BleedRule | geometry | Warning | Sim (NormalizeBoxesFix parcial) | Baixo | BleedBox ausente ou insuficiente. Warning no lenient, ErrorFixable no standard |
| GEO003 | BoxConsistencyRule | geometry | ErrorFixable | Sim (NormalizeBoxesFix) | Baixo | MediaBox menor que TrimBox, boxes inconsistentes |
| GEO004 | RotationRule | geometry | ErrorFixable | Sim (RotatePageFix) | Baixo | Página rotacionada incorretamente para o produto |
| GEO005 | PageCountRule | geometry | ErrorBlocking | Não | Nulo | Número de páginas fora do esperado pelo preset (ex: cartão precisa de 2 faces) |
| CLR001 | ColorSpaceRule | color | ErrorFixable | Sim (ConvertRgbToCmykFix) | Médio | Detecta objetos em RGB no documento. ErrorFixable no standard, Warning no lenient |
| CLR002 | OutputIntentRule | color | Warning | Sim (AttachOutputIntentFix) | Baixo | Ausência de Output Intent ICC |
| CLR003 | SpotColorRule | color | Warning | Sim (ConvertSpotToCmykFix) | Baixo | Cores spot quando preset não suporta |
| CLR004 | WhiteOverprintRule | color | ErrorFixable | Sim (RemoveWhiteOverprintFix) | Baixo | Objetos brancos com overprint habilitado |
| CLR005 | OverprintRule | color | Warning | Não no MVP | Médio | Overprint em outros objetos — sinaliza, não corrige no MVP |
| RES001 | ImageResolutionRule | resolution | Warning ou ErrorFixable | Não | Médio | Imagens abaixo do DPI mínimo. ErrorFixable apenas em perfis rígidos |
| RES002 | ImageColorSpaceRule | resolution | ErrorFixable | Sim (ConvertRgbToCmykFix) | Médio | Imagens em RGB (complementar ao CLR001) |
| STR001 | LayersRule | structure | Warning | Sim (RemoveLayersFix) | Baixo | Camadas opcionais presentes |
| STR002 | AnnotationsRule | structure | Warning | Sim (RemoveAnnotationsFix) | Baixo | Anotações, comentários PDF presentes |
| STR003 | EncryptionRule | structure | ErrorBlocking | Não | Baixo | PDF com criptografia — não pode ser processado |
| STR004 | TransparencyRule | structure | Warning | Não no MVP | Médio | Transparências complexas detectadas. Apenas informativo no MVP |
| STR005 | FontEmbeddingRule | structure | Warning | Não no MVP | Médio | Fontes não embarcadas. Fix (EmbedFontsFix) entra na fase 2 |

### Implementação de Exemplo — ColorSpaceRule

```cpp
// analysis/rules/color_rules.cpp

class ColorSpaceRule : public IRule {
public:
    std::string Id() const override { return "CLR001"; }
    std::string Category() const override { return "color"; }
    
    std::vector<Finding> Evaluate(const RuleContext& ctx) const override {
        std::vector<Finding> findings;
        
        for (const auto& page : ctx.document.pages) {
            // Verifica espaços de cor dos recursos da página
            for (const auto& cs : page.colorSpaces) {
                if (IsRgbColorSpace(cs.type)) {
                    Finding f;
                    f.code = "CLR001";
                    f.title = "Espaço de cor RGB detectado";
                    f.description = "A página " + std::to_string(page.index + 1) + 
                                    " contém objetos no espaço de cor " + cs.type +
                                    ". Para impressão CMYK, a conversão é necessária.";
                    f.severity = ctx.profile.requireCmyk && ctx.profile.treatRgbAsBlocking
                                 ? Severity::ErrorFixable : Severity::Warning;
                    f.fixability = Fixability::AutomaticSafe;
                    f.category = "color";
                    f.pageIndex = page.index;
                    f.evidence = {
                        "Espaço de cor detectado: " + cs.type,
                        "Página: " + std::to_string(page.index + 1),
                        "Preset requer CMYK: " + std::string(ctx.preset.requireCmyk ? "sim" : "não")
                    };
                    f.userMessage = "Seu arquivo usa cores RGB. Vamos converter automaticamente "
                                    "para o padrão de impressão CMYK. As cores podem ter pequenas "
                                    "variações após a conversão.";
                    findings.push_back(std::move(f));
                    break; // Um finding por página, não por objeto
                }
            }
            
            // Verifica imagens especificamente
            for (const auto& img : page.images) {
                if (IsRgbColorSpace(img.colorSpace)) {
                    // ... similar, mas com evidência específica da imagem
                }
            }
        }
        
        return findings;
    }
    
private:
    static bool IsRgbColorSpace(const std::string& cs) {
        return cs == "DeviceRGB" || cs == "sRGB" || cs == "AdobeRGB";
    }
};
```

---

## 26. Engine de Correção

### Princípios do Fix Engine

1. **Atomicidade por fix**: cada FixAction é aplicado de forma isolada. Se falhar, o próximo fix da fila pode ainda ser tentado.
2. **Preservação do original**: o Fix Engine trabalha sempre sobre uma **cópia de trabalho** do PDF, nunca sobre o original.
3. **Auditoria total**: cada tentativa de fix (sucesso ou falha) é registrada em `fixes_applied` com detalhes suficientes para reprodução.
4. **Reentrada segura**: se o pipeline for reiniciado (ex: após crash), o sistema verifica quais fixes já foram aplicados e não os duplica.
5. **Validação pré e pós**: `CanApply()` valida precondições antes do fix. Após aplicação, o DocumentModel em memória é atualizado.

### FixContext e Gerenciamento de Estado

```cpp
struct FixContext {
    QPDF& pdf;                              // Handle QPDF (cópia de trabalho)
    DocumentModel& document;               // Modelo mutável — atualizado por cada fix
    const ProductPreset& preset;
    const ValidationProfile& profile;
    ColorEngine& colorEngine;
    std::vector<FixAppliedRecord>& auditLog;
    
    // Contadores de uso de recursos (para evitar explosão de memória)
    size_t estimatedRamUsedBytes {0};
    
    // Flag: se true, fix de cor já foi aplicado — evita dupla conversão
    bool colorConversionApplied {false};
};
```

### FixPlanner — Lógica de Planejamento

O planner executa o seguinte algoritmo:

```
1. Para cada Finding em findings:
   a. Busca IFixAction com Id correspondente
   b. Se não existe: mark finding as unresolvable
   c. Se existe e risky=true e profile.allowRiskyFixes=false: mark as skipped
   d. Se CanApply() retorna false: mark as not_applicable
   e. Caso contrário: adiciona à lista de ações

2. Ordena lista de ações por topological sort (dependências) + prioridade

3. Identifica se ainda há ErrorBlocking sem resolução
   → hasBlockingUnresolved = true se houver

4. Retorna FixPlan completo
```

### Como Evitar Corromper o PDF

Esta é a preocupação mais crítica do sistema. As seguintes salvaguardas são obrigatórias:

1. **Sempre trabalhar em cópia**: o PDF original é copiado para um arquivo temporário antes de qualquer modificação. O original nunca é tocado.

2. **Write-on-complete via QPDF**: QPDF tem um modelo de escrita seguro — as modificações são feitas em memória e escritas em um novo arquivo de saída. O arquivo de entrada não é modificado in-place.

3. **Validação estrutural pós-escrita**: após cada write do QPDF, o sistema re-abre o arquivo resultante e valida que:
   - O arquivo é um PDF válido (QPDF não reporta erros de parsing)
   - O número de páginas é o mesmo
   - Os checksums de objetos não críticos batem

4. **Rollback por cópia**: se a validação falhar, o arquivo de trabalho é descartado e o job é marcado como `failed` com razão `pdf_corruption_detected_after_fix`.

5. **Fixes sequenciais, não paralelos**: nunca aplica dois fixes no mesmo PDF simultaneamente. A sequência garante que cada fix parte de um estado consistente.

```cpp
// fix/fix_engine.cpp

FixEngineResult FixEngine::Execute(const FixPlan& plan, FixContext& ctx) {
    FixEngineResult result;
    
    // Faz cópia de trabalho do PDF
    std::string workingCopy = CreateWorkingCopy(originalPdfPath_);
    QPDF workPdf;
    workPdf.processFile(workingCopy.c_str());
    ctx.pdf = workPdf;
    
    for (const auto& action : plan.actions) {
        auto* fix = GetFix(action.id);
        if (!fix) continue;
        
        // Valida precondições
        for (const auto& finding : FindingsForAction(action, allFindings_)) {
            if (!fix->CanApply(ctx, finding)) {
                RecordSkipped(ctx, action, finding, "CanApply returned false");
                continue;
            }
            
            auto startTime = std::chrono::steady_clock::now();
            try {
                fix->Apply(ctx, finding);
                
                // Valida integridade após cada fix
                if (!ValidateIntegrity(workPdf, ctx.document)) {
                    throw std::runtime_error("PDF integrity check failed after fix " + action.id);
                }
                
                RecordSuccess(ctx, action, finding, startTime);
            } catch (const std::exception& e) {
                RecordFailure(ctx, action, finding, e.what());
                // Continua para o próximo fix — não aborta tudo
            }
        }
    }
    
    // Escreve PDF final corrigido
    WriteOutputPdf(workPdf, correctedPdfPath_);
    
    return result;
}
```

---

## 27. Catálogo Inicial de Fixes

### Tabela de Fixes

| Fix | Objetivo | Nível de Risco | Depende de | Entra no MVP? | Precisa Revalidar | Custo Operacional |
|---|---|---|---|---|---|---|
| NormalizeBoxesFix | Ajusta MediaBox, TrimBox, BleedBox para consistência com o preset | Baixo | Nenhum | Sim | GEO001, GEO002, GEO003 | Baixo — apenas edição de dicionário PDF |
| RotatePageFix | Corrige a flag `/Rotate` das páginas | Baixo | NormalizeBoxesFix | Sim | GEO004 | Baixo |
| AttachOutputIntentFix | Adiciona objeto OutputIntent com perfil ICC ao PDF | Baixo | Nenhum | Sim | CLR002 | Baixo — apenas adiciona stream ICC |
| ConvertRgbToCmykFix | Converte espaços de cor RGB de objetos vetoriais e imagens para CMYK via LittleCMS2 | Médio | AttachOutputIntentFix | Sim | CLR001, RES002 | Alto — rasteriza e re-codifica imagens |
| ConvertSpotToCmykFix | Converte cores Separation (spot) para CMYK equivalente do alternateSpace | Baixo-Médio | AttachOutputIntentFix | Sim | CLR003 | Médio |
| RemoveWhiteOverprintFix | Remove atributo overprint de objetos com cor branca | Baixo | Nenhum | Sim | CLR004 | Baixo |
| RemoveLayersFix | Flatten de OCG (Optional Content Groups) — merge de layers no conteúdo da página | Baixo | Nenhum | Sim | STR001 | Baixo-Médio |
| RemoveAnnotationsFix | Remove objetos de anotação do dicionário de cada página | Baixo | Nenhum | Sim | STR002 | Baixo |
| EmbedFontsFix | Tenta embutir fontes referenciadas mas não embarcadas usando fonte do sistema | Alto | Nenhum | Fase 2 | STR005 | Alto — requer acesso a fontes do sistema |
| OutlineFontsFix | Converte texto em outlines vetoriais — fallback quando embed não é possível | Alto | Nenhum | Fase 2 | STR005 | Alto — rasteriza texto |
| FlattenTransparencyFix | Rasteriza objetos com transparência complexa para evitar artefatos em RIPs antigos | Alto | ConvertRgbToCmykFix | Fase 2 | STR004 | Muito alto — rasterização por região |
| TacReductionFix | Reduz cobertura total de tinta em áreas que excedem o limite do preset | Muito Alto | ConvertRgbToCmykFix | Fase 2 | N/A (nova regra) | Muito alto — recalcula cor por pixel |
| NormalizeBlackFix | Converte preto rico (C+M+Y+K) para preto puro (K100) em textos | Alto | ConvertRgbToCmykFix | Fase 2 | N/A (nova regra) | Médio |
| SafeBleedExpansionFix | Expande sangria por espelhamento das bordas — apenas quando a margem de conteúdo permite | Muito Alto | NormalizeBoxesFix | Fase 2 | GEO002 | Alto — opera sobre pixels |
| RecenterArtworkFix | Reposiciona artwork para o centro do TrimBox quando deslocamento é detectado | Muito Alto | NormalizeBoxesFix | Fase 3 | GEO001 | Alto — modifica coordenadas de objetos |

### Implementação de Exemplo — ConvertRgbToCmykFix

```cpp
// fix/fixes/convert_rgb_to_cmyk_fix.cpp

class ConvertRgbToCmykFix : public IFixAction {
public:
    std::string Id() const override { return "ConvertRgbToCmykFix"; }
    
    bool CanApply(const FixContext& ctx, const Finding& finding) const override {
        // Não aplica se já foi aplicado neste job
        if (ctx.colorConversionApplied) return false;
        // Não aplica se o PDF está criptografado
        if (ctx.pdf.isEncrypted()) return false;
        // Verifica que o perfil de cor está disponível
        return ctx.colorEngine.HasProfile("sRGB") && 
               ctx.colorEngine.HasProfile("GRACoL2013");
    }
    
    void Apply(FixContext& ctx, const Finding& finding) const override {
        // Para cada página do documento
        for (auto& page : ctx.document.pages) {
            // Processa imagens RGB da página
            for (auto& img : page.images) {
                if (IsRgbColorSpace(img.colorSpace)) {
                    ConvertImageInPlace(ctx, img);
                }
            }
            // Processa espaços de cor de conteúdo vetorial
            ConvertPageColorSpaces(ctx, page);
        }
        
        // Marca que a conversão foi aplicada
        ctx.colorConversionApplied = true;
    }
    
private:
    void ConvertImageInPlace(FixContext& ctx, ImageResource& img) const {
        // 1. Extrai pixels da imagem via QPDF
        // 2. Cria transformação lcms2: sRGB → GRACoL2013 (CMYK) com Perceptual intent
        // 3. Aplica transformação pixel por pixel (ou em chunks para memória)
        // 4. Re-codifica como JPEG CMYK ou TIFF CMYK
        // 5. Substitui stream de imagem no QPDF
        // 6. Atualiza ColorSpace dict no dicionário do XObject para /DeviceCMYK
    }
};
```

---

## 28. Matriz Finding → Correção

| Finding Code | Finding Nome | Fix Aplicado | Revalida | Severidade Pós-fix Esperada |
|---|---|---|---|---|
| GEO001 | PageSizeRule | NormalizeBoxesFix | GEO001, GEO002, GEO003 | Info (resolvido) |
| GEO002 | BleedRule | NormalizeBoxesFix (parcial) | GEO002 | Warning se não há bleed no conteúdo |
| GEO003 | BoxConsistencyRule | NormalizeBoxesFix | GEO003 | Info |
| GEO004 | RotationRule | RotatePageFix | GEO004 | Info |
| GEO005 | PageCountRule | ❌ Sem fix automático | — | ErrorBlocking (permanece) |
| CLR001 | ColorSpaceRule | ConvertRgbToCmykFix | CLR001 | Info |
| CLR002 | OutputIntentRule | AttachOutputIntentFix | CLR002 | Info |
| CLR003 | SpotColorRule | ConvertSpotToCmykFix | CLR003 | Info |
| CLR004 | WhiteOverprintRule | RemoveWhiteOverprintFix | CLR004 | Info |
| CLR005 | OverprintRule | ❌ Sem fix no MVP | — | Warning (permanece) |
| RES001 | ImageResolutionRule | ❌ Sem fix automático | — | Warning (permanece) |
| RES002 | ImageColorSpaceRule | ConvertRgbToCmykFix | RES002 | Info |
| STR001 | LayersRule | RemoveLayersFix | STR001 | Info |
| STR002 | AnnotationsRule | RemoveAnnotationsFix | STR002 | Info |
| STR003 | EncryptionRule | ❌ Sem fix — ErrorBlocking | — | ErrorBlocking (permanece) |
| STR004 | TransparencyRule | ❌ Sem fix no MVP | — | Warning (permanece) |
| STR005 | FontEmbeddingRule | ❌ Sem fix no MVP | — | Warning (permanece) |

---

## 29. Política de Segurança das Correções

### Princípio Geral

> **A integridade do arquivo do cliente vale mais do que a completude da correção.**

O sistema deve errar pelo lado da conservação: é melhor entregar um PDF com um warning não resolvido do que um PDF com conteúdo corrompido após uma tentativa de correção.

### Critérios para Classificar um Fix como "Seguro"

Um fix é classificado como `AutomaticSafe` (e pode rodar sem aprovação do operador) se:

1. **Reversível conceitualmente**: a informação original pode ser reconstruída a partir do resultado (ex: ajuste de boxes — os valores originais ficam no relatório).
2. **Sem perda de conteúdo de aparência**: o conteúdo visual da página não deve mudar significativamente para um observador humano.
3. **Determinístico**: dado o mesmo input, produz sempre o mesmo output.
4. **Sem ambiguidade de intenção**: a correção tem um único resultado correto óbvio.
5. **Testável por revalidação**: o problema que motivou o fix deve ser resolvido e verificável na revalidação.

### Critérios para Classificar um Fix como "Arriscado"

Um fix é `AutomaticRisky` (requer `profile.allowRiskyFixes = true` ou aprovação de operador) se:

1. **Mudança visual potencialmente perceptível**: conversão de cor, flatten de transparência.
2. **Depende de heurística ou interpolação**: expansão de sangria por espelhamento.
3. **Pode introduzir artefatos**: flatten de transparência sobre gradientes complexos.
4. **Irreversível sem o original**: recodificação de imagens com perda (JPEG).
5. **Dependente de fontes externas**: embedding de fontes (a fonte no sistema pode ser uma versão diferente).

---

## 30. Fixes Seguros vs. Fixes Arriscados

### Fixes Seguros — Executam Automaticamente sem Aprovação

| Fix | Por que é seguro |
|---|---|
| NormalizeBoxesFix | Opera apenas em dicionários de geometria. Conteúdo visual não é tocado. |
| RotatePageFix | Muda apenas a flag `/Rotate`. Conteúdo não é modificado. |
| AttachOutputIntentFix | Apenas adiciona um stream ICC. Não modifica nenhum conteúdo existente. |
| RemoveWhiteOverprintFix | Remove um atributo de rendering. O objeto branco continua branco — apenas garante que aparece. |
| RemoveLayersFix | Merge de layers visíveis no stream de conteúdo. Layers ocultas são descartadas, o que é a intenção. |
| RemoveAnnotationsFix | Remove objetos que não fazem parte do conteúdo imprimível por definição. |

### Fixes de Risco Médio — Executam com Perfil Permissivo

| Fix | Por que tem risco | Mitigação |
|---|---|---|
| ConvertRgbToCmykFix | Cores podem ter variação perceptível após conversão. Gamut mismatch pode resultar em cores diferentes. | Usar rendering intent Perceptual. Reportar gamut warnings no relatório. Mostrar no preview para cliente comparar. |
| ConvertSpotToCmykFix | O equivalente CMYK de uma cor spot pode não ser visualmente fiel ao Pantone especificado. | Usar tabela de conversão Pantone→CMYK conhecida. Informar o cliente claramente. |

### Fixes de Alto Risco — Requerem Aprovação de Operador (Fase 2)

| Fix | Por que tem alto risco |
|---|---|
| EmbedFontsFix | A versão da fonte no servidor pode ser diferente da usada no arquivo original. |
| OutlineFontsFix | Texto se torna vetor — sem possibilidade de edição posterior. Qualidade dependente da resolução de rendering. |
| FlattenTransparencyFix | Pode criar artefatos visíveis em bordas de objetos transparentes. Resultado depende do nível de complexidade da transparência. |
| TacReductionFix | Altera valores de cor de forma irreversível. Impacto visual potencialmente significativo em fundos escuros. |
| SafeBleedExpansionFix | Espelhamento de borda pode criar visual indesejado se o conteúdo próximo à borda não for "espelhável". |

---

## 31. Revalidação Pós-Correção

### Por que Revalidar é Obrigatório

Fixes podem:
1. Resolver o problema que motivaram
2. Introduzir um novo problema não previsto
3. Resolver apenas parcialmente o problema (ex: BleedBox corrigida, mas ainda insuficiente)

A revalidação executa o **mesmo conjunto de regras** sobre o PDF corrigido, marcando os findings com `phase = "postfix"`.

### O que a Revalidação Verifica

```
Revalidação executa o RuleEngine completo no PDF corrigido.
Resultado é persistido com phase = "postfix".

Pós-processamento dos resultados:
1. Compara findings "initial" vs "postfix"
2. Findings resolvidos: estavam em "initial", não estão em "postfix" com a mesma severidade
3. Findings não resolvidos: presentes em ambos
4. Novos findings: presentes apenas em "postfix" (potencialmente introduzidos por fixes)

Se houver novo finding de severidade ErrorBlocking em "postfix":
→ job vai para manual_review_required com motivo "fix_introduced_new_blocking_error"
```

### Relatório de Revalidação no JSON Interno

```json
{
  "revalidation": {
    "resolved_findings": ["CLR001", "STR001", "STR002"],
    "unresolved_findings": ["GEO002", "STR005"],
    "new_findings_introduced": [],
    "overall_result": "improved",
    "blocking_errors_remaining": 0
  }
}
```

---

## 32. Sistema de Presets

### O que é um Preset

Um preset representa um produto gráfico específico com suas características de impressão. É a configuração que o cliente (gráfica) seleciona ao criar um job, correspondendo ao produto que o cliente final encomendou.

### Formato JSON de um Preset

```json
// config/presets/business_card.json
{
  "id": "business_card",
  "name": "Cartão de Visita",
  "description": "Cartão de visita padrão frente e verso, acabamento UV ou fosco",
  "finalWidthMm": 90.0,
  "finalHeightMm": 50.0,
  "bleedMm": 3.0,
  "safeMarginMm": 5.0,
  "expectedPagesMin": 1,
  "expectedPagesMax": 2,
  "requireCmyk": true,
  "allowSpotColors": false,
  "allowTransparency": true,
  "autoFixBleed": false,
  "autoConvertRgb": true,
  "minDpi": 150,
  "recommendedDpi": 300,
  "maxTacPercent": 300,
  "notes": "Para UV spot ou laminação, verificar se as áreas de aplicação estão em layer separado"
}
```

```json
// config/presets/poster_a3.json
{
  "id": "poster_a3",
  "name": "Poster A3",
  "description": "Poster A3 para impressão em papel couché ou fotográfico",
  "finalWidthMm": 297.0,
  "finalHeightMm": 420.0,
  "bleedMm": 5.0,
  "safeMarginMm": 10.0,
  "expectedPagesMin": 1,
  "expectedPagesMax": 1,
  "requireCmyk": false,
  "allowSpotColors": false,
  "allowTransparency": true,
  "autoFixBleed": false,
  "autoConvertRgb": true,
  "minDpi": 100,
  "recommendedDpi": 150,
  "maxTacPercent": 320,
  "notes": "Posters visualizados à distância — DPI mínimo menor que para materiais de mão"
}
```

### Como Adicionar Novos Presets

Presets são carregados na inicialização do sistema a partir do diretório `config/presets/`. Não há necessidade de recompilação. Para adicionar um novo preset:
1. Criar o arquivo JSON seguindo o schema acima
2. Reiniciar o worker (systemd restart)
3. O preset fica disponível imediatamente para novos jobs

**Validação de presets**: ao carregar, o sistema valida o schema JSON e rejeita presets mal formados, logando o erro e continuando com os demais.

---

## 33. Sistema de Validation Profiles

### O que é um Validation Profile

Um validation profile define o **rigor** da validação aplicada independentemente do preset. Permite que a mesma gráfica use regras diferentes para clientes diferentes (ex: mais leniente para cliente VIP que insiste no arquivo "como está", mais rígido para produção standard).

```json
// config/validation_profiles/digital_print_standard.json
{
  "id": "digital_print_standard",
  "name": "Impressão Digital — Padrão",
  "description": "Perfil padrão para gráficas digitais. CMYK preferido, RGB convertível.",
  "requireCmyk": true,
  "treatRgbAsBlocking": false,
  "allowSpotColors": false,
  "allowTransparency": true,
  "allowAnnotations": false,
  "allowLayers": false,
  "minDpiOverride": 0,
  "autoFixEnabled": true,
  "allowRiskyFixes": false,
  "disabledRules": [],
  "disabledFixes": []
}
```

```json
// config/validation_profiles/digital_print_lenient.json
{
  "id": "digital_print_lenient",
  "name": "Impressão Digital — Permissivo",
  "description": "Para clientes que enviaram RGB e a gráfica aceita. Menos alertas bloqueantes.",
  "requireCmyk": false,
  "treatRgbAsBlocking": false,
  "allowSpotColors": true,
  "allowTransparency": true,
  "allowAnnotations": true,
  "allowLayers": true,
  "minDpiOverride": 100,
  "autoFixEnabled": true,
  "allowRiskyFixes": false,
  "disabledRules": ["CLR003", "STR001", "STR002"],
  "disabledFixes": []
}
```

```json
// config/validation_profiles/bw_fast_print.json
{
  "id": "bw_fast_print",
  "name": "Preto e Branco — Impressão Rápida",
  "description": "Para impressoras P&B de alta velocidade. Exige escala de cinza ou K puro.",
  "requireCmyk": false,
  "requireGrayscale": true,
  "treatRgbAsBlocking": true,
  "allowSpotColors": false,
  "allowTransparency": false,
  "allowAnnotations": false,
  "allowLayers": false,
  "minDpiOverride": 120,
  "autoFixEnabled": true,
  "allowRiskyFixes": false,
  "disabledRules": [],
  "disabledFixes": []
}
```

---

## 34. Estratégia de Color Management

### Decisão: LittleCMS2 como Única Engine de Cor

**Contexto:** Gerenciamento de cor em preflight envolve: identificar perfis ICC no documento, executar transformações de cor entre espaços, e aplicar as transformações aos streams de imagem e definições de cor vetorial.

**Decisão:** Usar exclusivamente LittleCMS2 (lcms2) para todas as operações de cor. Não usar ICC engine do MuPDF ou de outra biblioteca. Centralizar tudo em lcms2.

**Motivo:** LittleCMS2 é a referência de facto para gerenciamento de cor em software livre. É madura, bem testada, usada em GIMP, Inkscape, Ghostscript, e muitos outros softwares de produção. Sua API C é estável e bem documentada.

### Perfis ICC no MVP

**Perfis embarcados no sistema:**
- `sRGB.icc` — perfil fonte para conversão de RGB genérico
- `GRACoL2013.icc` — perfil destino CMYK para impressão digital coated (mais adequado que FOGRA39 para digital)
- `FOGRA39.icc` — alternativa para compatibilidade com workflows offset

**Por que GRACoL2013 e não FOGRA39 para digital:**
FOGRA39 é calibrado para impressão offset em papel coated. GRACoL2013 é calibrado para impressão digital de alta qualidade. Para o foco em gráficas digitais, GRACoL2013 produz conversões mais fiéis. A gráfica pode sobrescrever o perfil padrão por tenant via configuração.

### Pipeline de Conversão RGB → CMYK

```
1. Identificar espaço de cor de origem:
   - Se o PDF tem perfil ICC embarcado (ICCBased): usar esse perfil como origem
   - Se não tem: assumir sRGB como origem (mais seguro que DeviceRGB puro)

2. Determinar perfil de destino:
   - Usar GRACoL2013 como padrão
   - Ou usar o perfil especificado no preset/profile da gráfica

3. Criar transformação lcms2:
   - Para imagens fotográficas: intent Perceptual
   - Para gráficos com cores sólidas: intent Relative Colorimetric com black point compensation

4. Aplicar transformação:
   - Para imagens: pixel por pixel (ou em linhas para gerenciamento de memória)
   - Para cores vetoriais (fills, strokes no PDF): converter os valores discretos de cor

5. Log de gamut warnings:
   - Cores fora do gamut CMYK são registradas como evidência no relatório
   - Usuário é informado que pode haver pequena variação de cor
```

### Conversão de Spot Colors para CMYK

Cores spot (Separation) têm um `alternateSpace` no PDF que é frequentemente um equivalente CMYK ou RGB. O fix `ConvertSpotToCmykFix`:
1. Lê o `alternateSpace` da cor spot
2. Se já é CMYK: usa diretamente
3. Se é RGB: converte via lcms2 para CMYK
4. Substitui a definição da cor spot pelo equivalente CMYK

**Limitação reconhecida:** Cores Pantone convertidas para CMYK podem ter variação significativa. O sistema avisa o cliente explicitamente quando converte Pantone. No relatório, registra: nome da cor spot, valor CMYK equivalente usado, Delta E estimado se disponível.

---

## 35. Estratégia de Renderização e Preview

### Decisão: Preview Apenas da Primeira Página no MVP

**Contexto:** Renderizar todas as páginas de um PDF de 40 páginas em uma VPS com 2 vCPUs seria proibitivo. Mesmo uma página pode levar vários segundos para PDFs complexos.

**Decisão:** No pipeline automático do MVP, renderizar **apenas a primeira página**. Páginas adicionais são geradas sob demanda via endpoint específico (`GET /v1/jobs/{id}/preview/{page}`).

**Motivo:** A primeira página é a mais relevante para que o cliente veja o resultado. Para a maioria dos casos de uso (cartão de visita, flyer, convite), a primeira página representa o arquivo. Para documentos multipágina, o operador pode solicitar páginas específicas sob demanda.

### Especificação do Preview

```
- Formato de saída: JPEG
- Largura máxima: 1200px (proporcional ao tamanho real)
- Qualidade JPEG: 85%
- Espaço de cor do JPEG: sRGB (para exibição em tela)
- Resolução equivalente de rendering: 150 DPI (suficiente para preview de qualidade)
- Timeout: 30 segundos (se exceder, job continua sem preview, preview marcado como unavailable)
```

### Overlay de Problemas

O overlay é gerado como imagem PNG separada com canal alfa:
- Cada finding com `pageIndex = 0` (primeira página) gera uma marcação visual
- Geometria: se o finding tem coordenadas específicas (ex: ImageResolutionRule por imagem), um retângulo semitransparente é desenhado sobre a área
- Findings globais de cor e estrutura são marcados com uma borda colorida no perímetro da página
- Código de cor: vermelho = ErrorBlocking, laranja = ErrorFixable, amarelo = Warning

**Implementação do overlay:**
O overlay é desenhado diretamente sobre o bitmap RGBA resultante da rasterização, usando código C++ puro (sem dependência adicional). Operações simples de plot de retângulo com canal alfa são suficientes.

### Geração Sob Demanda de Outras Páginas

```
GET /v1/jobs/{job_id}/preview/{page_index}
```
- Disponível após job em status `completed` ou `manual_review_required`
- Executa rasterização da página específica sob demanda
- Resultado cacheado em storage com TTL de 24h (recriado se necessário)
- Limite: máximo de 10 requisições por job por hora (rate limit para proteção da VPS)

---

## 36. Estratégia de Fila e Processamento Assíncrono em VPS Pequena

### Decisão: Fila em PostgreSQL, sem RabbitMQ no MVP

**Contexto:** O sistema precisa de uma fila de jobs assíncrona. As opções são: (a) RabbitMQ, (b) Redis, (c) fila na tabela jobs do PostgreSQL, (d) SQLite separado.

**Decisão:** Usar **fila na tabela `jobs` do PostgreSQL via polling com `SELECT FOR UPDATE SKIP LOCKED`**.

**Motivo detalhado:**

| Critério | RabbitMQ | PostgreSQL queue |
|---|---|---|
| Processos adicionais | +1 processo (RabbitMQ server) | 0 — já temos PostgreSQL |
| RAM adicional | ~200-300 MB | 0 |
| Complexidade operacional | Alta (config, vhost, usuários, plugins) | Zero adicional |
| Durabilidade de mensagens | Configurável | Nativa — já está no banco |
| At-least-once delivery | Requer ack/nack explícito | Garantido pelo transação |
| Visibilidade de estado | Requer UI separada ou API | Consulta SQL direta |
| Retry e dead-letter | Configuração específica | Simples — UPDATE status |
| Adequação ao volume | Overkill para <100 jobs/dia | Adequado |

**Impacto:** A ausência do RabbitMQ economiza ~250 MB de RAM, elimina um processo para gerenciar, elimina toda a camada de configuração de broker, e mantém toda a auditoria de fila diretamente no banco de dados onde o restante dos dados está.

**Risco:** A fila PostgreSQL tem menor throughput máximo que RabbitMQ. Para volumes acima de ~5.000 jobs/dia com SLA de latência muito baixa, PostgreSQL pode se tornar gargalo.

**Mitigação:** Para o volume inicial (estimado <500 jobs/dia nos primeiros 6 meses), PostgreSQL é mais que suficiente. A abstração `IQueue` permite substituição futura por RabbitMQ ou outro broker sem mudança no código do pipeline. O risco de scale é real mas não imediato.

### Implementação do Polling

```cpp
// queue/queue_poller.cpp

void QueuePoller::Run() {
    while (!stopRequested_) {
        auto job = TryDequeueJob();
        
        if (job.has_value()) {
            if (concurrencyGuard_.TryAcquireSlot(job->id, ClassifyJob(*job))) {
                // Dispara processamento em thread separada (ou fork)
                DispatchJob(std::move(*job));
            } else {
                // Sem slot disponível — devolve para fila (não marca como em_processamento)
                // Job continua em "queued", será pego na próxima iteração
            }
        } else {
            // Fila vazia — aguarda antes de tentar novamente
            std::this_thread::sleep_for(std::chrono::seconds(2));
        }
    }
}

std::optional<JobDescriptor> QueuePoller::TryDequeueJob() {
    // Usa BEGIN + SELECT FOR UPDATE SKIP LOCKED + UPDATE + COMMIT
    // Garante que dois workers simultâneos nunca pegam o mesmo job
    return db_.ExecuteTransaction([this]() -> std::optional<JobDescriptor> {
        auto result = db_.Query(
            "SELECT id, tenant_id, product_preset_id, validation_profile_id, "
            "       original_blob_key, original_size_bytes, page_count "
            "FROM jobs "
            "WHERE status IN ('uploaded', 'queued') "
            "ORDER BY created_at ASC "
            "LIMIT 1 "
            "FOR UPDATE SKIP LOCKED"
        );
        
        if (result.empty()) return std::nullopt;
        
        auto job = ParseJobDescriptor(result[0]);
        
        db_.Execute(
            "UPDATE jobs SET status = 'parsing', picked_at = NOW(), "
            "worker_id = $1, updated_at = NOW() WHERE id = $2",
            {workerId_, job.id}
        );
        
        return job;
    });
}
```

### Controle de Concorrência em Memória

O `ConcurrencyGuard` usa um `std::atomic<int>` para controle de slots ativos. Não usa mutex para o check — apenas para a atualização:

```cpp
class ConcurrencyGuard {
    std::atomic<int> activeHeavyJobs_{0};
    std::atomic<int> activeLightJobs_{0};
    const int maxHeavy_;
    const int maxLight_;
    
public:
    bool TryAcquireSlot(const std::string& jobId, JobWeight weight) {
        if (weight == JobWeight::Heavy) {
            // Não aceita heavy se já há qualquer job ativo (heavy ou light)
            int currentHeavy = activeHeavyJobs_.load();
            int currentLight = activeLightJobs_.load();
            if (currentHeavy > 0 || currentLight > 0) return false;
            return activeHeavyJobs_.compare_exchange_strong(currentHeavy, currentHeavy + 1);
        } else {
            // Aceita light se não há heavy e há slot de light disponível
            int currentHeavy = activeHeavyJobs_.load();
            if (currentHeavy > 0) return false;
            int current = activeLightJobs_.load();
            if (current >= maxLight_) return false;
            return activeLightJobs_.compare_exchange_strong(current, current + 1);
        }
    }
};
```

### Retry e Dead-Letter Logic

```sql
-- Jobs que falharam podem ser recolocados em fila pelo operador (via API admin)
-- Máximo de 3 tentativas por job
ALTER TABLE jobs ADD COLUMN retry_count INT NOT NULL DEFAULT 0;
ALTER TABLE jobs ADD COLUMN max_retries INT NOT NULL DEFAULT 3;

-- Dead-letter: após max_retries tentativas, vai para failed permanente
UPDATE jobs 
SET status = 'failed', error_code = 'MAX_RETRIES_EXCEEDED'
WHERE status = 'queued' AND retry_count >= max_retries;
```

---

## 37. Persistência e Storage

### Decisão: Filesystem Local com Abstração para S3/MinIO

**Decisão tomada:** MVP usa filesystem local (`/var/printguard/storage/`). A abstração `IStorage` permite troca por MinIO ou S3 na fase 2 sem mudança no código do pipeline.

**Por que não MinIO desde o início:**
- MinIO é um processo adicional com ~100 MB de RAM de overhead
- Requer configuração de usuário, bucket, política de acesso
- Para volume inicial, filesystem local é equivalente em performance (ambos em NVMe)
- Filesystem local é mais simples de fazer backup (rsync direto)
- A abstração garante que a troca futura seja transparente

**Por que a abstração desde o início:**
- Não queremos hard-code de paths de filesystem espalhados pelo código
- Quando o volume justificar MinIO (ou quando a gráfica quiser backups em S3), a migração é uma linha de configuração

### Layout Organizado do Filesystem

```
/var/printguard/
├── storage/
│   └── {tenant_id}/          # ex: a1b2c3d4-...
│       ├── originals/
│       │   └── {job_id}.pdf  # ex: job_01J5....pdf
│       ├── corrected/
│       │   └── {job_id}.pdf
│       ├── previews/
│       │   ├── {job_id}_p0.jpg   # preview página 1
│       │   └── {job_id}_p0_overlay.png
│       └── reports/
│           ├── {job_id}_internal.json
│           └── {job_id}_client.json
├── tmp/                       # arquivos temporários de processamento
│   └── {job_id}/             # subdir por job — removido após conclusão
└── config/                    # presets e profiles (read-only em runtime)
```

### Política de Limpeza Automática

```bash
#!/bin/bash
# scripts/cleanup_old_jobs.sh — executado via cron diariamente às 2h

RETENTION_DAYS=${RETENTION_DAYS:-30}
STORAGE_PATH=/var/printguard/storage

# Remove arquivos de jobs com mais de RETENTION_DAYS dias
# Usa API de limpeza interna que também atualiza o banco
/usr/bin/printguard-worker --cleanup --older-than-days=$RETENTION_DAYS
```

```sql
-- SQL de limpeza associado
SELECT id, original_blob_key, corrected_blob_key 
FROM jobs
WHERE completed_at < NOW() - INTERVAL '$RETENTION_DAYS days'
  AND status IN ('completed', 'failed', 'rejected_by_limits');
-- Para cada job: deletar arquivos no storage, limpar artifacts, manter registro do job
-- (manter o job em si para histórico — apenas remover os binários grandes)
```

### Geração de URLs de Download

No MVP, os artefatos são servidos diretamente pelo processo da API via HTTP. Não há CDN nem URLs pré-assinadas no MVP.

```
GET /v1/jobs/{job_id}/download/{artifact_kind}
Authorization: Bearer {api_key}

Fluxo interno:
1. Valida API key e tenant
2. Verifica que job pertence ao tenant
3. Busca blob_key na tabela artifacts
4. Serve arquivo via streaming diretamente do filesystem
```

**Consideração de segurança:** arquivos nunca são servidos por path direto de filesystem. Sempre via controller que valida autorização. Não há URL pública sem autenticação.

---

## 38. Relatórios Internos e Externos

### 38.1 — Relatório Interno (Técnico/Audit)

O relatório interno contém tudo que é necessário para auditoria, debugging e suporte. É gerado em JSON e destinado a operadores e desenvolvedores.

```json
{
  "report_version": "1.0",
  "generated_at": "2026-04-18T15:30:00Z",
  "job": {
    "id": "job_01J5KXYZ...",
    "tenant_id": "tenant_abc...",
    "product_preset": "business_card",
    "validation_profile": "digital_print_standard",
    "original_filename": "cartao_visita_cliente.pdf",
    "original_size_bytes": 2457600,
    "page_count": 2,
    "status": "completed"
  },
  "software": {
    "version": "0.1.0",
    "rules_version": "0.1.0",
    "build_date": "2026-04-18"
  },
  "checksums": {
    "original_sha256": "a3f7b2...",
    "corrected_sha256": "9c1e4a..."
  },
  "timings": {
    "total_ms": 12450,
    "parse_ms": 850,
    "analyze_ms": 1200,
    "fix_ms": 8300,
    "revalidate_ms": 900,
    "preview_ms": 1200
  },
  "initial_findings": [
    {
      "code": "CLR001",
      "title": "Espaço de cor RGB detectado",
      "category": "color",
      "severity": "ErrorFixable",
      "fixability": "AutomaticSafe",
      "page_index": 0,
      "description": "Página 1 contém objetos em DeviceRGB...",
      "evidence": [
        "Espaço de cor: DeviceRGB",
        "Objetos afetados: 3 imagens, 2 fills vetoriais",
        "Imagem img_0: 1200x800px, DeviceRGB"
      ]
    }
  ],
  "fix_plan": {
    "planned_fixes": ["ConvertRgbToCmykFix", "AttachOutputIntentFix"],
    "skipped_fixes": [],
    "has_blocking_unresolved": false
  },
  "fixes_applied": [
    {
      "fix_id": "AttachOutputIntentFix",
      "finding_code": "CLR002",
      "risky": false,
      "success": true,
      "duration_ms": 12,
      "details": {
        "profile_attached": "GRACoL2013",
        "profile_source": "system_default"
      }
    },
    {
      "fix_id": "ConvertRgbToCmykFix",
      "finding_code": "CLR001",
      "risky": false,
      "success": true,
      "duration_ms": 8240,
      "details": {
        "images_converted": 3,
        "vector_fills_converted": 2,
        "source_profile": "sRGB",
        "dest_profile": "GRACoL2013",
        "rendering_intent": "Perceptual",
        "gamut_warnings": 0
      }
    }
  ],
  "postfix_findings": [
    {
      "code": "GEO002",
      "title": "Sangria insuficiente",
      "severity": "Warning",
      "description": "BleedBox encontrada mas menor que o mínimo recomendado de 3mm"
    }
  ],
  "revalidation": {
    "resolved_findings": ["CLR001", "CLR002"],
    "unresolved_findings": ["GEO002"],
    "new_findings_introduced": [],
    "blocking_errors_remaining": 0
  }
}
```

### 38.2 — Relatório de Cliente (Amigável)

O relatório de cliente usa linguagem não técnica, em português, focado no que o cliente precisa saber e fazer.

```json
{
  "report_version": "1.0",
  "generated_at": "2026-04-18T15:30:00Z",
  "job_id": "job_01J5KXYZ...",
  "summary": {
    "status": "optimized_with_warnings",
    "headline": "Seu arquivo foi otimizado para impressão",
    "description": "Encontramos 3 pontos de atenção no seu arquivo. Corrigimos 2 automaticamente. Há 1 ponto que recomendamos que você verifique, mas não impedirá a impressão.",
    "can_proceed": true
  },
  "corrections_made": [
    {
      "title": "Cores convertidas para impressão",
      "description": "Seu arquivo estava em formato de cor RGB (ideal para telas). Convertemos automaticamente para CMYK, que é o padrão de impressão. As cores podem ter pequenas variações — isso é normal no processo de impressão.",
      "icon": "check_circle"
    },
    {
      "title": "Perfil de cor adicionado",
      "description": "Adicionamos um perfil de cor padrão ao arquivo para garantir reprodução consistente na impressora.",
      "icon": "check_circle"
    }
  ],
  "warnings": [
    {
      "title": "Sangria menor que o recomendado",
      "description": "A área de corte seguro do seu arquivo está um pouco menor que o ideal (2mm ao invés de 3mm). Isso significa que o corte pode mostrar uma pequena borda branca em alguns exemplares. Se possível, abra seu arquivo e aumente a sangria para 3mm em todos os lados.",
      "can_proceed_anyway": true,
      "action_required": false,
      "icon": "warning"
    }
  ],
  "artifacts": {
    "original_pdf": "/v1/jobs/job_01J5KXYZ.../download/original_pdf",
    "corrected_pdf": "/v1/jobs/job_01J5KXYZ.../download/corrected_pdf",
    "preview_jpg": "/v1/jobs/job_01J5KXYZ.../download/preview_jpg"
  }
}
```

**Princípios do relatório de cliente:**
- Nunca usar siglas técnicas sem explicação (CMYK, DPI, TrimBox)
- Sempre indicar claramente o que pode prosseguir e o que bloqueia
- Usar linguagem de "nós fizemos por você" para correções automáticas
- Para warnings: explicar o impacto real, não o problema técnico
- Para erros bloqueantes: dar instrução clara e específica de como corrigir

---

## 39. Contratos de API

### Autenticação

Todas as requisições precisam do header:
```
Authorization: Bearer {api_key}
```

A API key é validada contra o hash SHA-256 na tabela `api_keys`. Nunca armazena a key em claro.

### Endpoints do MVP

#### POST /v1/jobs — Criar Job

```http
POST /v1/jobs
Content-Type: multipart/form-data
Authorization: Bearer {api_key}

Campos do form:
- file: (binary) — o PDF
- preset: string — ex: "business_card"
- profile: string — ex: "digital_print_standard" (opcional, default: "digital_print_standard")
- metadata: JSON string (opcional) — ex: {"order_id": "ORD-123", "client_name": "ACME"}
```

**Resposta de sucesso (202 Accepted):**
```json
{
  "job_id": "job_01J5KXYZ...",
  "status": "uploaded",
  "created_at": "2026-04-18T15:00:00Z",
  "estimated_completion_seconds": 30
}
```

**Resposta de erro — arquivo muito grande (413):**
```json
{
  "error": "FILE_TOO_LARGE",
  "message": "O arquivo excede o tamanho máximo permitido de 80 MB.",
  "limit_bytes": 83886080,
  "received_bytes": 95000000
}
```

**Resposta de erro — preset inválido (400):**
```json
{
  "error": "INVALID_PRESET",
  "message": "O preset 'invalid_preset' não existe.",
  "available_presets": ["business_card", "flyer_a5", "invitation_10x15", "sticker_square", "poster_a3"]
}
```

#### GET /v1/jobs/{job_id} — Status e Detalhes do Job

```json
{
  "job_id": "job_01J5KXYZ...",
  "status": "completed",
  "preset": "business_card",
  "profile": "digital_print_standard",
  "original_filename": "cartao_visita.pdf",
  "page_count": 2,
  "created_at": "2026-04-18T15:00:00Z",
  "completed_at": "2026-04-18T15:00:42Z",
  "duration_seconds": 42,
  "summary": {
    "initial_findings_count": 3,
    "fixes_applied_count": 2,
    "postfix_findings_count": 1,
    "blocking_errors_remaining": 0,
    "can_proceed": true
  },
  "artifacts": {
    "original_pdf": "/v1/jobs/job_01J5KXYZ.../download/original_pdf",
    "corrected_pdf": "/v1/jobs/job_01J5KXYZ.../download/corrected_pdf",
    "preview_jpg": "/v1/jobs/job_01J5KXYZ.../download/preview_jpg",
    "overlay_png": "/v1/jobs/job_01J5KXYZ.../download/overlay_png",
    "report_internal": "/v1/jobs/job_01J5KXYZ.../download/report_internal",
    "report_client": "/v1/jobs/job_01J5KXYZ.../download/report_client"
  }
}
```

#### GET /v1/jobs/{job_id}/findings — Lista de Findings

```json
{
  "job_id": "job_01J5KXYZ...",
  "findings": {
    "initial": [
      {
        "code": "CLR001",
        "title": "Espaço de cor RGB detectado",
        "category": "color",
        "severity": "ErrorFixable",
        "fixability": "AutomaticSafe",
        "page_index": 0,
        "description": "...",
        "evidence": ["..."]
      }
    ],
    "postfix": [
      {
        "code": "GEO002",
        "title": "Sangria insuficiente",
        "severity": "Warning",
        "fixability": "None"
      }
    ]
  }
}
```

#### GET /v1/jobs/{job_id}/download/{kind} — Download de Artefato

Kinds válidos: `original_pdf`, `corrected_pdf`, `preview_jpg`, `overlay_png`, `report_internal`, `report_client`

```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="cartao_visita_corrected.pdf"
Content-Length: 2150400

[binary stream]
```

#### GET /v1/presets — Lista Presets Disponíveis

```json
{
  "presets": [
    {
      "id": "business_card",
      "name": "Cartão de Visita",
      "description": "90x50mm, sangria 3mm",
      "dimensions": {"width_mm": 90, "height_mm": 50},
      "bleed_mm": 3.0
    }
  ]
}
```

#### GET /v1/health — Healthcheck

```json
{
  "status": "ok",
  "version": "0.1.0",
  "database": "ok",
  "storage": "ok",
  "worker": {
    "status": "running",
    "active_jobs": 1,
    "queued_jobs": 3
  },
  "timestamp": "2026-04-18T15:00:00Z"
}
```

---

## 40. Modelo de Orquestração

### PipelineOrchestrator

O orchestrator é o controlador central do fluxo de processamento de um job. Recebe um `JobDescriptor` e executa todas as etapas em sequência, atualizando o status no banco em cada transição.

```cpp
// orchestration/pipeline_orchestrator.cpp

class PipelineOrchestrator {
public:
    void Execute(const JobDescriptor& job) {
        try {
            // 1. Setup
            UpdateStatus(job.id, "parsing");
            auto workDir = PrepareWorkDir(job.id);
            auto originalPath = storage_->Get(job.originalBlobKey, workDir);
            
            // 2. Parse com timeout
            auto document = WithTimeout(parseTimeout_, [&]() {
                return pdfLoader_->Load(originalPath, job);
            }, "parse_timeout");
            
            // 3. Análise
            UpdateStatus(job.id, "analyzing");
            auto ruleCtx = BuildRuleContext(document, job);
            auto findings = WithTimeout(analysisTimeout_, [&]() {
                return ruleEngine_->RunAll(ruleCtx);
            }, "analysis_timeout");
            PersistFindings(job.id, findings, "initial");
            
            // 4. Planejamento
            UpdateStatus(job.id, "planning_fixes");
            auto fixPlan = fixPlanner_->BuildPlan(findings, GetProfile(job), GetFixes());
            
            // 5. Correção (somente se há fixes a aplicar)
            std::string correctedPath = originalPath; // fallback = original
            if (!fixPlan.actions.empty()) {
                UpdateStatus(job.id, "fixing");
                correctedPath = MakeCorrectedCopy(originalPath, job.id);
                auto fixCtx = BuildFixContext(correctedPath, document, job);
                WithTimeout(fixTimeout_, [&]() {
                    fixEngine_->Execute(fixPlan, fixCtx);
                }, "fix_timeout");
                PersistFixes(job.id, fixCtx.auditLog);
            }
            
            // 6. Revalidação
            UpdateStatus(job.id, "revalidating");
            auto correctedDocument = pdfLoader_->Load(correctedPath, job);
            auto postFixFindings = ruleEngine_->RunAll(BuildRuleContext(correctedDocument, job));
            PersistFindings(job.id, postFixFindings, "postfix");
            
            // 7. Preview
            UpdateStatus(job.id, "rendering_preview");
            auto previewResult = TryRenderPreview(correctedPath, postFixFindings, job.id);
            
            // 8. Relatórios
            UpdateStatus(job.id, "generating_reports");
            auto reports = reportEngine_->Generate(job, findings, postFixFindings, 
                                                    fixPlan, fixCtx.auditLog);
            PersistArtifacts(job.id, originalPath, correctedPath, previewResult, reports);
            
            // 9. Status final
            bool hasBlockingRemaining = HasBlockingErrors(postFixFindings);
            bool hasUnresolvedFixes = fixPlan.hasBlockingUnresolved;
            
            if (hasBlockingRemaining || hasUnresolvedFixes) {
                UpdateStatus(job.id, "manual_review_required");
            } else {
                UpdateStatus(job.id, "completed");
            }
            
        } catch (const TimeoutError& e) {
            UpdateJobFailed(job.id, e.stage(), e.what());
        } catch (const std::exception& e) {
            UpdateJobFailed(job.id, "unknown", e.what());
        }
        
        CleanupWorkDir(job.id);
    }
};
```

---

## 41. Observabilidade

### Logging Estruturado

Todos os logs são emitidos em formato JSON Lines (um objeto JSON por linha) via `spdlog`. Configuração por variável de ambiente (`LOG_LEVEL=info|debug|warn|error`).

```json
// Exemplo de log de início de job
{"timestamp":"2026-04-18T15:00:00.123Z","level":"info","service":"worker","job_id":"job_01J5...","tenant_id":"tenant_abc...","event":"job_started","preset":"business_card","file_size_bytes":2457600,"page_count":2}

// Exemplo de log de fix aplicado
{"timestamp":"2026-04-18T15:00:08.456Z","level":"info","service":"worker","job_id":"job_01J5...","event":"fix_applied","fix_id":"ConvertRgbToCmykFix","duration_ms":8240,"success":true}

// Exemplo de log de erro
{"timestamp":"2026-04-18T15:00:30.789Z","level":"error","service":"worker","job_id":"job_01J5...","event":"fix_failed","fix_id":"EmbedFontsFix","reason":"font_not_found_in_system","error":"Could not locate font 'CustomFont-Bold'"}
```

### Rotação de Logs

```bash
# /etc/logrotate.d/printguard
/var/log/printguard/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    postrotate
        systemctl reload printguard-api printguard-worker 2>/dev/null || true
    endscript
}
```

### Métricas Básicas (sem Prometheus no MVP)

No MVP, métricas são disponíveis via o endpoint `/v1/health` e por queries diretas ao banco. Para o MVP, não há Prometheus ou Grafana — o overhead não justifica. Na fase 2, adicionar `prometheus-cpp` e expor métricas em `/metrics`.

**Métricas consultáveis via SQL:**

```sql
-- Jobs por status nas últimas 24h
SELECT status, COUNT(*) 
FROM jobs 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY status;

-- Tempo médio de processamento por preset
SELECT product_preset_id, AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) AS avg_seconds
FROM jobs 
WHERE status = 'completed' AND completed_at IS NOT NULL
GROUP BY product_preset_id;

-- Taxa de sucesso de fixes
SELECT fix_id, 
       COUNT(*) FILTER (WHERE success) AS succeeded,
       COUNT(*) FILTER (WHERE NOT success) AS failed
FROM fixes_applied
GROUP BY fix_id;
```

### Alertas Simples

No MVP, usar script de healthcheck chamado via cron a cada 5 minutos:

```bash
#!/bin/bash
# scripts/healthcheck.sh

RESPONSE=$(curl -sf http://localhost:8080/v1/health 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "ALERT: PrintGuard API não responde" | mail -s "[ALERT] PrintGuard Down" ops@empresa.com
    exit 1
fi

WORKER_STATUS=$(echo "$RESPONSE" | jq -r '.worker.status')
if [ "$WORKER_STATUS" != "running" ]; then
    echo "ALERT: Worker parado" | mail -s "[ALERT] PrintGuard Worker Down" ops@empresa.com
fi
```

---

## 42. Segurança

### Autenticação e Autorização

- **API Keys**: hash SHA-256 armazenado no banco. A key em si nunca é armazenada — apenas o hash.
- **Isolamento por tenant**: toda query ao banco inclui `tenant_id` como filtro. Impossível acessar dados de outro tenant com uma API key válida.
- **Sem JWT no MVP**: API keys são simples e suficientes para o modelo B2B descrito. JWT seria overhead para o volume e modelo de uso inicial.

### Segurança de Upload

- **Validação de magic bytes**: antes de processar, verificar que o arquivo começa com `%PDF-` (magic bytes do PDF). Rejeitar uploads com extensão .pdf mas conteúdo não-PDF.
- **Tamanho máximo na camada HTTP**: limitar request body antes de chegar ao handler (configuração do servidor HTTP).
- **Armazenamento em path controlado**: arquivos salvos em paths com UUID como nome — nunca usar o nome original do arquivo como nome no filesystem (path traversal prevention).
- **Sem execução do PDF**: o sistema nunca executa scripts JavaScript embutidos no PDF. QPDF e MuPDF operam no nível de estrutura, sem engine JavaScript.

### Segurança da VPS

- SSH apenas com chave pública (sem password auth)
- Firewall UFW: apenas portas 22 (SSH), 80 (HTTP redirect), 443 (HTTPS futura) abertas
- Processo da API roda como usuário `printguard` (não root)
- Processo do worker roda como usuário `printguard` (não root)
- Permissões de filesystem: `/var/printguard/storage/` acessível apenas pelo usuário `printguard`
- PostgreSQL: socket Unix local, sem porta TCP exposta externamente

### HTTPS

No MVP, usar Let's Encrypt via Certbot com nginx como proxy reverso. O binário da API escuta em `localhost:8080`; o nginx faz proxy e gerencia TLS.

```nginx
server {
    listen 443 ssl;
    server_name api.printguard.app;
    
    ssl_certificate /etc/letsencrypt/live/api.printguard.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.printguard.app/privkey.pem;
    
    client_max_body_size 100M;  # limite de upload
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header X-Tenant-ID $http_x_tenant_id;
        proxy_read_timeout 120s;
    }
}
```

### Proteção contra Abuso

- **Rate limiting por API key** (implementar na fase 2): no MVP, limitar via nginx (`limit_req_zone`) por IP
- **Tamanho de arquivo**: validado na API antes do disco
- **Número de jobs simultâneos por tenant**: configurável — no MVP, sem limite por tenant (limite global no worker)

---

## 43. Multi-Tenancy

### Modelo de Isolamento

O PrintGuard usa **multi-tenancy lógico** — todos os tenants compartilham o mesmo banco de dados e o mesmo filesystem, mas com isolamento garantido por `tenant_id` em todas as tabelas e paths de storage.

**Por que não multi-tenancy físico (banco separado por tenant):**
- Inviável para uma VPS pequena com muitos tenants
- Overhead operacional alto (N bancos para gerenciar)
- Para o volume e tamanho dos tenants no MVP, isolamento lógico é suficiente e seguro

**Garantias de isolamento:**

1. **Banco**: toda query inclui `WHERE tenant_id = $tenant_id`. Impossível acessar registro de outro tenant sem ter o `tenant_id` correto.

2. **Storage**: todos os arquivos ficam em `/var/printguard/storage/{tenant_id}/`. A resolução de path de download sempre inclui verificação do tenant.

3. **API**: a API key valida o `tenant_id` na primeira instrução de qualquer handler. Qualquer acesso a recurso que não pertença ao tenant autenticado resulta em 404 (não 403 — não confirmar existência).

4. **Relatórios**: relatórios nunca incluem dados de outros tenants.

### Configurações por Tenant (Futuro)

Na fase 2, cada tenant poderá configurar:
- Perfil ICC padrão para conversão de cor
- Presets customizados (além dos padrão)
- Retention period de arquivos
- Webhooks de notificação
- Limite de tamanho de arquivo próprio (dentro do limite global)

---

## 44. Escalabilidade

### Trajetória de Escalabilidade Planejada

| Fase | Volume esperado | Infraestrutura | Bottleneck |
|---|---|---|---|
| MVP | <100 jobs/dia | 1 VPS 2vCPU/8GB | CPU do worker |
| Fase 2 | 100-1000 jobs/dia | 1 VPS 4vCPU/16GB (upgrade Hostinger) | CPU + disco |
| Fase 3 | 1000-5000 jobs/dia | 1 VPS grande + 1 worker dedicado | Fila, banco |
| Fase 4 | >5000 jobs/dia | Múltiplas VPS + MinIO + PostgreSQL dedicado | Arquitetura |

### O que Permite Escalar sem Reescrever

1. **Abstração IQueue**: substituir polling PostgreSQL por RabbitMQ sem mudar o pipeline
2. **Abstração IStorage**: substituir filesystem por MinIO/S3 sem mudar o pipeline
3. **Worker como processo separado**: adicionar segundo worker em outra máquina apenas configurando conexão com o mesmo banco e storage
4. **Stateless API**: a API não tem estado — adicionar segundo servidor de API é trivial (ambos leem/escrevem no mesmo banco)

### Limitações Conhecidas no MVP

- **Single point of failure**: uma VPS cai = serviço cai. Não há HA no MVP.
- **Storage local não compartilhável**: se houver dois workers em máquinas diferentes, ambos precisam acessar o mesmo storage (precisa migrar para MinIO nesse cenário).
- **Concorrência fixa**: o número de jobs simultâneos é configurado no binário, não auto-escalonado.

Essas limitações são **aceitáveis para o MVP** e devem ser documentadas para clientes durante o período de beta.

---

## 45. Performance e Benchmarks

### Metas de Performance para o MVP

| Operação | Meta | Medido em |
|---|---|---|
| Upload e criação do job | <500ms | Tempo de response do POST |
| Parse de PDF simples (1-2 páginas, <5MB) | <2s | Tempo de parse no worker |
| Parse de PDF médio (10 páginas, 20MB) | <8s | Tempo de parse no worker |
| Análise de regras (15 regras, doc médio) | <3s | Tempo de analysis |
| Conversão RGB→CMYK (1 imagem 300DPI) | <5s | Tempo de fix |
| Conversão RGB→CMYK (documento com 5 imagens) | <30s | Tempo de fix |
| Preview de primeira página | <15s | Tempo de render |
| Job completo end-to-end (cartão de visita simples) | <60s | Tempo total de pipeline |
| Job completo end-to-end (flyer A5 complexo, RGB) | <120s | Tempo total de pipeline |

### Benchmarks Automatizados

```cpp
// benchmarks/parse_bench.cpp

static void BM_ParseSmallPdf(benchmark::State& state) {
    for (auto _ : state) {
        QPDF pdf;
        pdf.processFile("test_data/business_card_simple.pdf");
        auto pages = QPDFPageDocumentHelper(pdf).getAllPages();
        benchmark::DoNotOptimize(pages);
    }
}
BENCHMARK(BM_ParseSmallPdf);

static void BM_ParseLargePdf(benchmark::State& state) {
    for (auto _ : state) {
        QPDF pdf;
        pdf.processFile("test_data/catalog_40pages.pdf");
        auto pages = QPDFPageDocumentHelper(pdf).getAllPages();
        benchmark::DoNotOptimize(pages);
    }
}
BENCHMARK(BM_ParseLargePdf);
```

### Gerenciamento de Memória por Job

O pipeline deve monitorar e limitar uso de memória:

```cpp
// Após cada etapa pesada, verificar uso de memória
size_t GetProcessRssBytes() {
    std::ifstream status("/proc/self/status");
    // Lê VmRSS da linha "VmRSS: N kB"
    // Retorna em bytes
}

// Em cada ponto de checkpoint:
if (GetProcessRssBytes() > MAX_JOB_RAM_BYTES) {
    throw MemoryLimitExceeded("Job excedeu limite de " + 
                               std::to_string(MAX_JOB_RAM_BYTES / (1024*1024)) + "MB");
}
```

---

## 46. Estratégia de Testes

### Pirâmide de Testes

```
         /\
        /  \
       / E2E \          API integration tests com PDF real
      /--------\
     /Integration\      Pipeline completo por módulo
    /--------------\
   /   Unit Tests   \   Regras, fixes, planner, parser, report
  /------------------\
```

### Testes Unitários

Cada regra e cada fix deve ter testes unitários isolados. O `DocumentModel` é construído programaticamente nos testes — sem necessidade de PDF real.

```cpp
// tests/unit/rules/test_color_space_rule.cpp

TEST(ColorSpaceRule, DetectsRgbOnFirstPage) {
    DocumentModel doc;
    PageModel page;
    page.index = 0;
    page.colorSpaces.push_back({"DeviceRGB"});
    doc.pages.push_back(page);
    
    ProductPreset preset = BuildPreset("business_card");
    ValidationProfile profile = BuildProfile("digital_print_standard");
    
    RuleContext ctx{doc, preset, profile};
    ColorSpaceRule rule;
    
    auto findings = rule.Evaluate(ctx);
    
    ASSERT_EQ(findings.size(), 1);
    EXPECT_EQ(findings[0].code, "CLR001");
    EXPECT_EQ(findings[0].severity, Severity::ErrorFixable);
    EXPECT_EQ(findings[0].pageIndex, 0);
}

TEST(ColorSpaceRule, NoFindingsForCmyk) {
    DocumentModel doc;
    PageModel page;
    page.colorSpaces.push_back({"DeviceCMYK"});
    doc.pages.push_back(page);
    // ... assert findings.empty()
}

TEST(ColorSpaceRule, LenientProfileDowngradesToWarning) {
    // ... profile.treatRgbAsBlocking = false
    // ... severity deve ser Warning, não ErrorFixable
}
```

### Golden Tests (Testes de Regressão)

PDFs de referência com problemas conhecidos e relatórios JSON esperados. Cada vez que o sistema processa um PDF de golden test, o resultado é comparado com o esperado.

```
tests/golden/
├── pdfs/
│   ├── business_card_rgb_no_bleed.pdf       # cartão RGB sem sangria
│   ├── flyer_a5_correct.pdf                  # flyer correto — deve ter 0 blocking errors
│   ├── poster_encrypted.pdf                  # poster criptografado — deve rejeitar
│   └── invitation_spot_colors.pdf            # convite com spot colors
└── expected/
    ├── business_card_rgb_no_bleed_findings.json
    ├── flyer_a5_correct_findings.json         # deve ser vazio ou só Info
    ├── poster_encrypted_result.json           # status = failed, STR003
    └── invitation_spot_colors_findings.json
```

### Testes de Integração do Pipeline

Testam o pipeline completo com PDFs reais (ou sintéticos gerados por QPDF em código de teste):

```cpp
// tests/integration/pipeline/test_full_pipeline.cpp

TEST(FullPipeline, BusinessCardRgbIsProcessedAndConverted) {
    auto jobDesc = CreateTestJob("business_card", "digital_print_standard",
                                  "tests/pdfs/business_card_rgb.pdf");
    
    TestPipelineOrchestrator orchestrator = BuildTestOrchestrator();
    orchestrator.Execute(jobDesc);
    
    auto result = FetchJobResult(jobDesc.id);
    
    EXPECT_EQ(result.status, "completed");
    EXPECT_TRUE(result.HasFix("ConvertRgbToCmykFix"));
    EXPECT_FALSE(result.HasPostfixFinding("CLR001"));  // RGB foi resolvido
    EXPECT_TRUE(result.HasCorrectedPdf());
    EXPECT_TRUE(result.HasPreviewJpg());
}
```

### Testes de API

```cpp
// tests/integration/api/test_job_api.cpp

TEST(JobApi, UploadAndProcessJob) {
    auto client = BuildTestApiClient(testApiKey_);
    
    auto response = client.PostJob("tests/pdfs/business_card_simple.pdf", 
                                    "business_card", "digital_print_standard");
    
    EXPECT_EQ(response.status_code, 202);
    EXPECT_FALSE(response.job_id.empty());
    
    // Polling até completion (com timeout de 120s no teste)
    auto result = client.WaitForCompletion(response.job_id, 120s);
    
    EXPECT_EQ(result.status, "completed");
}
```

### Cobertura Mínima Exigida

| Módulo | Cobertura mínima |
|---|---|
| `analysis/rules/` | 85% |
| `fix/fixes/` | 80% |
| `fix/fix_planner.cpp` | 90% |
| `report/` | 75% |
| `pdf/pdf_loader.cpp` | 70% |
| `color/color_engine.cpp` | 75% |
| `queue/` | 80% |

---

## 47. Riscos Técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| QPDF não suporta estrutura de PDF incomum | Média | Alto | Capturar exceções QPDF, marcar job como failed com código específico, nunca crashar o worker |
| Conversão de cor produz resultado inesperado (gamut out) | Alta | Médio | Logar gamut warnings, avisar cliente, usar rendering intent Perceptual |
| MuPDF OOM em PDF com imagens 4K | Média | Alto | Limite de tamanho de arquivo, timeout de preview, fallback: pular preview |
| Fix introduz corrupção de PDF | Baixa | Crítico | Validação de integridade após cada fix, teste golden extensivo, preservação do original |
| Disco cheio na VPS | Média | Alto | Monitor de disco, limpeza automática, alertas |
| Worker OOM (8GB insuficiente) | Média | Alto | Fork por job (isolamento de memória), limite de concorrência, rejeição de arquivos muito grandes |
| PostgreSQL lento sob carga de polling | Baixa | Médio | Index correto em (status, created_at), SKIP LOCKED evita lock contention |
| Fonte não encontrada no sistema para EmbedFontsFix | Alta (fase 2) | Médio | Manter fix fora do MVP, quando implementar: fallback para OutlineFontsFix |
| Dependências C++ com vulnerabilidades de segurança | Baixa | Alto | Política de atualização de dependências a cada 3 meses, monitorar CVE |
| PDF com JavaScript malicioso | Baixa | Médio | QPDF não executa JS. MuPDF tem opção de desabilitar JS. Validar na abertura |

---

## 48. Trade-offs Arquiteturais

### 48.1 — Monólito Modular vs. Microsserviços

**Decisão: Monólito Modular**

O ganho de independência de deploy e scaling que microsserviços oferecem é real, mas só se materializa quando há:
- Volume suficiente para justificar múltiplos servidores
- Equipe suficiente para operar múltiplos serviços
- Componentes com necessidades de scaling radicalmente diferentes

Nenhuma dessas condições existe no MVP. Monólito modular com interfaces bem definidas é a resposta correta. A refatoração para microsserviços é possível quando necessária.

### 48.2 — Filesystem Local vs. S3/MinIO no MVP

**Decisão: Filesystem Local com Abstração**

MinIO teria custo de:
- ~100-150 MB de RAM permanentemente
- Configuração de bucket, usuário, políticas
- Um processo adicional a monitorar e reiniciar

O benefício (interface S3-compatible para migração futura) existe mas é prematuro. A abstração `IStorage` fornece o mesmo benefício sem o custo.

**Atenção:** a decisão deve ser revista quando houver necessidade de múltiplos workers em máquinas diferentes. Nesse cenário, filesystem local se torna bloqueador e a migração para MinIO se torna obrigatória.

### 48.3 — RabbitMQ vs. Fila em PostgreSQL no MVP

**Decisão: Fila em PostgreSQL**

Reiterado de forma clara: RabbitMQ é desnecessário e prejudicial para o MVP nessa infraestrutura. Adiciona processo, RAM, configuração e complexidade operacional sem benefício real no volume inicial. A fila em PostgreSQL com `SELECT FOR UPDATE SKIP LOCKED` é robusta, durável, auditável e operacionalmente simples.

### 48.4 — Preview Completo vs. Preview Parcial

**Decisão: Preview da Primeira Página Apenas**

Renderizar todas as páginas de um job de 40 páginas consumiria CPU excessivamente e poderia levar vários minutos. A primeira página cobre >90% dos casos de uso do preview (visualização geral, verificação de composição básica). Páginas adicionais sob demanda são a solução correta para os outros 10%.

### 48.5 — Concorrência Alta vs. Concorrência Controlada

**Decisão: Concorrência Estritamente Controlada**

1 job pesado por vez. Ponto. Em uma VPS de 2 vCPU / 8 GB, tentar processar 3 jobs simultaneamente resulta em:
- Trashing de memória
- CPU saturada sem ganho de throughput
- Timeouts cruzados
- Degradação de qualidade dos resultados

Melhor entregar 1 job bem processado por vez do que 3 jobs mal processados ou com falhas.

### 48.6 — Correções Automáticas Amplas vs. Conservadoras

**Decisão: Conservadoras no MVP**

O sistema deve ganhar confiança do usuário antes de expandir o escopo de correções automáticas. No MVP:
- Corrigir apenas o que é seguro e reversível
- Sinalizar o resto com contexto claro
- Não tentar corrigir o que pode piorar o arquivo

A reputação do sistema de "nunca piora o arquivo" vale mais do que "tenta corrigir tudo". Isso é crítico para adoção em gráficas que têm responsabilidade comercial com seus clientes.

---

## 49. Roadmap por Milestones

### Milestone 1 — Fundação (Semanas 1-4)

**Meta:** Pipeline básico funcionando end-to-end com análise e relatório.

**Entregas:**
- Estrutura do repositório, CMake configurado
- Módulo `common/` (logger, config, UUID, Result<T>)
- Módulo `domain/` (tipos fundamentais)
- Módulo `pdf/` — PdfLoader com QPDF (parse, DocumentModel)
- Módulo `persistence/` — JobRepository, FindingRepository com PostgreSQL
- Módulo `storage/` — LocalFileStorage
- Módulo `queue/` — PostgresQueue com polling
- Regras: GEO001, GEO002, GEO003, GEO004, GEO005, CLR001, CLR002, RES001, STR003
- Módulo `analysis/` — RuleEngine
- Módulo `report/` — ReportEngine (relatório interno apenas)
- API REST: POST /v1/jobs, GET /v1/jobs/:id
- Worker básico: parse + analyze + report (sem fixes ainda)
- Testes unitários das regras (>80% cobertura)
- Golden tests com 3 PDFs de referência
- Deploy na VPS com systemd

**Critério de aceite:** Upload de PDF, análise executada, relatório interno gerado com findings corretos em <30s.

### Milestone 2 — Correção e Preview (Semanas 5-8)

**Meta:** Fixes seguros implementados, revalidação, preview gerado.

**Entregas:**
- Módulo `fix/` — FixPlanner + FixEngine
- Módulo `color/` — ColorEngine com LittleCMS2
- Fixes: NormalizeBoxesFix, RotatePageFix, AttachOutputIntentFix, ConvertRgbToCmykFix, ConvertSpotToCmykFix, RemoveWhiteOverprintFix, RemoveLayersFix, RemoveAnnotationsFix
- Revalidação pós-fix
- Módulo `render/` — PreviewRenderer com MuPDF
- Overlay de findings no preview
- Relatório de cliente (amigável) gerado
- Download de todos os artefatos via API
- Controle de concorrência (ConcurrencyGuard)
- Isolamento por fork()
- Timeouts implementados
- Testes de integração do pipeline completo
- Testes de API

**Critério de aceite:** Job completo end-to-end em <60s para cartão de visita RGB simples. PDF corrigido sem RGB. Preview gerado. Relatório de cliente claro.

### Milestone 3 — Produção Real (Semanas 9-12)

**Meta:** Produto estável em produção com primeiros clientes piloto.

**Entregas:**
- Regras adicionais: CLR003, CLR004, CLR005, STR001, STR002, STR004, STR005
- Presets: business_card, flyer_a5, invitation_10x15, sticker_square, poster_a3
- Validation profiles: 3 perfis
- Multi-tenancy com API keys
- Segurança: HTTPS, autenticação, isolamento de tenant
- Limpeza automática de arquivos (cron)
- Reconciliação de jobs presos
- Healthcheck e alertas básicos
- Documentação da API (OpenAPI YAML)
- Onboarding de primeiros 3-5 clientes piloto
- Monitoramento básico (logs + healthcheck)

**Critério de aceite:** 3 gráficas usando em produção real por 2 semanas sem incidentes críticos.

### Milestone 4 — Operação Matura (Semanas 13-20)

**Meta:** Produto polido com base de clientes crescente.

**Entregas:**
- Fase 2 de fixes: EmbedFontsFix, OutlineFontsFix, FlattenTransparencyFix (após validação extensa)
- Interface web básica para operadores
- Modo de revisão manual (aprovação de fixes arriscados)
- Webhook de notificação de conclusão de job
- Dashboard de uso por tenant
- Métricas de produto (KPIs automatizados)
- SDK JavaScript básico para integração
- Documentação detalhada de integração
- Rate limiting por tenant
- Preview sob demanda de páginas adicionais

---

## 50. Critérios de Aceite do MVP

O MVP é considerado aceito quando:

**Funcionais:**
- [ ] Upload de PDF via API retorna job_id em <500ms
- [ ] Job completo (análise + fixes + preview + relatório) concluído em <60s para cartão de visita simples (<5MB, 2 páginas)
- [ ] As 15 regras do catálogo inicial detectam problemas corretamente (validado por golden tests)
- [ ] Os 8 fixes seguros do MVP são aplicados e verificados em golden tests
- [ ] Revalidação detecta corretamente quando problema foi resolvido ou permanece
- [ ] Preview JPEG da primeira página gerado com qualidade de visualização adequada
- [ ] Overlay de problems visível e informativo
- [ ] Relatório interno contém todas as evidências necessárias para debugging
- [ ] Relatório de cliente é compreensível por usuário sem conhecimento técnico (validado por teste com persona real)
- [ ] PDF original nunca é modificado (checksum idêntico antes e depois)
- [ ] PDF corrigido não corrompido (válido segundo QPDF após escrita)

**Técnicos:**
- [ ] Sistema estável por 72 horas contínuas em VPS descrita sem degradação
- [ ] Consumo de RAM por job ≤1.5 GB no worst case testado
- [ ] Cobertura de testes unitários >80% nos módulos core
- [ ] Zero race conditions em concorrência de 2 jobs light simultâneos
- [ ] Logs estruturados emitidos em todas as etapas do pipeline
- [ ] Healthcheck responde corretamente

**Operacionais:**
- [ ] Deploy documentado e executável em <30 minutos em VPS limpa
- [ ] Processo de atualização (deploy de nova versão) sem downtime >5 minutos
- [ ] Limpeza automática de arquivos funcionando (teste com jobs antigos)
- [ ] Reconciliação de jobs presos funcionando (teste com kill do worker)

---

## 51. KPIs de Produto

| KPI | Definição | Meta MVP (30 dias) | Meta Fase 2 (6 meses) |
|---|---|---|---|
| Tenants ativos | Tenants com ≥1 job nos últimos 30 dias | 5 | 50 |
| Jobs processados/dia | Total de jobs completed + manual_review | 20 | 500 |
| Taxa de sucesso automático | % de jobs em "completed" (vs. manual_review) | >70% | >80% |
| Tempo médio de processamento | Tempo médio de pipeline completo | <60s | <45s |
| Taxa de rejeição por limites | % de jobs rejected_by_limits | <5% | <5% |
| Satisfação do operador | NPS interno dos operadores de gráfica piloto | >7/10 | >8/10 |
| Redução de retrabalho | % redução de jobs que precisaram intervenção manual do operador (vs. baseline pré-PrintGuard) | -40% | -70% |
| Churn de tenant | Tenants que cancelaram no período | 0 no piloto | <10% |

---

## 52. KPIs Técnicos

| KPI | Meta | Alerta |
|---|---|---|
| Uptime da API | >99% mensal | <99% em 24h |
| P95 de tempo de job | <90s | >120s |
| P99 de tempo de job | <180s | >300s |
| Taxa de falha de job (failed/total) | <3% | >5% |
| Consumo de RAM do worker | <6 GB peak | >7 GB |
| Uso de disco | <80% dos 100GB | >85% |
| Taxa de erro da API | <1% de requests 5xx | >2% |
| Tempo de resposta da API (endpoints de status) | <200ms P95 | >500ms P95 |

---

## 53. Modelo de Monetização

### Planos Iniciais

**Starter (Gráficas Pequenas):**
- 100 jobs/mês incluídos
- Presets padrão (5 presets incluídos)
- API + relatórios
- Suporte por e-mail
- R$ 197/mês

**Professional (Gráficas Médias e Plataformas):**
- 1.000 jobs/mês incluídos
- Todos os presets + 3 presets customizados
- Prioridade de fila
- Webhook de notificação
- Suporte prioritário
- R$ 697/mês

**Enterprise (White-label, Alto Volume):**
- 10.000 jobs/mês incluídos
- Presets ilimitados
- SLA garantido
- White-label
- Suporte dedicado
- Preço por negociação (R$ 2.000+/mês)

**Pay-as-you-go para excedentes:**
- R$ 0,25/job acima do limite do plano

### Estratégia de Preço

O pricing é posicionado abaixo do custo de 1 hora de trabalho de um operador de pré-impressão por mês (R$ 197). Se o sistema economizar 10 horas de trabalho por mês, o ROI é imediato. Esse argumento de venda é simples e mensurável.

---

## 54. Estratégia de Rollout

### Fase Beta Fechada (Meses 1-2)

- 3-5 gráficas piloto selecionadas manualmente
- Acesso gratuito durante o beta
- Acompanhamento semanal do uso e feedback
- Foco em: descobrir casos de PDF que o sistema não lida bem, coletar NPS, ajustar relatório de cliente

### Lançamento Limitado (Mês 3)

- Abrir acesso a lista de espera (50 gráficas)
- Plano Starter com desconto de lançamento (R$ 97/mês primeiros 3 meses)
- Documentação pública da API
- Blog post técnico explicando o produto

### Lançamento Geral (Mês 4-5)

- Produto disponível via self-service
- Planos públicos sem desconto
- Parceria com 2-3 plataformas de e-commerce gráfico para integração

### Topologia de Deploy Inicial — Diagrama

```
┌─────────────────────────────────────────────────────────┐
│  Internet                                               │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS 443
┌───────────────────────▼─────────────────────────────────┐
│  Nginx (reverse proxy + TLS termination)                │
│  Porta 443 → proxy → localhost:8080                      │
│  Let's Encrypt / Certbot                                 │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP localhost:8080
┌───────────────────────▼─────────────────────────────────┐
│  VPS Hostinger — Ubuntu 22.04 LTS — 2vCPU / 8GB / 100GB │
│                                                          │
│  printguard-api.service (systemd)                        │
│    └─ Binário: /usr/local/bin/printguard-api             │
│    └─ Escuta: localhost:8080                             │
│                                                          │
│  printguard-worker.service (systemd)                     │
│    └─ Binário: /usr/local/bin/printguard-worker          │
│    └─ 1 processo, polling PostgreSQL                     │
│                                                          │
│  postgresql@15.service (systemd)                         │
│    └─ Socket Unix: /var/run/postgresql/.s.PGSQL.5432     │
│    └─ Banco: printguard_production                       │
│                                                          │
│  nginx.service (systemd)                                 │
│    └─ Porta 443 (TLS) e 80 (redirect)                   │
│                                                          │
│  Cron Jobs:                                              │
│    └─ cleanup_old_jobs.sh (diário 2h)                    │
│    └─ healthcheck.sh (a cada 5 minutos)                  │
│    └─ certbot renew (semanal)                            │
│                                                          │
│  Filesystem:                                             │
│    └─ /var/printguard/storage/ (artefatos)               │
│    └─ /var/log/printguard/ (logs)                        │
└─────────────────────────────────────────────────────────┘
```

### Configurações Systemd

```ini
# /etc/systemd/system/printguard-api.service
[Unit]
Description=PrintGuard API Server
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=printguard
Group=printguard
WorkingDirectory=/opt/printguard
ExecStart=/usr/local/bin/printguard-api
Restart=always
RestartSec=5
EnvironmentFile=/etc/printguard/api.env
StandardOutput=append:/var/log/printguard/api.log
StandardError=append:/var/log/printguard/api_error.log
# Limites de recursos
LimitNOFILE=65536
MemoryMax=1G

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/printguard-worker.service
[Unit]
Description=PrintGuard Worker Process
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=printguard
Group=printguard
WorkingDirectory=/opt/printguard
ExecStart=/usr/local/bin/printguard-worker
Restart=always
RestartSec=10
EnvironmentFile=/etc/printguard/worker.env
StandardOutput=append:/var/log/printguard/worker.log
StandardError=append:/var/log/printguard/worker_error.log
# Limites críticos para estabilidade da VPS
LimitNOFILE=65536
MemoryMax=6G    # Hard limit — systemd mata o processo se exceder
CPUQuota=180%   # Máximo de 1.8 cores (dos 2 disponíveis)

[Install]
WantedBy=multi-user.target
```

### Backup

```bash
# backup diário às 3h via cron
0 3 * * * /opt/printguard/scripts/backup.sh

# backup.sh:
# pg_dump printguard_production | gzip > /backup/db_$(date +%Y%m%d).sql.gz
# rsync -a /var/printguard/storage/ backup-server:/backups/printguard/storage/
# Remove backups com mais de 30 dias
# find /backup -name "*.sql.gz" -mtime +30 -delete
```

---

## 55. Open Questions

As seguintes questões estão abertas e precisam de decisão antes ou durante o desenvolvimento:

1. **Qual servidor HTTP C++ usar?** Candidatos: `cpp-httplib` (header-only, simples), `Crow` (mais features, async), `Drogon` (mais pesado, async). Para o MVP, `cpp-httplib` parece a escolha mais simples. Avaliar se o throughput é suficiente para o volume esperado antes de comprometer.

2. **Como lidar com PDFs com JavaScript embutido?** QPDF não executa JS, mas alguns PDFs usam JS para efeitos de apresentação. O sistema deve: (a) ignorar e prosseguir, (b) remover o JS, ou (c) rejeitar? Proposta: remover JS silenciosamente (é irrelevante para impressão), mas registrar no relatório.

3. **Qual é o DPI mínimo aceitável no perfil lenient?** 100 DPI é muito leniente para materiais de mão, mas pode ser adequado para banners vistos à distância. O perfil deve ser parametrizado por produto ou ter um limite absoluto?

4. **Como tratar PDFs com múltiplos espaços de cor misturados por página?** Um PDF pode ter texto em CMYK, imagens em RGB e elementos em DeviceGray na mesma página. A regra CLR001 deve reportar um finding por combinação ou um finding global?

5. **Threshold de "sangria insuficiente" vs. "sem sangria":** se o documento tem 1.5mm de sangria mas precisa de 3mm, é um Warning ou um ErrorFixable? A decisão afeta quantos jobs vão para manual_review. Proposta: definir threshold de 50% da sangria esperada — abaixo disso é ErrorFixable, acima é Warning.

6. **Relatório de cliente em múltiplos idiomas?** No MVP, apenas português do Brasil. Para expansão internacional, o sistema de mensagens deve estar em arquivo de tradução desde o início ou pode ser refatorado depois?

7. **Preview deve ser gerado do PDF original ou do PDF corrigido?** O overlay deve mostrar os problemas **antes** da correção (no PDF original) ou o resultado **após** a correção (no PDF corrigido). Proposta: preview e overlay são gerados do PDF corrigido, pois é o que será impresso. Problemas não corrigidos são marcados no overlay do PDF corrigido.

8. **Qual é a política de preço para jobs que excedem o plano?** Cobrar pelo excedente automaticamente, bloquear o tenant, ou permitir e cobrar no próximo ciclo? Para evitar surpresas, a proposta é bloquear novos uploads quando o limite é atingido, com notificação e opção de upgrade.

9. **Como o sistema deve se comportar com PDFs que são scans (imagens rasterizadas embutidas)?** Um PDF de scan tem uma ou mais imagens JPEG como conteúdo principal, sem vetores ou texto real. A análise de resolução funciona, mas a conversão RGB→CMYK vai processar uma imagem gigante. Definir limite de tamanho de imagem individual antes de tentar converter.

10. **Logging de dados pessoais:** o nome do arquivo original e os metadados do job podem conter dados pessoais (nome do cliente, número de pedido). Definir política de retenção de logs separada dos dados do job.

---

## 56. Conclusão Executiva

PrintGuard é um produto com fundação técnica sólida, mercado real e claro, e uma abordagem de produto honesta e pragmática.

**Por que este produto faz sentido:**

O mercado de gráficas digitais está crescendo, digitalizado e mal atendido por ferramentas de preflight. As soluções existentes são caras demais, complexas demais ou desktop-only. Há uma lacuna de mercado real para uma API/SaaS de preflight acessível, funcional e com preço proporcional ao volume.

**Por que a arquitetura escolhida é a correta:**

Monólito modular com fila PostgreSQL, storage local com abstração, e concorrência controlada não é uma concessão — é a decisão técnica correta para o estágio atual. É o que permite entregar um produto funcionando em produção real com orçamento mínimo de infraestrutura, sem comprometer a trajetória de crescimento. A abstração nos lugares certos (IStorage, IQueue, IRule, IFixAction) garante que escalar horizontalmente quando o volume justificar será uma evolução, não uma reescrita.

**Por que o foco em "nunca corromper o arquivo" é o diferencial mais importante:**

A confiança de uma gráfica em uma ferramenta automatizada é conquistada lentamente e perdida rapidamente. Um sistema que eventualmente produz um PDF com texto corrompido ou cores totalmente erradas perde a confiança imediatamente, e provavelmente o cliente junto. O conservadorismo deliberado nas correções automáticas do MVP — corrigir apenas o que é seguro, sinalizar o resto com clareza — é a estratégia correta para construir uma base de usuários que confia no produto.

**O que o time precisa fazer agora:**

1. Configurar o repositório e o ambiente de build (CMake + deps)
2. Começar pelo Milestone 1: foundation, parse, análise, relatório
3. Selecionar as 3-5 gráficas piloto antes de lançar o MVP
4. Processar PDFs reais dos pilotos durante o desenvolvimento para refinar regras e relatórios
5. Não tentar implementar tudo de uma vez — a sequência de milestones existe por razão

O produto descrito neste PRD é viável, comercialmente defensável e tecnicamente executável por uma equipe pequena em 90 dias. O que está escrito aqui é a fundação; o trabalho de engenharia, vendas e produto vai construir o restante em cima dela.

---

## Apêndice A — Exemplo de Status Lifecycle Completo

```json
// Timeline de transições de status para um job típico (cartão de visita RGB)
[
  {"status": "uploaded",          "timestamp": "15:00:00.000", "note": "API recebeu o upload"},
  {"status": "queued",            "timestamp": "15:00:00.050", "note": "Worker não tem slot ainda (outro job rodando)"},
  {"status": "parsing",           "timestamp": "15:00:32.100", "note": "Slot liberado, worker pegou o job"},
  {"status": "analyzing",         "timestamp": "15:00:33.200", "note": "Parse concluído em 1.1s"},
  {"status": "planning_fixes",    "timestamp": "15:00:34.500", "note": "Análise concluída, 3 findings"},
  {"status": "fixing",            "timestamp": "15:00:34.600", "note": "Plano montado: 3 fixes"},
  {"status": "revalidating",      "timestamp": "15:00:43.800", "note": "Fixes concluídos em 9.2s"},
  {"status": "rendering_preview", "timestamp": "15:00:44.700", "note": "Revalidação: 1 finding restante (Warning)"},
  {"status": "generating_reports","timestamp": "15:00:52.100", "note": "Preview gerado em 7.4s"},
  {"status": "completed",         "timestamp": "15:00:52.400", "note": "Relatórios gerados, job concluído"}
]
// Tempo total: ~52 segundos — dentro da meta de 60s
```

## Apêndice B — Critérios para `manual_review_required`

Um job entra em `manual_review_required` quando qualquer uma das seguintes condições é verdadeira:

| Condição | Código de Razão | Ação Sugerida ao Operador |
|---|---|---|
| Há finding ErrorBlocking sem fix automático disponível | `BLOCKING_ERROR_NO_FIX` | Contatar cliente com instrução específica |
| Há finding ErrorBlocking cujo fix é classificado como Risky e o validation profile não permite risky fixes | `RISKY_FIX_REQUIRES_APPROVAL` | Operador pode aprovar o fix risky para continuar |
| Um fix foi aplicado mas a revalidação encontrou novo ErrorBlocking | `FIX_INTRODUCED_NEW_ERROR` | Investigar o fix e o documento específico |
| O processamento excedeu o timeout de correção mas fixes parciais foram aplicados | `FIX_TIMEOUT_PARTIAL` | Revisar o que foi feito, decidir se é suficiente |
| A análise de revalidação encontrou que o PDF corrigido tem mais problemas que o original | `REGRESSION_AFTER_FIX` | Investigar qual fix causou regressão |

---

*Documento gerado como base técnica e de produto para o projeto PrintGuard.*  
*Versão 1.0.0 — Abril de 2026*  
*Classificação: Documento de fundação do projeto — para uso interno, equipe fundadora e técnica*
