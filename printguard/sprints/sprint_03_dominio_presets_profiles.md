> **ENCERRADA** — Sprint migrada para `SPRINSTS_REFATORACAO/`. O trabalho realizado aqui foi incorporado ao novo roadmap do MVP comercial. Data de encerramento: 2026-04-19.

---

# Sprint 03 — Domínio, Presets, Profiles e Estados

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusão.

## Objetivo
Definir a inteligência de configuração do sistema, mapeando as regras de preflight (nomes, severidades, parâmetros) e as máquinas de estado que regem o processamento dos jobs.

## Escopo da Sprint
- Definição do Modelo de Domínio C++ (Classes base).
- Sistema de Presets (Configurações físicas por tipo de produto).
- Sistema de Validation Profiles (Níveis de rigor: standard, lenient, etc).
- Implementação da Máquina de Estados do Job (uploaded -> queued -> analyzed -> ... -> completed).
- Carregamento de configurações via JSON/YAML.

## Fora do escopo da Sprint
- Execução real de análise de PDF.
- Correção de arquivos.

## Dependências
- Sprints 01 e 02 concluídas.
- Biblioteca `nlohmann-json` integrada.

## Entregáveis
- [x] Catálogo de Presets iniciais (cartão de visita, flyer, etc).
- [x] Validation Profiles iniciais em arquivo (`config/profiles/`).
- [x] Implementação de `JobStateMachine`.
- [x] Módulo `domain/config_loader` funcional.

## Checklist Técnico

### Domain
- [x] Criar classe `Preset` (width, height, bleed_required, min_dpi).
- [x] Criar classe `ValidationProfile` (ativar/desativar regras de cor, geometria, etc).
- [x] Definir Enums de Status de Job (QUEUED, PARSING, ANALYZING, FIXING, COMPLETED, FAILED).
- [x] Implementar classe `Finding` (code, severity, message, page, evidence).

### Persistence
- [x] Atualizar tabela `jobs` para suportar `preset_id` e `profile_id`.
- [x] Adicionar timestamps para cada mudança de estado (para benchmark futuro).

### API
- [x] Endpoint `GET /v1/presets` para listar opções para o frontend.
- [x] Validar se o preset e profile fornecidos no upload existem.

### PDF
- [ ] Definir a interface `IRule` e `IFixAction` (contratos de código).

### Testes
- [x] Testes de transição de estado da `JobStateMachine`.
- [ ] Validar integridade dos arquivos JSON de configuração no boot do sistema.

### Operação
- [x] Definir local padrão de configs: `/etc/printguard/configs/` ou `config/` no repositório.

## Arquivos e módulos impactados
- `src/domain/`
- `include/printguard/domain/`
- `config/presets/`
- `config/profiles/`

## Critérios de Aceite
- [x] O sistema carrega presets do disco no startup e os disponibiliza via API.
- [x] Transições de estado inválidas no Job (ex: `uploaded` -> `completed` direto) são impedidas ou logadas como erro.
- [x] Um finding gerado possui severidade clara (INFO, WARNING, ERROR).

## Riscos
- Excesso de abstração no modelo de regras que prejudique a performance da CPU.
- Acoplamento entre configuração e motor de PDF.

## Mitigações
- Manter o domínio puro: classes de configuração não devem instanciar nada de PDF diretamente.

## Observações de Implementação
- Os presets devem refletir o PRD: `business_card`, `flyer_a5`, `invitation_10x15`, `sticker_square`, `poster_a3`.
- Usar nomes de constantes amigáveis em vez de IDs mágicos.

## Definição de pronto
- [x] código implementado
- [x] build funcionando
- [x] testes unitários de domínio concluídos
- [ ] critérios de aceite atendidos
- [x] documentação da sprint atualizada

## Status
**Progresso da sprint:** `85%`  
**Situação:** `Em andamento`
