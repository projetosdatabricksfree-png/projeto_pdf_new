# Skill: Linux Systemd Operations

## Missão
Operar API e worker do PrintGuard com systemd de forma simples, previsível e robusta.

## Quando usar
Use esta skill para:
- deploy em VPS
- serviços do worker e API
- restart policy
- logs
- healthchecks
- boot startup

## Regras obrigatórias
1. API e worker em services separados.
2. Restart policy explícita.
3. Usuário de sistema dedicado quando possível.
4. Diretórios de storage e logs com permissão correta.
5. Não depender de intervenção manual para subir após reboot.

## Checklist técnico
- [ ] service da API criado
- [ ] service do worker criado
- [ ] restart policy definida
- [ ] working directory correto
- [ ] env file definido
- [ ] logs acessíveis
- [ ] boot automático configurado

## Alertas
- Não executar tudo como root.
- Não misturar service e build manual sem padronização.

## Saída esperada
Operação simples e confiável em uma VPS única.
