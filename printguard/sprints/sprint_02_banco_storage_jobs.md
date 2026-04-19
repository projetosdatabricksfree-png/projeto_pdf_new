> **ENCERRADA** — Sprint migrada para `SPRINSTS_REFATORACAO/`. O trabalho realizado aqui foi incorporado ao novo roadmap do MVP comercial. Data de encerramento: 2026-04-19.

---

# Sprint 02 — Banco, Storage e Lifecycle de Jobs

> Atualize manualmente cada item de `- [ ]` para `- [x]` conforme a conclusão.

## Objetivo
Implementar a camada de persistência e armazenamento de arquivos, definindo como os jobs são registrados e como os artefatos (PDFs) são gerenciados no sistema.

## Escopo da Sprint
- Integração com PostgreSQL via `libpqxx`.
- Schema inicial de banco de dados (Jobs, Artifacts).
- Abstração de IStorage (Filesystem local como primeira implementação).
- Gestão de UUIDs para jobs e nomes de arquivos.
- Implementação do lifecycle de status inicial.

## Fora do escopo da Sprint
- Fila de processamento ativa.
- Lógica de preflight.
- Relatórios JSON complexos.

## Dependências
- Sprint 01 concluída.
- PostgreSQL 15 instalado localmente.

## Entregáveis
- [x] Schema SQL versionado (migrations).
- [x] Classe `JobRepository` com CRUD básico.
- [x] Classe `LocalStorage` com operações `put`, `get`, `delete`.
- [x] Endpoint de upload funcional salvando arquivo em disco e registro no banco.

## Checklist Técnico

### Common
- [x] Criar utilitário de manipulação de Filesystem (criação de diretórios, checagem de espaço).
- [x] Implementar utilitários de Hash (SHA256).

### Persistence
- [x] Configurar pool de conexões com PostgreSQL.
- [x] Criar tabela `tenants`.
- [x] Criar tabela `jobs` (id, tenant_id, status, created_at, updated_at).
- [x] Criar tabela `artifacts` (id, job_id, type, path, size, hash).

### Storage
- [x] Definir estrutura de pastas: `storage/{tenant_id}/{job_id}/original/`.
- [x] Implementar limpeza atômica em caso de falha no upload.

### API
- [x] Implementar `POST /v1/jobs` com suporte a multipart/form-data.
- [x] Validar tipo de arquivo (magic bytes para PDF).
- [x] Persistir metadados básicos do upload.

### Testes
- [ ] Testes de integração para banco de dados (salvar/recuperar job).
- [ ] Testes de unidade para IStorage.

### Operação
- [ ] Configurar volume de storage no Docker Compose.
- [ ] Documentar vars de ambiente de conexão ao DB.

## Arquivos e módulos impactados
- `src/persistence/`
- `src/storage/`
- `src/api/controllers/JobController.cpp`
- `include/printguard/storage/`

## Critérios de Aceite
- [ ] O sistema permite upload de um arquivo de 50MB sem crash.
- [x] Registro no banco é criado com status `uploaded`.
- [x] Arquivo é salvo no path correto e o hash SHA256 coincide.

## Riscos
- Vazamento de conexões com o banco de dados.
- Storage encher com arquivos de teste.

## Mitigações
- Uso de RAII para conexões SQL.
- Implementação imediata de um comando CLI de limpeza manual (`purge-storage`).

## Observações de Implementação
- Respeitar estritamente a arquitetura monolítica: o DB roda na mesma VPS.
- Não usar ORM pesado; preferir SQL puro via `libpqxx` para performance na CPU limitada.

## Definição de pronto
- [x] código implementado
- [x] build configurado com libpqxx e OpenSSL
- [ ] testes de integração executados
- [ ] critérios de aceite atendidos
- [x] documentação da sprint atualizada

## Status
**Progresso da sprint:** `75%`  
**Situação:** `Em andamento`
