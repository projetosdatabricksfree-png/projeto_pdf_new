# Skill: nlohmann/json Contracts

## Missão
Usar `nlohmann::json` de forma disciplinada para contratos, config, reports e payloads internos.

## Quando usar
Use esta skill em:
- presets
- validation profiles
- relatórios
- payloads de API
- serialização de findings e artifacts

## Regras obrigatórias
1. Contratos devem ser estáveis.
2. Validar campos obrigatórios.
3. Não confiar cegamente em JSON externo.
4. Distinguir claramente config interna de payload público.
5. Usar conversão explícita quando necessário.

## Checklist técnico
- [ ] schema mental ou validação mínima aplicada
- [ ] campos obrigatórios verificados
- [ ] valores default definidos com cuidado
- [ ] erros de parse tratados
- [ ] serialização consistente
- [ ] backward compatibility considerada quando aplicável

## Alertas
- Não usar JSON como desculpa para ausência de modelo.
- Não enfiar tudo em campo livre se estrutura forte resolve.

## Saída esperada
JSON confiável, previsível e compatível com evolução do projeto.
