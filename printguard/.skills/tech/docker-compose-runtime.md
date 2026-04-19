# Skill: Docker Compose Runtime

## Missão
Usar Docker Compose como conveniência de desenvolvimento e/ou deploy simples, sem transformar o MVP em uma mini-plataforma de orquestração.

## Quando usar
Use esta skill para:
- ambiente local
- empacotamento opcional da stack
- API + worker + PostgreSQL em compose
- scripts de subida rápida

## Regras obrigatórias
1. Compose deve simplificar, não complicar.
2. Não simular cluster.
3. Volumes persistentes claros.
4. Healthchecks básicos.
5. Limites e envs explícitos.

## Checklist técnico
- [ ] compose define postgres
- [ ] compose define api
- [ ] compose define worker
- [ ] volumes persistentes configurados
- [ ] envs configuradas
- [ ] healthcheck básico configurado

## Alertas
- Não esconder problema de produção atrás de compose “mágico”.
- Não depender exclusivamente de Docker se systemd puro for o caminho real.

## Saída esperada
Ambiente previsível para dev e deploy simples.
