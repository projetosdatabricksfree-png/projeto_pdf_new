# Skill: PrintGuard Architecture Guard

## Missão
Garantir que qualquer alteração no projeto PrintGuard respeite a arquitetura oficial do MVP.

## Deve proteger
- monólito modular
- API + worker em processos separados, mesma base
- PostgreSQL como fila no MVP
- filesystem local no MVP
- sem RabbitMQ no MVP
- sem microsserviços
- sem Kubernetes
- sem GPU
- fixes seguros primeiro
- revalidação obrigatória
- preview leve, preferencialmente só da primeira página
- operação em VPS 2 vCPU / 8 GB RAM / 100 GB NVMe

## Quando usar
Use esta skill sempre que:
- uma nova feature for proposta
- uma sprint for executada
- um refactor importante for iniciado
- houver dúvida entre simplicidade e sofisticação arquitetural

## Regras obrigatórias
1. Não permitir abstração prematura.
2. Não aceitar componentes distribuídos sem necessidade objetiva.
3. Não aceitar novas dependências pesadas sem justificativa clara.
4. Não aceitar feature que aumente custo operacional do MVP sem ganho direto.
5. Não aceitar correção automática visualmente arriscada no MVP.
6. Não aceitar qualquer fluxo de fix sem revalidação posterior.
7. Não aceitar sobrescrita do PDF original.

## Checklist de validação
- [ ] continua sendo monólito modular
- [ ] continua compatível com VPS pequena
- [ ] não adiciona serviço externo desnecessário
- [ ] não aumenta complexidade operacional sem motivo
- [ ] não fere segurança do pipeline de PDF
- [ ] mantém original intacto
- [ ] mantém revalidação obrigatória

## Saída esperada
Responder com:
- impacto arquitetural
- riscos
- violações detectadas
- recomendação objetiva: aprovar, ajustar ou bloquear
