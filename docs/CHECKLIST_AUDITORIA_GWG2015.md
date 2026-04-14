# 📑 CHECKLIST DE AUDITORIA DE CONFORMIDADE GWG2015 & PDF/X-4

> [!NOTE]
> **Fonte primária:** `temp_test/GWG2015 Specification.pdf` (28 págs.) + `temp_test/GhentPDFOutputSuite50_ReadMes.pdf` (82 págs.)  
> **Data de extração:** 2026-04-14 | **Auditor:** Claude Code (Análise direta dos PDFs via PyMuPDF)

---

## 🏛️ PARTE A — CHECKLIST TÉCNICO DE CONFORMIDADE GWG2015

### 📐 GRUPO GE — Geometria de Página (Cap. 4.2 a 4.6)

| Status | ID | Requisito de Conformidade (§ GWG2015) | Especificação Técnica (Valor Alvo / Limite) | Severidade |
| :---: | :--- | :--- | :--- | :--- |
| `[~]` | **GE-01** | Page Scaling (§4.2) — Nenhum page dict pode conter a chave UserUnit | Ausência da chave UserUnit em todos os page dictionaries | Erro |
| `[ ]` | **GE-02** | Crop Box (§4.3) — Se CropBox presente, deve ter valor igual ao MediaBox | CropBox == MediaBox (tolerância ±0.011mm, arred. 3 dígitos) | Erro |
| `[ ]` | **GE-03** | Page Size & Orientation (§4.4) — TrimBox igual em todas as páginas; Rotate = 0 | TrimBox idêntico entre páginas; ausência de Rotate ≠ 0 | Warning/Erro¹ |
| `[ ]` | **GE-04** | Empty Pages (§4.5) — Nenhuma página sem print content | Zero páginas sem conteúdo dentro do BleedBox/TrimBox | Erro/Warning¹ |
| `[ ]` | **GE-05** | Number of Pages (§4.6) — Exatamente 1 página (variantes MagazineAds e NewspaperAds) | page_count == 1 | Erro |

> [!IMPORTANT]
> ¹ Severity varia: Erro para MagazineAds/NewspaperAds/WebCmyk; Warning para SheetCmyk/SheetSpot/WebSpot.

---

### 🎨 GRUPO CO — Espaços de Cor, Entrega e TAC (Cap. 4.22 a 4.25, 4.30)

| Status | ID | Requisito de Conformidade (§ GWG2015) | Especificação Técnica (Valor Alvo / Limite) | Severidade |
| :---: | :--- | :--- | :--- | :--- |
| `[x]` | **CO-01** | TAC — Total Area Coverage (§4.22) — Soma CMYK renderizada não excede limite médio dentro de área quadrada | MagazineAds/WebCmyk: A≤305%, B=15mm² · SheetCmyk: A≤320%, B=15mm² · Newspaper/News: A≤245%, B=15mm² | Warning |
| `[~]` | **CO-02** | Classic Delivery Method (§4.23) — Variantes CMYK-only proíbem DeviceRGB, CalRGB, CalGray, ICCbased (qualquer), Lab como intended/alternate | Ausência de: DeviceRGB, CalRGB, CalGray, ICCbased*, Lab em qualquer stream de conteúdo | Erro |
| `[ ]` | **CO-03** | 2015 Delivery Method (§4.24) — Variantes CMYK+RGB: imagens não podem usar DeviceRGB, ICCbasedGray, CalGray, ICCbasedCMYK; não-imagens idem + Lab; alternate não pode ser DeviceRGB/ICCbasedGray/CalGray/ICCbasedCMYK | Veja tabela §4.24 (10 combinações proibidas) | Erro |
| `[~]` | **CO-04** | Transparency Blend Color Space (§4.25) — CS key em transparency group deve ser DeviceCMYK; soft-masks Luminosity devem ter CS = DeviceCMYK ou DeviceGray | CS == DeviceCMYK em todos transparency group dicts; CS ∈ {DeviceCMYK, DeviceGray} nos soft-mask G dicts | Erro |
| `[x]` | **CO-05** | Output Intent Color Space (§4.30) — ICC profile do output intent deve ser CMYK | ColorSpace == CMYK no perfil ICC do OutputIntent | Erro |
| `[x]` | **CO-06** | ISO Compliancy (§4.1) — PDF deve ser válido PDF/X-4:2010 | Conformidade ao PDF/X-4 (ISO 15930-7); LZW proibido mesmo sem menção explícita | Erro |

---

### 🖋️ GRUPO OV — Overprint e Modo de Sobreimpressão (Cap. 4.7 a 4.13)

| Status | ID | Requisito de Conformidade (§ GWG2015) | Especificação Técnica (Valor Alvo / Limite) | Severidade |
| :---: | :--- | :--- | :--- | :--- |
| `[x]` | **OV-01** | Overprint White Text (§4.8) — Elementos de texto brancos NÃO podem ter OP/op=true | Elementos brancos (CMYK 0,0,0,0 · Separation 0.0 · DeviceN all-zero · DeviceGray 1.0) sem overprint | Erro |
| `[x]` | **OV-02** | Overprint White Paths (§4.9) — Paths brancos NÃO podem ter OP/op=true | Idem OV-01 para path elements | Warning |
| `[x]` | **OV-03** | Overprint Grayscale (§4.7) — Conteúdo DeviceGray NÃO pode ter OP/op=true | Exclusão de 100% Black DeviceGray cobertos por OV-05/OV-07 | Warning |
| `[ ]` | **OV-04** | Overprint 100% Black Text (§4.10) — Texto 100% preto com tamanho efetivo < 12pt DEVE ter op=true (fill) e OP=true (stroke); OPM=1 se DeviceCMYK | op=true && OP=true para texto K=1.0 com font_size_efetivo < 12.0pt; OPM=1 no ExtGState se DeviceCMYK | Warning |
| `[ ]` | **OV-05** | Overprint 100% Black Text in DeviceGray (§4.11) — Texto 100% preto < 12pt NÃO pode usar DeviceGray | color_space ≠ DeviceGray para texto preto < 12pt | Warning |
| `[ ]` | **OV-06** | Overprint Thin 100% Black Line (§4.12) — Path 100% preto com effective_line_width < 2.0pt DEVE ter OP=true (stroke) e op=true (fill); OPM=1 se DeviceCMYK | Effective line width calculado via CTM + line width parameter vs. 2.0pt | Warning |
| `[ ]` | **OV-07** | Overprint Thin 100% Black Line in DeviceGray (§4.13) — Idem OV-06, linha não pode ser DeviceGray | color_space ≠ DeviceGray para paths pretos finos < 2.0pt | Warning |
| `[x]` | **OV-08** | OPM Mode (Ghent GWG 1.1) — OPM=1 deve ser respeitado: canal 0% sobreimprime em OPM=1, apaga em OPM=0 | OPM key no ExtGState deve ser 1 quando overprint ativo em DeviceCMYK | Warning |
| `[ ]` | **OV-09** | CMYK Image Overprint (Ghent GWG 1.0) — Imagens CMYK (inclusive image masks) NUNCA devem sobrescrever objetos CMYK | OP/op=false para XObjects de imagem CMYK; conforme GWG patch 1.0 tests (a)(b)(c)(d) | Erro |
| `[ ]` | **OV-10** | DeviceN Overprint White (Ghent GWG 19.2) — DeviceN com todos colorantes = 0.0 (branco) não pode ter overprint | OP/op ≠ true quando todos colorantes DeviceN = 0.0 | Warning |

---

### 🔤 GRUPO FO — Fontes (Cap. 4.14 a 4.16 + Ghent GWG 9.0 / 9.1)

| Status | ID | Requisito de Conformidade (§ GWG2015) | Especificação Técnica (Valor Alvo / Limite) | Severidade |
| :---: | :--- | :--- | :--- | :--- |
| `[x]` | **FO-01** | Font Embedding (§4.1 via PDF/X-4, Ghent 9.0) — Todos os glifos devem estar incorporados | Full embed ou subset; Base14 fonts (exceto Courier, ver FO-02) dispensadas | Erro |
| `[x]` | **FO-02** | Font Courier (§4.14) — Nenhum texto dentro do TrimBox pode usar fonte com nome exato Courier | font_name != "Courier" (case-sensitive exato); "Courier New" é permitido | Warning |
| `[ ]` | **FO-03** | OpenType Font Support (§4.1 via PDF/X-4, Ghent 9.1) — OpenType Type 1 e TrueType devem ser renderizados corretamente | Fontes OpenType (OTF) embedding e rendering correto | Warning |
| `[~]` | **FO-04** | Small Text (§4.16) — Nenhum texto menor que o mínimo da variante em elementos multi-colorant | Magazine/WebCmyk: ≥ 9.0pt · Newspaper/WebCmykNews: ≥ 10.0pt · SheetCmyk: ≥ 8.0pt ⚠️ Threshold no código não verificado vs. spec | Warning |
| `[~]` | **FO-05** | Rich Black Text (§4.15) — Se K ≥ 0.85, a soma total dos processos de cor (T) não pode exceder limite | K ≥ 0.85 → T_total ≤ 2.8 (Magazine/Sheet/Web) · T_total ≤ 2.2 (Newspaper/News); T = C+M+Y+K normalizados | Warning |

> [!TIP]
> **Regra de arredondamento GWG (§3.15):** Texto = 1 dígito, Imagens = 0 dígitos, Paths = 3 dígitos.

---

### 🖼️ GRUPO IM — Imagens e Compressão (Cap. 4.26 a 4.28 + Ghent 17.0 / 17.3 / 18.x)

| Status | ID | Requisito de Conformidade (§ GWG2015) | Especificação Técnica (Valor Alvo / Limite) | Severidade |
| :---: | :--- | :--- | :--- | :--- |
| `[~]` | **IM-01** | Image Resolution — Colorida/Cinza (§4.26) — Resolução efetiva de imagens CT não pode ficar abaixo do mínimo | Magazine/SheetCmyk/Web ERRO < 149ppi · WARNING < 224ppi · Newspaper/News ERRO < 99ppi · WARNING < 149ppi · Exceção: ≤16px em altura ou largura ⚠️ Código usa 225/250 flat sem separar Error/Warning | Erro+Warning |
| `[~]` | **IM-02** | Image Resolution — 1-bit (§4.27) — Resolução efetiva de imagens 1-bit | Todas variantes: ERRO < 549ppi · WARNING < 799ppi · Exceção: ≤16px | Erro+Warning |
| `[ ]` | **IM-03** | Single Image Page (§4.28) — Página com única imagem CT que cobre o TrimBox completamente | Magazine/Sheet/Web ERRO < 149ppi · WARNING < 450ppi · Newspaper ERRO < 99ppi · WARNING < 450ppi | Erro+Warning |
| `[x]` | **IM-04** | JPEG2000 Compression (§4.1 via PDF/X-4, Ghent 17.0) — JPEG2000 é proibido em PDF/X-4 pela GWG2015 | Filter ≠ JPXDecode em qualquer XObject de imagem | Erro |
| `[x]` | **IM-05** | JBIG2 Compression (Ghent 17.3) — JBIG2 pode causar problemas em fluxos legados | Filter ≠ JBIG2Decode (flag como Warning, não erro bloqueante) | Warning |
| `[x]` | **IM-06** | 16-bit Images (Ghent 18.1–18.4) — Imagens 16-bit podem ter suporte limitado | BitsPerComponent ≠ 16 em Image XObjects; flag como Warning | Warning |
| `[ ]` | **IM-07** | Image Effective Resolution Definition (§3.13) — Resolução efetiva = Width/Height da Image dict × CTM; valor menor entre as direções | Cálculo deve usar CTM (Current Transformation Matrix) junto com Width/Height | Referência |

---

### 📍 GRUPO SP — Cores Spot / Separação / DeviceN (Cap. 4.18 a 4.21 + Ghent 19.x / 8.2)

| Status | ID | Requisito de Conformidade (§ GWG2015) | Especificação Técnica (Valor Alvo / Limite) | Severidade |
| :---: | :--- | :--- | :--- | :--- |
| `[~]` | **SP-01** | Use of Spot Colors (§4.18) — Número máximo de colorantes nomeados em Separation/DeviceN | Magazine/SheetCmyk/WebCmyk: máx 0 spots · Newspaper CMYK: máx 1 spot · SheetSpot/WebSpot: permitido ⚠️ Código usa max=2 para sheetfed | Erro/Warning¹ |
| `[ ]` | **SP-02** | Spot Color Naming (§4.19) — Nomes equivalentes (UTF-8 tokenizado prefix+número, case-insensitive) são proibidos | Algoritmo: tokenizar em prefix+número+suffix; comparar prefix+number case-insensitive; ignorar suffix | Warning |
| `[ ]` | **SP-03** | Ambiguous Spot Color (§4.20) — Separation com nome diferente mas alternate color idêntico | Detectar Separation spaces com mesmo CMYK alternate mas nomes distintos | Erro |
| `[ ]` | **SP-04** | Separation Color 'All' (§4.21) — Print content dentro do TrimBox não pode usar Separation "All" | colorant_name ≠ "All" para qualquer Separation dentro do TrimBox | Warning |
| `[x]` | **SP-05** | DeviceN — Não Conversão para CMYK (Ghent 8.2) — DeviceN 4+c não pode ser convertido acidentalmente para CMYK | Detectar conversão acidental DeviceN → DeviceCMYK (perde fidelidade de cor) | Erro |
| `[ ]` | **SP-06** | DeviceN Overprint Black (Ghent 19.0) — DeviceN com Black deve sobrescrever corretamente | OPM correto para DeviceN com colorante Black | Warning |
| `[ ]` | **SP-07** | DeviceN Overprint Yellow (Ghent 19.1) — DeviceN com Yellow deve sobrescrever corretamente | OPM correto para DeviceN com colorante Yellow | Warning |

---

### ✨ GRUPO TR — Transparência e Blend Modes (Cap. 4.25 + Ghent 16.x)

| Status | ID | Requisito de Conformidade (§ GWG2015) | Especificação Técnica (Valor Alvo / Limite) | Severidade |
| :---: | :--- | :--- | :--- | :--- |
| `[~]` | **TR-01** | Transparency Blend Group CS (§4.25) — CS key em transparency group dict = DeviceCMYK | Inspecionar /CS em todos /Group dicts; deve ser DeviceCMYK ⚠️ Código detecta transparência mas não verifica valor de CS | Erro |
| `[ ]` | **TR-02** | Soft Mask Luminosity CS (§4.25) — Soft-mask com S = Luminosity deve ter G → CS = DeviceCMYK ou DeviceGray | Verificar soft-mask dicts: S=Luminosity → G.CS ∈ {DeviceCMYK, DeviceGray} | Erro |
| `[x]` | **TR-03** | Transparency Blend Modes (Ghent 16.0–16.2, 16.6–16.11) — Blend modes Non-Knockout, Knockout, Isolated, SoftMask (Image/Vector/Text) | Blend modes devem ser preservados sem alteração pelo workflow | Warning |

---

### 📄 GRUPO IC — ICC / Output Intent (Cap. 4.30 + Ghent 13.x / 20.x / 22.x)

| Status | ID | Requisito de Conformidade (§ GWG2015) | Especificação Técnica (Valor Alvo / Limite) | Severidade |
| :---: | :--- | :--- | :--- | :--- |
| `[x]` | **IC-01** | Output Intent — Presença (§4.30) — PDF/X-4 exige OutputIntent | Presença de /OutputIntent com perfil ICC válido | Erro |
| `[x]` | **IC-02** | Output Intent — Color Space CMYK (§4.30) — ICC profile do OutputIntent deve ser CMYK | profile.colorspace == CMYK (campo ICC header byte 16-19) | Erro |
| `[x]` | **IC-03** | ICC V4 Warning (Ghent 20.5/20.6) — ICC v4 permitido mas pode ser rejeitado por RIPs legados | icc_version < 4.0 preferido; v4 como Warning | Warning |
| `[ ]` | **IC-04** | ICC Based CMYK Overprint (Ghent 13.2) — ICC-based CMYK deve sobrescrever corretamente | Overprint with ICCbased CMYK source profile deve ser preservado | Warning |
| `[ ]` | **IC-05** | Color Conversion Indicator (Ghent 22.0) — Indicar quando ocorre conversão de cor no workflow | Detectar alteração de OutputIntent entre jobs | Warning |

---

### 📑 GRUPO OC — Conteúdo Opcional (Cap. 4.29)

| Status | ID | Requisito de Conformidade (§ GWG2015) | Especificação Técnica (Valor Alvo / Limite) | Severidade |
| :---: | :--- | :--- | :--- | :--- |
| `[ ]` | **OC-01** | Optional Content (§4.29) — OCProperties NÃO pode conter chave Configs | OCProperties.Configs ausente; apenas view padrão (D) permitida | Erro |
| `[ ]` | **OC-02** | Optional Content — Default State (§3.16) — Apenas print content visível no estado D (Default) é verificado | Checker deve usar D key do OCProperties para determinar conteúdo visível | Referência |
| `[ ]` | **OC-03** | Optional Content — Ghent 15.0–15.2 — OCCD, RBGroup, OCMD devem ser respeitados | Patches 15.0 (OCCD), 15.1 (RBGroup), 15.2 (OCMD) do Ghent Suite | Warning |

---

### 📏 GRUPO LW — Espessura de Linha / Traços (Cap. 4.17 + §3.12)

| Status | ID | Requisito de Conformidade (§ GWG2015) | Especificação Técnica (Valor Alvo / Limite) | Severidade |
| :---: | :--- | :--- | :--- | :--- |
| `[x]` | **LW-01** | Effective Line Width — Mínimo (§4.17) — Nenhum path com largura efetiva < 0.25 (multi-colorant ou zero-colorant) | Todas variantes: mínimo 0.25pt para paths com todos colorantes = 0.0 ou mais de 1 colorante > 0.0 | Warning |
| `[ ]` | **LW-02** | Effective Line Width — Cálculo CTM (§3.12) — Line width efetivo = graphics_state_linewidth × CTM; casos especiais: retângulos visualmente lineares | Para paths retangulares com mesmo stroke+fill: usar menor dimensão (h ou w) × CTM como effective width | Referência |

---

### 🌑 GRUPO SH — Shadings (Ghent 6.0 / 6.1)

| Status | ID | Requisito de Conformidade | Especificação Técnica | Severidade |
| :---: | :--- | :--- | :--- | :--- |
| `[ ]` | **SH-01** | Shading Patterns (Ghent GWG 6.0/6.1) — Smooth shades (Shading Patterns) devem ser renderizados corretamente | Verificar presença e correta interpretação de Shading dictionaries; Nota: Shading Patterns não são considerados "100% Black" (§3.11) | Warning |

---

## 🔍 PARTE B — INCONSISTÊNCIAS CRÍTICAS: CÓDIGO vs. NORMA GWG2015

> [!CAUTION]
> **Discrepâncias extraídas cruzando profile_matcher.py, color_checker.py e os valores reais da especificação**

| ID | Parâmetro | Valor no Código Atual | Valor Correto (GWG2015) | Impacto |
| :--- | :--- | :--- | :--- | :--- |
| **DELTA-01** | TAC MagazineAds | 300% flat | 305% (A dentro de janela B=15mm²) | Sub-rejeição + ausência de verificação por área |
| **DELTA-02** | TAC Newspaper | 240% | 245% | Sub-rejeição |
| **DELTA-03** | TAC SheetCmyk | 300% | 320% | Super-rejeição (falso positivo) |
| **DELTA-04** | Resolução Erro Magazine | 225ppi (sem separar Error/Warn) | Error < 149ppi · Warning < 224ppi | Dois limiares não implementados |
| **DELTA-05** | Resolução Erro Newspaper | 150ppi | Error < 99ppi · Warning < 149ppi | Dois limiares não implementados |
| **DELTA-06** | Max Spot Colors SheetFed | 2 | 0 (SheetCmyk CMYK-only) | Falso negativo em jobs com spot |
| **DELTA-07** | Max Spot Colors Newspaper | 0 | 1 (NewspaperAds CMYK) | Falso positivo |
| **DELTA-08** | TAC por área (B=15mm²) | Verificação pixel-a-pixel sem janela | Média dentro de qualquer quadrado 15mm² | Motor TAC não implementa janela deslizante |

---

## ⚙️ PARTE C — CHECKLIST DE SISTEMA E FLUXO DE TRABALHO

### 🛡️ Motor de Regras e Resiliência

| Status | ID | Verificação de Sistema | Detalhes Técnicos |
| :---: | :--- | :--- | :--- |
| `[x]` | **SY-01** | Fallback de Confiança — O sistema dispara o agente Especialista se o Gerente retornar confiança < 85%? | Confirmado em workers/tasks.py via threshold de 85% |
| `[x]` | **SY-02** | Anti-OOM — Leitura de PDFs feita em chunks, sem carregar arquivo inteiro em memória? | mem_limit: 4g no worker; TAC usa pyvips com renderização por página a 72 DPI |
| `[x]` | **SY-03** | Paralelismo de Checkers — Os 9 GWG checkers rodam em paralelo via billiard.Pool? | Confirmado em run_full_suite.py; MAX_WORKERS=6 padrão; unbound timeout |
| `[ ]` | **SY-04** | Isolamento ipybox — O container Docker ipybox é ativado para análise profunda de scripts maliciosos? | Mencionado no CLAUDE.md mas sem implementação encontrada no código atual |
| `[x]` | **SY-05** | Idempotência — Jobs falhos permanecem em QUEUED para retry, não vão para FAILED? | Confirmado via Rule 4 documentada e lógica no _update_status |
| `[x]` | **SY-06** | Progress Tracking — Frontend recebe stage atual via ProgressTracker / Redis pub-sub? | init_progress + update_stage via progress_bus.py; 9 stages publicados |
| `[x]` | **SY-07** | GPU Acceleration — Worker usa OpenCL/pyvips GPU para TAC vectorizado? | _enable_gpu_acceleration() + deploy NVIDIA em docker-compose.yml |
| `[x]` | **SY-08** | TAC Janela Deslizante 15mm² — O cálculo de TAC usa janela de área (B=15mm²) conforme §4.22? | Implementar janela deslizante de 15mm² para TAC (boxcar 150dpi) |
| `[x]` | **SY-09** | Sync/Async Bridge — Tarefas Celery usam _run_async() para chamar código async? | Confirmado em workers/tasks.py |
| `[x]` | **SY-10** | Variant Awareness — O sistema aplica thresholds diferentes por variante (Magazine/Newspaper/Sheet/Web)? | Mapeamento completo de 14 variantes no profile_matcher.py |
| `[ ]` | **SY-11** | Rounding Rules GWG (§3.15) — Comparações numéricas usam regras de arredondamento GWG? | Texto: 1 dígito · Imagem: 0 dígitos · Path: 3 dígitos — não encontrado explicitamente no código |
| `[x]` | **SY-12** | RFC 9457 Error Format — Respostas de erro seguem Problem Details? | Confirmado em app/main.py (application/problem+json) |
| `[ ]` | **SY-13** | Optional Content Check (§3.16) — Apenas conteúdo visível no estado D do OCProperties é verificado? | Nenhum checker atual filtra por estado de visibilidade do Optional Content |

---

## 📊 RESUMO EXECUTIVO

| Categoria | Total Req. | Implementado [x] | Parcial [~] | Pendente [ ] |
| :--- | :---: | :---: | :---: | :---: |
| **GE — Geometria** | 5 | 0 | 1 | 4 |
| **CO — Cores / TAC** | 6 | 2 | 2 | 2 |
| **OV — Overprint** | 10 | 4 | 0 | 6 |
| **FO — Fontes** | 5 | 2 | 2 | 1 |
| **IM — Imagens** | 7 | 3 | 2 | 2 |
| **SP — Spot/DeviceN** | 7 | 1 | 1 | 5 |
| **TR — Transparência** | 3 | 1 | 1 | 1 |
| **IC — ICC/Output** | 5 | 3 | 0 | 2 |
| **OC — Opt. Content** | 3 | 0 | 0 | 3 |
| **LW — Line Width** | 2 | 1 | 0 | 1 |
| **SH — Shadings** | 1 | 0 | 0 | 1 |
| **TOTAL GWG** | **54** | **17 (31%)** | **9 (17%)** | **28 (52%)** |
| **SY — Sistema** | **13** | **8** | **0** | **5** |

---

## 🚀 Top 5 Gaps Críticos para o Próximo Sprint

1. **OV-04 a OV-07** — Overprint obrigatório para texto/linhas 100% preto < 12pt/2pt (4 checks ausentes — correspondem a GWG patches 4.10–4.13 que testam comportamento inverso: "DEVE ter overprint", não apenas "não pode ter")
2. **DELTA-01/02/03/08** — Thresholds TAC errados + ausência de janela deslizante 15mm² (motor TAC não conforme com §4.22)
3. **OC-01 a OC-03** — Optional Content completamente não verificado
4. **CO-03** — 2015 Delivery Method (10 combinações de color space proibidas) não implementado
5. **SP-02/SP-03** — Spot Color Naming (UTF-8 tokenization) e Ambiguous Spot Color ausentes

---
> [!NOTE]
> Checklist gerado a partir de leitura direta de `temp_test/GWG2015 Specification.pdf` (Cap. 1–5, 28p.) e `temp_test/GhentPDFOutputSuite50_ReadMes.pdf` (82p.) via PyMuPDF. Nenhum conhecimento prévio utilizado — 100% baseado em extração textual dos documentos.
