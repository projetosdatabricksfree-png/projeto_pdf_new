# Post-MVP Backlog — Graphic-Pro (PreFlight Inspector)

Items intentionally deferred from the 4-sprint MVP. Each entry includes: ID, title, rationale for deferral, RICE priority score, estimated effort, target version, dependencies, technical implementation notes, and Definition of Done.

> **Baseline de referência**: Sprint QA concluída. Remediadores ativos: `ColorSpaceRemediator`, `FontRemediator`, `ResolutionRemediator`. Pipeline Celery + Redis estável com 6 replicas de worker. Os Sprints A, B e C (Auto-Remediação) são **pré-requisito** para os itens v1.1 e v1.2 listados aqui.

---

## Legenda de Esforço

| Sigla | Estimativa |
|:---:|:---|
| **S** | ≤ 1 dia de engenharia |
| **M** | 2–4 dias |
| **L** | 1–2 semanas |
| **XL** | > 2 semanas + pesquisa ativa |

## Legenda de RICE

`RICE = (Reach × Impact × Confidence) / Effort`
- **Reach**: Percentual estimado de jobs de produção afetados.
- **Impact**: 1 (baixo) → 3 (alto).
- **Confidence**: % de certeza técnica da estimativa.
- **Effort**: dias de engenharia.

---

## v1.1 — Hardening & Observabilidade

> **Critério de entrada para v1.1**: Sprints A, B e C integrados e batch de 10 PDFs passando a 10/10 no ambiente staging.

---

### `FO-05` — Rich Black ratio por variante (§4.15 GWG)

| Atributo | Valor |
|:---|:---|
| **Área** | Fontes / Tipografia |
| **Esforço** | M |
| **RICE** | Reach 35% · Impact 2 · Confidence 80% / 3d → **~19** |
| **Target** | v1.1 |
| **Depende de** | FO-04 (per-variant text-quality, já no MVP) |

**Razão do deferimento**: FO-04 implementa a inspeção de qualidade textual por variante, mas não tabula a proporção de Rich Black (K=100, CMY > 0) por composição de tinta. Juntar os dois em um único release de "text-quality atômica" evita dois ciclos de QA sobre o mesmo subsistema.

**Notas de implementação**:
- Adicionar verificação no `agentes/operarios/` relevante (papelaria plana, editoriais) que lê o dicionário de cor de cada glyph path via PyMuPDF `page.get_drawings()`.
- Para cada objeto com `color` CMYK onde C+M+Y > 0 e K == 1.0, incrementar contador `rich_black_count`.
- Comparar `rich_black_count / total_text_objects` contra threshold por variante (definido na `messages_table.py` — nunca hardcode em lógica de negócio).
- Emitir `W_RICH_BLACK_RATIO` se acima do limite.
- **Rule 2 (Anti-RAG)**: mensagem gerada a partir de `messages_table.py`, sem LLM.

**DoD**:
- [ ] Verificação ativada para variantes `papelaria_plana` e `editoriais`.
- [ ] `W_RICH_BLACK_RATIO` mapeado em `messages_table.py` (pt-BR, en-US, es-ES).
- [ ] Teste unitário com PDF sintético contendo ≥ 30% Rich Black em corpo de texto.
- [ ] Lint `ruff` sem violações.

---

### `GE-01-FULL` — UserUnit ausente em **todos** os dicionários de página (herança PageTree)

| Atributo | Valor |
|:---|:---|
| **Área** | Geometria |
| **Esforço** | S |
| **RICE** | Reach 8% · Impact 2 · Confidence 90% / 1d → **~14** |
| **Target** | v1.1 |
| **Depende de** | GE-01 (partial — MVP) |

**Razão do deferimento**: A implementação parcial do MVP verifica `UserUnit` apenas no dicionário da página diretamente. O caso de herança via PageTree (onde `UserUnit` está no nó pai e herdado pelos filhos) é raro e edge-case em PDFs gerados por software moderno, mas ocorre em arquivos exportados por software legado de CAD.

**Notas de implementação**:
- No `agentes/operarios/operario_projetos_cad/agent.py` (e/ou no validador), ao iterar páginas via PyMuPDF `doc[i].xref`, subir a árvore de `Parent` refs até a raiz, acumulando `UserUnit` pelo primeiro nó que o define.
- Não carregar o documento inteiro em memória — usar `doc.xref_get_key(xref, "UserUnit")` por referência cruzada.
- **Rule 1 (Anti-OOM)**: processar via iteração lazy, não `doc.tobytes()`.

**DoD**:
- [ ] Função `_resolve_user_unit(doc, page_index)` com traversal de PageTree.
- [ ] Teste com PDF de 3 níveis de herança PageTree.
- [ ] Nenhuma regressão em testes existentes de geometria.

---

### `CO-04-FULL` — Transparency Blend CS em Form XObjects aninhados dentro de Patterns

| Atributo | Valor |
|:---|:---|
| **Área** | Cor / Transparência |
| **Esforço** | M |
| **RICE** | Reach 5% · Impact 2 · Confidence 70% / 3d → **~2** |
| **Target** | v1.1 |
| **Depende de** | TR-01, TR-02 (MVP — detecção de transparência em nível de página) |

**Razão do deferimento**: TR-01/TR-02 cobrem transparência em nível de página e Form XObjects diretos. O caso de Form XObjects aninhados *dentro de Tiling Patterns* (`/Pattern` → `/XObject` → `/Group`) é subconjunto muito pequeno do universo real de jobs (brochuras de luxo com padrões decorativos).

**Notas de implementação**:
- Estender o scanner de transparência existente para recursão em recursos do tipo `/Pattern`.
- Limitar profundidade de recursão a 5 níveis para prevenir loops em PDFs malformados.
- Adicionar métrica `blend_group_depth_max` em `TechnicalReport` para rastreabilidade.
- Cuidado com possível OOM: limitar `page.get_xobjects()` a scan de referências, não carregamento de imagem.

**DoD**:
- [ ] Scanner recursivo com `max_depth=5`.
- [ ] PDF de teste com Pattern → Form XObject → Transparency Group.
- [ ] `blend_group_depth_max` exposto no `TechnicalReport`.
- [ ] Tempo de processamento ≤ 500ms para PDF de 50 páginas no P95 (benchmark documentado).

---

### `TAC-HEATMAP` — Exportação de heatmap TAC por página (overlay PNG)

| Atributo | Valor |
|:---|:---|
| **Área** | UX / Observabilidade |
| **Esforço** | M |
| **RICE** | Reach 20% · Impact 2 · Confidence 85% / 3d → **~11** |
| **Target** | v1.1 |
| **Depende de** | TAC atual (pyvips, MVP) |

**Razão do deferimento**: Feature de QA/revisão visual, não um gate de conformidade. Agrega valor a operadores de pré-impressão que precisam identificar visualmente áreas de excesso de tinta, mas não bloqueia a entrega do `_gold.pdf`.

**Notas de implementação**:
- Após `pyvips` calcular o TAC por tile, converter o grid de tiles em uma imagem de calor usando colormap (0–300% → verde, 300–320% → amarelo, > 320% → vermelho).
- Salvar como `{job_id}_tac_heatmap_p{n}.png` em storage temporário.
- Expor via `GET /api/v1/jobs/{id}/heatmap/{page}` retornando `Content-Type: image/png`.
- **Rule 1 (Anti-OOM)**: gerar heatmap por página sob demanda (lazy), nunca para todas as páginas na memória.

**DoD**:
- [ ] Endpoint `/heatmap/{page}` implementado e documentado no OpenAPI.
- [ ] Heatmap gerado sem carregar mais de uma página rasterizada por vez.
- [ ] Frontend exibe overlay no `ProgressTracker` (componente de visualização, conforme Rule 7).
- [ ] Teste de carga: 10 requisições simultâneas de heatmap sem OOM.

---

### `AUDIT-LOG` — Log estruturado de cada lookup de threshold por job

| Atributo | Valor |
|:---|:---|
| **Área** | Observabilidade / Compliance |
| **Esforço** | M |
| **RICE** | Reach 100% · Impact 1 · Confidence 95% / 3d → **~32** |
| **Target** | v1.1 |
| **Depende de** | Logger atual (MVP) |

**Razão do deferimento**: Os eventos do `progress_bus` cobrem observabilidade de progresso, mas não rastreiam *qual regra específica da tabela GWG foi consultada* e *qual valor foi comparado*. Isso é necessário para auditorias de conformidade e debugging de casos-limite.

**Notas de implementação**:
- Adicionar campo `rule_audit_trail: list[RuleAuditEntry]` ao schema `FinalReport` em `app/api/schemas.py`.
- `RuleAuditEntry`: `{ rule_id: str, variant: str, measured_value: float | str, threshold_value: float | str, outcome: Literal["pass","fail","warn"], message_code: str }`.
- O `agentes/validador/agent.py` deve preencher essa lista a cada consulta à `messages_table`.
- Persistir em coluna JSON no banco via SQLAlchemy (compatível com SQLite e Postgres).
- **Rule 2 (Anti-RAG)**: os valores vêm exclusivamente de `messages_table.py`, nunca gerados.

**DoD**:
- [ ] `RuleAuditEntry` schema definido e validado com Pydantic.
- [ ] Campo `rule_audit_trail` persistido no banco para 100% dos jobs.
- [ ] Endpoint `GET /api/v1/jobs/{id}` retorna `rule_audit_trail` no payload.
- [ ] Teste: job com 3 regras consultadas → trail com 3 entradas corretas.

---

### `UX-AMBIGUOUS` — Fluxo de recuperação `W_VARIANT_AMBIGUOUS` no frontend

| Atributo | Valor |
|:---|:---|
| **Área** | UX / Frontend |
| **Esforço** | M |
| **RICE** | Reach 12% · Impact 3 · Confidence 80% / 3d → **~10** |
| **Target** | v1.1 |
| **Depende de** | Backend emite `W_VARIANT_AMBIGUOUS` (MVP) |

**Razão do deferimento**: O backend já emite o warning quando o Gerente retorna confiança < 85% e o Especialista não converge. A interação de confirmação do usuário no frontend foi explicitamente descartada do MVP para não bloquear entrega.

**Notas de implementação**:
- No `ProgressTracker` (frontend), interceptar `status === "AWAITING_VARIANT_CONFIRMATION"` (novo status terminal intermediário a adicionar no backend).
- Exibir modal com lista dos 2-3 candidatos de variante ordenados por confiança, com descrição textual de cada tipo gráfico.
- Submissão do usuário faz `POST /api/v1/jobs/{id}/confirm-variant` com `{ variant: string }`.
- Backend retoma o pipeline a partir do operário correto via `task_receive_routing_decision` (reutiliza Rule 3 — nunca chama operário direto do endpoint).
- Timeout de 30 minutos: job sem confirmação volta para `QUEUED` com note.

**DoD**:
- [ ] Status intermediário `AWAITING_VARIANT_CONFIRMATION` no DB e exposto via polling.
- [ ] Modal de confirmação implementado com lista de candidatos e % de confiança.
- [ ] Endpoint `POST /confirm-variant` implementado com retomada via fila (não chamada direta).
- [ ] Timeout: job confirmado após 30min → `QUEUED` com `retry_reason` preenchido.
- [ ] Teste E2E: upload de PDF ambíguo → modal aparece → usuário confirma → job conclui.

---

### `SP-05` — DeviceN com > 1 colorante não-processo (Ghent 14.x — embalagens)

| Atributo | Valor |
|:---|:---|
| **Área** | Cor / Espaços de Cor |
| **Esforço** | M |
| **RICE** | Reach 4% · Impact 2 · Confidence 75% / 3d → **~2** |
| **Target** | v1.1 |
| **Depende de** | SP-02 (validação UTF-8 de colorantes, MVP) |

**Razão do deferimento**: Afeta exclusivamente jobs de embalagem flexível com tintas especiais (verniz, pantone NChannel), fora do escopo dos 14 tipos GWG2015 do MVP. A base de clientes de embalagem é pós-MVP.

**Notas de implementação**:
- Em `agentes/operarios/operario_cortes_especiais/agent.py`, após validação SP-02, iterar `page.get_colorspace()` e verificar `cs.name == "DeviceN"` com `cs.n > 1`.
- Separar colorantes processo (C, M, Y, K) dos não-processo via atributo `/Colorants` no dict do espaço de cor.
- Emitir `W_DEVICEN_MULTI_SPOT` se mais de 1 colorante não-processo detectado sem alternateSpace CMYK definido.
- Ghent 14.x exige AlternateSpace DeviceCMYK — verificar presença do mapping.

**DoD**:
- [ ] Detecta e conta colorantes não-processo em DeviceN.
- [ ] `W_DEVICEN_MULTI_SPOT` em `messages_table.py` com localização pt-BR/en-US/es-ES.
- [ ] Teste com PDF de embalagem com Pantone + spot color customizado.
- [ ] Ativo apenas para variante `cortes_especiais` (sem regressão em papelaria/editoriais).

---

## v1.2 — Escala & Personalização

> **Critério de entrada para v1.2**: v1.1 estável em produção por ≥ 4 semanas sem incidentes críticos de OOM ou deadlock.

---

### `OV-09-MASK` — Overprint de ImageMask CMYK com chroma-keyed alternates

| Atributo | Valor |
|:---|:---|
| **Área** | Cor / Overprint |
| **Esforço** | M |
| **RICE** | Reach 3% · Impact 2 · Confidence 65% / 3d → **~1** |
| **Target** | v1.2 |
| **Depende de** | OV-01..OV-08 (overprint básico, MVP) |

**Razão do deferimento**: Traversal profundo do grafo de máscaras (ImageMask → AlternateMask → SMask encadeados) é raro em PDFs de publicidade. O custo de implementação é desproporcional ao reach atual.

**Notas de implementação**:
- Implementar `_resolve_mask_chain(xobj)` com limite de profundidade 4 para evitar loops.
- Para cada imagem do tipo `ImageMask`, verificar `CS == DeviceCMYK` e presença de `/Alternates` array com entrada chroma-keyed.
- Integrar ao `ColorSpaceRemediator` existente: se overprint ativo + ImageMask + CMYK + chroma-key → emitir `W_IMAGEMASK_OVERPRINT_CHROMA`.
- **Rule 1**: nunca deserializar bytes da imagem; analisar apenas metadados do stream via PyMuPDF `xref_get_key`.

**DoD**:
- [ ] `_resolve_mask_chain` com `max_depth=4` e proteção contra ciclos (set de xrefs visitados).
- [ ] `W_IMAGEMASK_OVERPRINT_CHROMA` em `messages_table.py`.
- [ ] Benchmark: análise de PDF com 200 imagens em ≤ 2s.

---

### `ML-COLORANT-NORM` — Normalização NFKC de nomes de colorantes não-ASCII

| Atributo | Valor |
|:---|:---|
| **Área** | Cor / Internacionalização |
| **Esforço** | M |
| **RICE** | Reach 6% · Impact 1 · Confidence 85% / 3d → **~2** |
| **Target** | v1.2 |
| **Depende de** | SP-02 (UTF-8 validity, MVP) |

**Razão do deferimento**: Gráficas multilíngues (Oriente Médio, Ásia) são pós-MVP. A validação de UTF-8 do SP-02 já captura strings inválidas; a normalização canônica é refinamento sobre isso.

**Notas de implementação**:
- Após SP-02 confirmar UTF-8 válido, aplicar `unicodedata.normalize("NFKC", name)` em cada nome de colorante.
- Comparar o nome normalizado com o nome original — se diferente, registrar em `quality_loss_warnings` com `original` e `normalized`.
- Garantir que o nome normalizado seja usado nas comparações subsequentes (SP-02, SP-05).
- Sem bloqueio: normalização é sempre aplicada silenciosamente, nunca rejeita o job.

**DoD**:
- [ ] Normalização aplicada antes de qualquer comparação de nome em SP-02 e SP-05.
- [ ] Teste com colorante em árabe, japonês e grego — verificar idempotência.
- [ ] `quality_loss_warnings` contém entrada se o nome mudou na normalização.

---

### `TAC-STREAMING-LARGE` — TAC tile-based para posters > A2 @ 300dpi

| Atributo | Valor |
|:---|:---|
| **Área** | Performance / Anti-OOM |
| **Esforço** | L |
| **RICE** | Reach 10% · Impact 3 · Confidence 80% / 8d → **~3** |
| **Target** | v1.2 |
| **Depende de** | TAC atual (pyvips, MVP) |

**Razão do deferimento**: O MVP cobre até A2 @ 300dpi (~86 megapixels rasterizados). Formatos acima disso (A0, B1, grandes formatos para plotagem) requerem estratégia de tiling diferente — o pyvips atual processaria via sequential mas o pico de RAM pode exceder 4g em certos layouts de canal.

**Notas de implementação**:
- Detectar tamanho efetivo em pixels: `(width_pt / 72) * dpi × (height_pt / 72) * dpi`.
- Se > 100M pixels: ativar modo tile com tile size de 4096×4096 px.
- Usar `pyvips.Image.tiffload_stream()` com `access=VIPS_ACCESS_SEQUENTIAL` para garantir que nunca mais de 2 tiles estejam em RAM simultaneamente.
- Agregar TAC por tile → calcular percentil 95 (não média simples) para capturar picos.
- **Rule 1 (Anti-OOM)**: worker configurado com `mem_limit: 4g`; esta implementação deve manter uso de pico < 2g para deixar headroom.
- Adicionar teste de carga com PDF A0 sintético gerado via Ghostscript.

**DoD**:
- [ ] Threshold de ativação de tiling configurável via env var `TAC_TILE_THRESHOLD_MPIX` (default: 100).
- [ ] Pico de RAM medido ≤ 2g em PDF A0 no benchmark de stress test.
- [ ] Resultado de TAC tileado vs. processamento completo difere ≤ 2% (validação de acurácia).
- [ ] Teste de regressão: PDFs ≤ A2 continuam usando o caminho atual sem overhead.

---

### `VARIANTS-CUSTOM` — Variantes definidas por usuário via UI de administração

| Atributo | Valor |
|:---|:---|
| **Área** | Produto / Configurabilidade |
| **Esforço** | L |
| **RICE** | Reach 15% · Impact 3 · Confidence 70% / 8d → **~4** |
| **Target** | v1.2 |
| **Depende de** | Sistema de autenticação (pós-MVP), banco de dados de variantes |

**Razão do deferimento**: Requer camada de persistência de configuração separada da `messages_table.py` atual (que é código-fonte, não DB), além de UI administrativa e sistema de autenticação.

**Notas de implementação**:
- Nova tabela `variant_definitions` no DB: `{ id, shop_id, name, base_variant, threshold_overrides: JSON, created_at }`.
- O Gerente e os Operários devem consultar `variant_definitions` por `shop_id` (extraído do JWT) antes de usar defaults da `messages_table`.
- **Rule 2 (Anti-RAG)**: as mensagens continuam vindo de `messages_table.py`; o usuário só sobrescreve *thresholds numéricos*, nunca texto de mensagem.
- Migration Alembic necessária.
- UI: página `/admin/variants` no frontend (React) com formulário de CRUD.

**DoD**:
- [ ] CRUD via `POST/PUT/DELETE /api/v1/admin/variants` com autenticação.
- [ ] Gerente consulta `variant_definitions` por shop antes do fallback global.
- [ ] Migração Alembic reversível (`upgrade`/`downgrade`).
- [ ] Testes: variante customizada sobrescreve threshold → job usa novo valor.
- [ ] UI administrável sem acesso ao código-fonte.

---

## v2.0 — Expansão de Escopo Técnico

> **Critério de entrada para v2.0**: Produto consolidado com ≥ 6 meses de dados de produção. Decisão de escopo revisada com stakeholders.

---

### `OPI-DEVICEN` — Suporte a referências OPI e detecção de imagem como NChannel

| Atributo | Valor |
|:---|:---|
| **Área** | Cor / Workflows Especializados |
| **Esforço** | L |
| **RICE** | Reach 2% · Impact 2 · Confidence 60% / 8d → **~0.3** |
| **Target** | v2.0 |
| **Depende de** | SP-05 (DeviceN multi-spot, v1.1) |

**Razão do deferimento**: Workflows OPI (Open Prepress Interface) são exclusivos de gráficas com fluxos de pré-impressão legados de alto volume (offset de publicações). Fora do escopo GWG2015 press-job.

**Notas de implementação**:
- Detectar chave `/OPI` em dicionários de XObject de imagem via `xref_get_key`.
- Para referências OPI 1.3 e 2.0, extrair `ImageFileName` e emitir aviso sobre substituição pendente.
- NChannel: detectar `cs.name == "DeviceN"` com `cs.n >= 4` e mapping de canais não-padrão.
- Roadmap: integrar com servidor OPI externo (API externa — fora do escopo v2.0 inicial; apenas detecção).

**DoD**:
- [ ] Detecção de referências OPI 1.3 e 2.0 sem carregamento de imagem substituta.
- [ ] `W_OPI_REFERENCE_DETECTED` e `W_NCHANNEL_IMAGE` em `messages_table.py`.
- [ ] Sem impacto de performance em PDFs sem OPI (check de presença de chave é O(1)).

---

### `FO-03-CFF` — Validação de programa charstring CFF em OpenType embutido

| Atributo | Valor |
|:---|:---|
| **Área** | Fontes |
| **Esforço** | XL |
| **RICE** | Reach 5% · Impact 2 · Confidence 55% / 15d → **~0.4** |
| **Target** | v2.0 |
| **Depende de** | FO-01, FO-02 (presença e embedding de fontes, MVP) |

**Razão do deferimento**: Vai além da verificação de presença/embedding. Requer integração com `fontTools` (biblioteca Python de parsing de fontes) para analisar a corretude do programa charstring CFF — operação custosa e com risco de falsos positivos em fontes legítimas não-conformes mas funcionais.

**Notas de implementação**:
- Usar `fontTools.ttLib.TTFont` para abrir a fonte embutida do stream.
- Acessar tabela `CFF ` e iterar `TopDictIndex` para verificar charstrings.
- Validar que cada charstring termina com `endchar` e não contém operadores inválidos.
- Isolar em subprocess com timeout de 5s por fonte para prevenir hang em fontes corrompidas.
- **Rule 1**: não carregar todos os glyphs em memória — validar apenas o índice e amostrar 20 charstrings aleatórios.
- Considerar cache de resultado por hash SHA-256 da fonte (mesma fonte aparece em múltiplas páginas).

**DoD**:
- [ ] Integração com `fontTools` via subprocess isolado com timeout.
- [ ] Cache de resultado por SHA-256 da fonte embutida.
- [ ] Falsa-positivos validados: suite de 50 fontes comerciais conhecidas deve ter 0 falsos positivos.
- [ ] Overhead de tempo: ≤ 3s por fonte em P95 no batch de produção.
- [ ] `E_CFF_CHARSTRING_INVALID` em `messages_table.py`.

---

## Backlog de Risco — Monitorar, Não Planejar

Itens que podem surgir dependendo de evidência de produção. Não priorizar sem dados reais.

| ID | Título | Trigger de Priorização |
|:---|:---|:---|
| `PERF-01` | Cache Redis de resultados de validação por hash do PDF | P95 de tempo de processamento > 30s para PDFs idênticos repetidos |
| `SEC-01` | Rate limiting por `shop_id` no endpoint de upload | Evidência de abuso ou stress de um único tenant |
| `OBS-01` | Dashboard Grafana de métricas por variante | Time de operações pede visibilidade de SLA por tipo de produto |
| `DB-01` | Migração SQLite → PostgreSQL para multi-tenant | Volume de jobs > 10k/dia ou necessidade de multi-instância da API |

---

## Restrições Transversais (aplicáveis a todos os itens acima)

Qualquer item implementado neste backlog deve respeitar:

1. **Rule 1 (Anti-OOM)**: Nenhum carregamento de arquivo inteiro em RAM. Qualquer operação que cresce linearmente com o tamanho do PDF deve usar streaming ou mmap.
2. **Rule 2 (Anti-RAG)**: Mensagens de validação sempre originadas em `messages_table.py`. Proibido gerar texto de resultado dinamicamente ou via LLM.
3. **Rule 3 (Deadlock)**: Qualquer novo agente que precise acionar outro agente downstream deve publicar em fila intermediária — nunca chamada direta entre pools.
4. **Rule 4 (Idempotência)**: Qualquer novo stage de processamento deve ser seguro para retry sem efeitos colaterais (sobrescrita idempotente de arquivos gerados, upsert no banco).
5. **Celery Bridge**: Código async chamado de dentro de task Celery sempre via `_run_async()` em `workers/tasks.py`.
6. **Schemas Pydantic**: Toda nova mensagem entre agentes deve ter schema Pydantic próprio com `.model_dump_json()` / `.model_validate_json()`.

---

## Definition of Done Universal (DoD Global)

Além dos critérios específicos de cada item, toda story neste backlog deve:

- [ ] Passar em `ruff check .` e `ruff format --check .` sem violações.
- [ ] Ter testes unitários com cobertura ≥ 90% do novo código de lógica de negócio.
- [ ] Ser validada contra ao menos 1 PDF real de produção (não apenas sintético).
- [ ] Não introduzir nenhuma violação de Rule 1 (Anti-OOM) — verificável no review de código.
- [ ] Ter documentação técnica em `Documentacao/` atualizada se introduzir novo agente, fila ou schema.
- [ ] Ter migration Alembic (`upgrade`/`downgrade`) se alterar o schema do banco.
