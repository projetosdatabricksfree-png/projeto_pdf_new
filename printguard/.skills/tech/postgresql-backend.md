# Skill: PostgreSQL Backend

## Missão
Modelar e operar o PostgreSQL do PrintGuard com foco em simplicidade, consistência transacional e baixo custo operacional.

## Quando usar
Use esta skill para:
- schema
- migrations
- índices
- queries
- repositórios
- status de jobs
- artifacts
- findings
- fixes_applied
- tenants e api_keys

## Regras obrigatórias
1. Modelagem simples e explícita.
2. Integridade referencial sempre que fizer sentido.
3. Índices guiados por acesso real.
4. Não otimizar cedo demais.
5. Status de job sempre persistido de forma transacional.
6. Evitar lógica de negócio complexa em stored procedures no MVP.

## Tabelas principais
- tenants
- api_keys
- jobs
- findings
- fixes_applied
- artifacts

## Checklist técnico
- [ ] migrations criadas
- [ ] chaves primárias consistentes
- [ ] foreign keys corretas
- [ ] índices mínimos aplicados
- [ ] queries críticas revisadas
- [ ] status transitions consistentes
- [ ] retenção pensada
- [ ] isolamento por tenant aplicado

## Alertas
- Não usar JSON onde coluna normal resolve.
- Não esconder regra crítica em trigger obscura.
- Não deixar jobs sem índice por status/updated_at.

## Saída esperada
Banco simples, consistente e operável em VPS pequena.
