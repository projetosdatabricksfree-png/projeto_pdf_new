# Auditoria Sonar por Sprint

## Resumo Geral
- **Data da auditoria consolidada**: 2026-04-19
- **Escopo auditado**: repositório completo acumulado até o estado atual
- **Scanner**: SonarQube local em `http://localhost:9000`
- **Resultado consolidado atual**:
  - `0` bugs
  - `0` vulnerabilidades
  - `0` code smells
  - `0` issues abertas
  - cobertura global importada: `0.9%`
  - quality gate: `ERROR` por `new_coverage = 0.0 < 80`
- **Observação de rastreabilidade**: nesta retomada a auditoria foi reexecutada no código acumulado; as seções por sprint abaixo registram o estado auditado de forma retrospectiva e honesta, sem fingir execuções históricas isoladas quando a evidência não existe neste workspace.

## Sprint 01
- **Data da auditoria**: 2026-04-19
- **Escopo auditado**: repositório completo até a fundação do projeto
- **Principais issues encontradas**:
  - configuração do Sonar ainda sem cobertura importada
  - ruído de includes do host no plugin C++
- **Issues corrigidas**:
  - build limpo com `compile_commands.json`
  - geração de `coverage.xml` com `gcovr`
- **Issues mantidas com justificativa**:
  - cobertura de código insuficiente para satisfazer o quality gate
- **Status final da auditoria**: `Concluída com ressalva de cobertura`

## Sprint 02
- **Data da auditoria**: 2026-04-19
- **Escopo auditado**: repositório completo até banco, storage e upload
- **Principais issues encontradas**:
  - ausência de testes automatizados de integração com PostgreSQL
  - coverage gate em aberto
- **Issues corrigidas**:
  - build/test do repositório estabilizados
  - `ctest` limpo, sem testes herdados de dependências
- **Issues mantidas com justificativa**:
  - falta evidência automática de upload de 50MB e de integração real com DB em teste
- **Status final da auditoria**: `Concluída com pendências operacionais`

## Sprint 03
- **Data da auditoria**: 2026-04-19
- **Escopo auditado**: repositório completo com domínio, presets e profiles
- **Principais issues encontradas**:
  - ausência de contratos formais `IRule` e `IFixAction`
  - validação de config no boot ainda incompleta
- **Issues corrigidas**:
  - `Finding` consolidado no domínio
  - testes de state machine presentes e passando
- **Issues mantidas com justificativa**:
  - pendências são estruturais e não geraram issues Sonar classificadas como bug/vulnerability/code smell
- **Status final da auditoria**: `Concluída com pendências funcionais`

## Sprint 04
- **Data da auditoria**: 2026-04-19
- **Escopo auditado**: repositório completo com `PdfLoader` e modelo canônico
- **Principais issues encontradas**:
  - cobertura muito baixa nas rotas de parsing real
  - ausência de testes automatizados com PDFs corrompidos e protegidos por senha
- **Issues corrigidas**:
  - compatibilidade do loader com a API atual do QPDF
  - leitura de boxes, rotação, metadata e linearização validadas em execução real
- **Issues mantidas com justificativa**:
  - inventário de fontes/imagens e cenários de erro ainda não cobertos
- **Status final da auditoria**: `Concluída com pendências de fixture`

## Sprint 05
- **Data da auditoria**: 2026-04-19
- **Escopo auditado**: repositório completo com worker e claim de jobs
- **Principais issues encontradas**:
  - worker ainda sem controle explícito de concorrência
  - pipeline do worker termina em `ANALYZING`, não no ciclo completo
- **Issues corrigidas**:
  - polling com `FOR UPDATE SKIP LOCKED`
  - sinais `SIGINT` e `SIGTERM` tratados
- **Issues mantidas com justificativa**:
  - falta de `PipelineContext` e hardening operacional ainda é limitação funcional, não finding Sonar
- **Status final da auditoria**: `Concluída com pendências de orquestração`

## Sprint 06
- **Data da auditoria**: 2026-04-19
- **Escopo auditado**: repositório completo com engine de análise MVP
- **Principais issues encontradas**:
  - findings ainda não persistidos em banco
  - cobertura automatizada da engine muito baixa
- **Issues corrigidas**:
  - `RuleEngine` real entregue com geometria, bleed, RGB, DPI, margem e transparência
  - execução em lote real comprovou detecção em 206 PDFs locais
- **Issues mantidas com justificativa**:
  - falta suíte de fixtures automatizadas cobrindo os cenários sujos
- **Status final da auditoria**: `Concluída com pendências de persistência e testes`

## Sprint 07
- **Data da auditoria**: 2026-04-19
- **Escopo auditado**: repositório completo com planner e fix engine MVP
- **Principais issues encontradas**:
  - sem `OutputIntent` e sem conversão ICC completa
  - histórico de fixes não persistido no banco
- **Issues corrigidas**:
  - `NormalizeBoxesFix` implementado
  - conversão conservadora de operadores RGB para CMYK implementada
  - validação estrutural do PDF corrigido via QPDF
- **Issues mantidas com justificativa**:
  - correções restantes dependem de estratégia mais robusta de cor e storage transacional
- **Status final da auditoria**: `Concluída com pendências de MVP avançado`

## Sprint 08
- **Data da auditoria**: 2026-04-19
- **Escopo auditado**: repositório completo com revalidação, preview e relatórios
- **Principais issues encontradas**:
  - preview ainda em PNG/MuPDF, não JPEG/PDFium
  - endpoints de relatório e artefatos não existem na API
- **Issues corrigidas**:
  - revalidação obrigatória implementada
  - delta before/after implementado
  - relatórios técnico, cliente, resumo e consolidado gerados em lote real
- **Issues mantidas com justificativa**:
  - diferenças de formato/integração com API ficaram fora do que foi entregue no lote local
- **Status final da auditoria**: `Concluída com pendências de integração`

## Sprint 09
- **Data da auditoria**: 2026-04-19
- **Escopo auditado**: repositório completo com hardening e go-live parciais
- **Principais issues encontradas**:
  - quality gate falhou por cobertura
  - ainda sem `systemd`, `logrotate`, sweeper e benchmark formal
- **Issues corrigidas**:
  - lote real resiliente executado com `206` arquivos e `0` falhas
  - exceções principais capturadas no worker e CLI
- **Issues mantidas com justificativa**:
  - maturidade operacional de produção ainda não concluída
- **Status final da auditoria**: `Concluída com bloqueio de cobertura e hardening`
