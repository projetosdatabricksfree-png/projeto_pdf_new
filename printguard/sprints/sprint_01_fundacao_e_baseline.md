> **ENCERRADA** — Sprint migrada para `SPRINSTS_REFATORACAO/`. O trabalho realizado aqui foi incorporado ao novo roadmap do MVP comercial. Data de encerramento: 2026-04-19.

---

# Sprint 01 — Fundação e Baseline

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusão.

## Objetivo
Estabelecer o alicerce técnico do PrintGuard, garantindo um ambiente de desenvolvimento reprodutível com C++20, gestão de dependências moderna e estrutura de pastas que suporte o monólito modular.

## Escopo da Sprint
- Configuração do CMake e Toolchain (GCC 11+ / Clang 14+).
- Definição da estrutura física de pastas do repositório.
- Implementação do sistema de logging estruturado (JSON).
- Criação dos entry-points básicos (API e CLI de Teste).
- Configuração do ambiente de desenvolvimento (Docker Compose para Dev).

## Fora do escopo da Sprint
- Persistência em banco de dados.
- Lógica de domínio PDF.
- Implementação real de worker.

## Dependências
- SO Ubuntu 22.04 ou superior.
- CMake 3.22+, GCC 11+.

## Entregáveis
- [x] Repositório inicializado com estrutura `src/`, `include/`, `tests/`, `scripts/`.
- [x] `CMakeLists.txt` configurado com padrões de segurança e performance.
- [x] Módulo `common/logging` funcional (baseado em spdlog).
- [x] Binário `printguard-api` básico (responde "OK" via HTTP).

## Checklist Técnico

### Build / Toolchain
- [x] Configurar CMake para C++20 como padrão obrigatório.
- [x] Implementar `-Wall -Wextra -Werror` no nível de debug.
- [x] Configurar busca de dependências via `FetchContent` ou `Vcpkg`.

### Common
- [x] Criar logger estruturado emitindo JSON para stdout/files.
- [x] Implementar sistema de constantes globais e tags de versão.

### API
- [x] Integrar `cpp-httplib` ou `Crow` para o servidor HTTP básico.
- [x] Implementar endpoint `/health`.
- [x] Configurar middleware de logs de requisição.

### Testes
- [x] Configurar framework `Catch2` ou `GTest`.
- [x] Criar teste unitário de "Hello World" para validar toolchain.

### Operação
- [x] Criar `Dockerfile` de desenvolvimento.
- [x] Preparar script `scripts/setup.sh` para desenvolvedores.

## Arquivos e módulos impactados
- `CMakeLists.txt`
- `cmake/`
- `src/common/logging/`
- `src/api/`
- `tests/`
- `scripts/`

## Critérios de Aceite
- [x] `cmake .. && make` compila sem warnings.
- [x] Logs seguem o formato `{"timestamp": "...", "level": "INFO", "msg": "..."}`.
- [x] Servidor HTTP responde na porta 8080 com status code 200 no healthcheck.

## Riscos
- Incompatibilidade de versão de compilador no ambiente de dev vs produção.

## Mitigações
- Uso de Docker para padronizar o toolchain desde o dia 1.

## Observações de Implementação
- Não usar bibliotecas pesadas de UI.
- Manter o link estático sempre que possível para simplificar deploy na VPS.

## Definição de pronto
- [x] código implementado
- [x] build configurado
- [x] testes mínimos executados
- [x] critérios de aceite atendidos
- [x] documentação da sprint atualizada

## Status
**Progresso da sprint:** `100%`  
**Situação:** `Concluída`
