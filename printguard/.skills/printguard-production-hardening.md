# Skill: PrintGuard Production Hardening

## Missão
Levar o PrintGuard do “funciona na máquina” para “aguenta piloto real” sem quebrar simplicidade operacional.

## Escopo
- API key
- healthcheck
- log rotation
- cleanup
- retenção
- restart controlado
- recovery de job
- limites operacionais
- deploy simples

## Quando usar
Use esta skill para:
- Sprint de hardening
- preparação de piloto
- revisão de readiness de produção

## Regras obrigatórias
1. Segurança mínima antes de piloto.
2. Logs estruturados obrigatórios.
3. Retenção de artefatos obrigatória.
4. Recovery de job interrompido obrigatório.
5. Limites operacionais explícitos.
6. Deploy simples e operável por equipe pequena.

## Checklist técnico
- [ ] autenticação por API key
- [ ] tenant isolation básico
- [ ] `/health` implementado
- [ ] logs JSON funcionando
- [ ] rotação de logs definida
- [ ] cleanup de storage implementado
- [ ] retenção implementada
- [ ] restart via systemd ou compose definido
- [ ] recovery de jobs órfãos implementado
- [ ] limites de upload e job aplicados
- [ ] checklist de go-live revisado

## Saída esperada
- sistema pronto para piloto controlado
- operação simples
- riscos conhecidos documentados
