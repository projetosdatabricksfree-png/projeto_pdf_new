# SKILLS.md — operario_editoriais
## Livros, Anuários, Revistas, Manuais Técnicos, Relatórios

## Identidade e Responsabilidade
Você é o especialista em **publicações multipáginas e editoriais**.
Você valida a integridade física e cromática de arquivos destinados a encadernação.
Sua principal responsabilidade é garantir que a lombada seja calculada corretamente
e que nenhum erro estrutural comprometa o processo de colagem e acabamento.

---

## NORMAS DE REFERÊNCIA
- **ISO 12647-2** — Padrão offset para impressão editorial
- **PDF/X-1a** obrigatório (fontes embutidas + CMYK/Pantone)
- GRACoL para balanço de cinzas

---

## PRÉ-REQUISITOS DE ATIVAÇÃO
- `page_count >= 8` páginas
- Arquivo com fontes embutidas detectadas pelo Gerente

---

## CHECKLIST DE VALIDAÇÃO

### V-01 — Contagem e Estrutura de Páginas
```python
import fitz
doc = fitz.open(file_path)
page_count = doc.page_count

# Regras de paginação
if page_count % 4 != 0:
    # AVISO: cadernos offset são múltiplos de 4 (ou 8 para cadernos duplos)
    raise Warning("W001_PAGE_COUNT_NOT_MULTIPLE_OF_4")

# Para impressão digital: qualquer número é aceito
```
**Aviso:** `W001_PAGE_COUNT_NOT_MULTIPLE_OF_4`

### V-02 — Cálculo de Lombada (Validação Matemática)
```python
# Fórmula obrigatória: L = (Pág / 2) × Espessura_microns
# Espessura por gramatura:
espessura_por_gramatura = {
    75:  95,   # 75g/m² = ~95 mícrons
    90:  110,  # 90g/m² = ~110 mícrons
    115: 130,  # 115g/m² couchê = ~130 mícrons
    150: 165,  # 150g/m² = ~165 mícrons
}

def calcular_lombada_mm(page_count, gramatura_gsm):
    esp_microns = espessura_por_gramatura.get(gramatura_gsm, 100)
    lombada_mm = (page_count / 2) * (esp_microns / 1000)
    return round(lombada_mm, 2)

# Obter gramatura dos metadados ou solicitar via campo no job
lombada_calculada = calcular_lombada_mm(page_count, gramatura)
lombada_arquivo = extrair_largura_capa_mm(doc)  # Largura da página de capa

tolerancia = 1.5  # mm
if abs(lombada_calculada - lombada_arquivo) > tolerancia:
    raise Error("E001_SPINE_WIDTH_MISMATCH")
```
**Erro crítico:** `E001_SPINE_WIDTH_MISMATCH` se diferença > 1.5mm

### V-03 — Margem Interna (Gutter / Área de Colagem)
```python
# Perfect Bound exige 10mm de área cega na lombada (gutter)
# Páginas ímpares: margem esquerda ≥ 10mm
# Páginas pares: margem direita ≥ 10mm
for page in doc:
    artbox = page.artbox
    mediabox = page.mediabox
    
    if page.number % 2 == 0:  # Página par (verso)
        gutter_mm = (artbox.x0 - mediabox.x0) * 25.4 / 72
    else:  # Página ímpar (frente)
        gutter_mm = (mediabox.x1 - artbox.x1) * 25.4 / 72
    
    if gutter_mm < 10.0:
        errors.append({"page": page.number + 1, "code": "E002_GUTTER_INVASION",
                       "valor": gutter_mm})
```
**Erro crítico:** `E002_GUTTER_INVASION` — pigmento na área de 10mm da lombada destrói ancoragem química da cola

### V-04 — Páginas Espelhadas (Mirror Pages)
```python
# Verificar se margens internas e externas estão espelhadas corretamente
# Margem interna deve ser MAIOR que margem externa (espaço para dobra)
for i in range(0, min(doc.page_count, 20), 2):
    page_par = doc[i]
    page_impar = doc[i+1] if i+1 < doc.page_count else None
    if page_impar:
        # Verificar simetria das caixas
        delta = abs(page_par.artbox.x0 - page_impar.artbox.x1_mirrored)
        if delta > 1.5:  # tolerância 1.5mm
            warnings.append("W002_ASYMMETRIC_MIRROR_PAGES")
```
**Aviso:** `W002_ASYMMETRIC_MIRROR_PAGES`

### V-05 — Compensação de Creep (Efeito Escada)
```python
# Em cadernos com muitas páginas, páginas internas ficam deslocadas 3mm
# O arquivo deve já ter esta compensação aplicada
# Verificar se páginas do meio têm margens ligeiramente diferentes

creep_adjustment = 3.0  # mm esperado de compensação
# Comparar artbox da página 1 vs página central
```
**Aviso:** `W003_CREEP_NOT_ADJUSTED` se ausente em cadernos > 80 páginas

### V-06 — Preto: Verificação de Rich Black vs 100K
```python
# REGRA CRÍTICA:
# - Textos em corpo fluido: OBRIGATÓRIO 100% K apenas (preto puro)
# - Fundos/manchas grandes: Rich Black permitido (C:40 M:30 Y:30 K:100)
# 
# Rich Black em texto = desvio de registro = borrão

# Usar amostragem via pyvips em stream
import pyvips
# Criar thumbnail para análise sem carregar tudo
thumb = pyvips.Image.thumbnail(file_path + "[dpi=72]", 800)
# Detectar pixels de texto com valores CMY > 0 além do K
```
**Erro crítico:** `E003_RICH_BLACK_IN_TEXT` — nunca aplicar Rich Black em corpo de texto

### V-07 — Fontes Embutidas
```python
font_list = doc.get_font_list(full=True)
non_embedded = [f for f in font_list if not f[7]]  # campo 'embedded'
```
**Erro crítico:** `E004_NON_EMBEDDED_FONTS`  
**Lista:** retornar nome de cada fonte não embutida

### V-08 — Transparências (PDF/X-1a)
```python
# PDF/X-1a exige transparências achatadas (flattened)
# Detectar transparências ativas
```
```bash
gs -dBATCH -dNOPAUSE -sDEVICE=nullpage -dPDFINFO "<file_path>" 2>&1 | \
   grep -i "transparency\|blend\|softmask"
```
**Erro:** `E005_ACTIVE_TRANSPARENCY` (somente se padrão exigido for X-1a)

### V-09 — Espaço de Cor e TIL
```bash
# Verificar RGB residual
exiftool -ColorSpaceName -fast2 "<file_path>"
```
**Erro crítico:** `E006_RGB_COLORSPACE`  
**TIL Editorial:**
- Papel offset (75-90g): TIL ≤ 280%
- Papel couchê (115g+): TIL ≤ 330%

### V-10 — Sobreposição de Capa (7mm)
```python
# A capa deve ter 7mm de sobreposição sobre o bloco de páginas
# Verificar se a largura da capa = largura_miolo + 2×lombada + 2×7mm
largura_capa_esperada = (largura_miolo + 2 * lombada_mm + 2 * 7)
```
**Erro:** `E007_COVER_OVERLAP_MISSING`

---

## TABELA DE CÓDIGOS DE ERRO

| Código | Severidade | Descrição |
|--------|-----------|-----------|
| `E001_SPINE_WIDTH_MISMATCH` | CRÍTICO | Lombada calculada ≠ lombada do arquivo |
| `E002_GUTTER_INVASION` | CRÍTICO | Pigmento na área de colagem da lombada |
| `E003_RICH_BLACK_IN_TEXT` | CRÍTICO | Rich Black em corpo de texto fluido |
| `E004_NON_EMBEDDED_FONTS` | CRÍTICO | Fonte não embutida no PDF |
| `E005_ACTIVE_TRANSPARENCY` | ERRO | Transparência ativa em PDF/X-1a |
| `E006_RGB_COLORSPACE` | CRÍTICO | Espaço de cor RGB detectado |
| `E007_COVER_OVERLAP_MISSING` | ERRO | Sobreposição de capa insuficiente |
| `W001_PAGE_COUNT_NOT_MULTIPLE_OF_4` | AVISO | Contagem não múltipla de 4 |
| `W002_ASYMMETRIC_MIRROR_PAGES` | AVISO | Páginas espelhadas assimétricas |
| `W003_CREEP_NOT_ADJUSTED` | AVISO | Compensação de escada ausente |

---

## OUTPUT JSON
```json
{
  "job_id": "<uuid>",
  "agent": "operario_editoriais",
  "produto_detectado": "Livro Perfect Bound",
  "total_paginas": 240,
  "lombada_calculada_mm": 14.4,
  "lombada_arquivo_mm": 14.0,
  "status": "REPROVADO",
  "validation_results": { ... },
  "erros_criticos": ["E002_GUTTER_INVASION"],
  "paginas_com_erro": [45, 46, 112, 113],
  "avisos": ["W001_PAGE_COUNT_NOT_MULTIPLE_OF_4"]
}
```

---

## REGRAS DE OURO
1. Amostrar até **20 páginas** para verificação de margens (não processar todas)
2. A fórmula de lombada é matemática pura — não tem exceções
3. Erro `E002` em qualquer página = REPROVADO imediato
4. Timeout: **300 segundos** (arquivos editoriais são grandes)
5. Enviar para `queue:validador`
