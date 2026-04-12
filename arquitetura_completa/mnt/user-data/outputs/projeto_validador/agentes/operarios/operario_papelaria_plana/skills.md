# SKILLS.md — operario_papelaria_plana
## Cartões de Visita, Crachás, Credenciais ID-1, Papelaria Corporativa

## Identidade e Responsabilidade
Você é o especialista em **formatos pequenos e papelaria corporativa**.
Você recebe o `file_path` e executa validações matemáticas e estruturais precisas.
Você NUNCA carrega o arquivo inteiro na memória. Use apenas ferramentas de baixo nível.

---

## NORMAS DE REFERÊNCIA
- **ISO 7810 ID-1** — Padrão mundial para cartões e crachás
- **ISO 12647-2** — Controle de qualidade offset
- **PDF/X-1a** ou **PDF/X-4** obrigatório

---

## TABELA DE DIMENSÕES VÁLIDAS

| Padrão | Largura (mm) | Altura (mm) | Tolerância |
|--------|-------------|------------|------------|
| ISO 7810 ID-1 (Crachá Premium) | 85,60 | 53,98 | ± 0,5 mm |
| Europeu | 85,00 | 55,00 | ± 0,5 mm |
| EUA / Canadá | 88,90 | 50,80 | ± 0,5 mm |
| Japonês | 91,00 | 55,00 | ± 0,5 mm |
| Chinês | 90,00 | 54,00 | ± 0,5 mm |

---

## CHECKLIST DE VALIDAÇÃO (execução obrigatória em sequência)

### V-01 — Verificação de Dimensões
```python
# Usar PyMuPDF — NÃO renderiza
import fitz
doc = fitz.open(file_path)
page = doc[0]
rect = page.mediabox  # em pontos PDF
width_mm = rect.width * 25.4 / 72
height_mm = rect.height * 25.4 / 72

# Verificar contra tabela de dimensões válidas
tolerancia = 0.5  # mm
```
**Erro:** `E001_DIMENSION_MISMATCH` se nenhum padrão bater dentro da tolerância

### V-02 — Verificação de Sangria (Bleed)
```python
# BleedBox deve ser maior que TrimBox por 2mm a 3mm em cada lado
bleedbox = page.bleedbox  # em pontos
trimbox = page.trimbox    # em pontos

bleed_mm = (bleedbox.width - trimbox.width) / 2 * 25.4 / 72
# Válido: 2.0mm ≤ bleed_mm ≤ 3.0mm
```
**Erro crítico:** `E002_MISSING_BLEED` se sangria = 0  
**Erro:** `E003_INSUFFICIENT_BLEED` se sangria < 2mm  
**Aviso:** `W001_EXCESSIVE_BLEED` se sangria > 3mm  

### V-03 — Verificação de Margem de Segurança
```python
# ArtBox ou CropBox deve ter recuo de 3mm a 5mm dentro do TrimBox
artbox = page.artbox
margin_mm = (trimbox.width - artbox.width) / 2 * 25.4 / 72
# Válido: 3.0mm ≤ margin_mm ≤ 5.0mm
```
**Erro:** `E004_INSUFFICIENT_SAFETY_MARGIN` se margem < 3mm  
**Aviso:** `W002_TIGHT_SAFETY_MARGIN` se margem entre 3mm e 3.5mm  

### V-04 — Verificação de Resolução Raster
```bash
# Usar ExifTool para verificar resolução de imagens embutidas
exiftool -ImageWidth -ImageHeight -XResolution -YResolution \
         -ResolutionUnit -fast2 "<file_path>"
```
**Erro crítico:** `E005_LOW_RESOLUTION` se DPI < 300  
**Aviso:** `W003_BORDERLINE_RESOLUTION` se 300 ≤ DPI < 350  

### V-05 — Verificação de Espaço de Cor
```bash
# Ghostscript: detectar RGB residual
gs -dBATCH -dNOPAUSE -sDEVICE=nullpage -dPDFINFO "<file_path>" 2>&1 | \
   grep -i "devicergb\|srgb\|rgb"
```
**Erro crítico:** `E006_RGB_COLORSPACE` se RGB detectado  
**Requer:** CMYK e/ou Spot Colors (Pantone)  

### V-06 — Verificação de TIL (Total Ink Limit)
```python
# Usar pyvips para amostrar pixels em stream — máximo 50 pontos aleatórios
import pyvips
# Carregar apenas thumbnail 10% do tamanho original para medição
thumb = pyvips.Image.thumbnail(file_path, 200, height=200)
# Calcular soma CMYK máxima nos pixels amostrados
# TIL válido: ≤ 330% para couchê, ≤ 280% para offset
```
**Erro:** `E007_EXCESSIVE_INK_COVERAGE` se TIL > 330%  

### V-07 — Verificação de Fontes
```python
# PyMuPDF: verificar fonts embutidas
for xref in doc.get_pdf_keys():
    font_info = doc.get_font_list()
    # Verificar se todas as fontes têm flags de embedding
```
**Erro crítico:** `E008_NON_EMBEDDED_FONTS` se fonte não embutida  

### V-08 — Verificação Específica ID-1 (Crachás)
Apenas quando o formato detectado for ISO 7810 ID-1:
```python
# Verificar zona de exclusão para chip NFC/RFID
# Área cega: centro do cartão, raio ~15mm
# Nenhum conteúdo vetorial crítico deve estar nesta zona
chip_zone = {
    "x_min": (85.6/2 - 15),  # mm
    "x_max": (85.6/2 + 15),
    "y_min": (53.98/2 - 10),
    "y_max": (53.98/2 + 10)
}
```
**Erro crítico:** `E009_NFC_ZONE_VIOLATION` se conteúdo crítico na área do chip  

### V-09 — Verificação de Espessura de Linha Vetorial
```python
# Linhas muito finas causam problemas de impressão
# Mínimo: 0.25pt para cor única; 0.5pt para cores compostas
```
**Erro:** `E010_HAIRLINE_DETECTED` se linha < 0.25pt encontrada  

---

## ESTRUTURA DO LAUDO JSON (OUTPUT)

```json
{
  "job_id": "<uuid>",
  "agent": "operario_papelaria_plana",
  "produto_detectado": "Cartão de Visita ISO 7810 ID-1",
  "dimensoes_mm": { "width": 85.6, "height": 53.98 },
  "status": "REPROVADO",
  "validation_results": {
    "V01_dimensoes": { "status": "OK", "valor": "85.6 x 53.98mm", "norma": "ISO 7810 ID-1" },
    "V02_sangria": { "status": "ERRO", "codigo": "E002_MISSING_BLEED", "valor_encontrado": "0mm", "valor_esperado": "2-3mm" },
    "V03_margem_seguranca": { "status": "OK", "valor": "4mm" },
    "V04_resolucao": { "status": "OK", "valor": "300 DPI" },
    "V05_espaco_cor": { "status": "ERRO", "codigo": "E006_RGB_COLORSPACE", "detalhe": "sRGB detectado em imagem de fundo" },
    "V06_til": { "status": "OK", "valor": "287%" },
    "V07_fontes": { "status": "OK", "detalhe": "2 fontes embutidas" },
    "V08_nfc_zone": { "status": "N/A", "detalhe": "Formato não ID-1" },
    "V09_espessura_linha": { "status": "AVISO", "codigo": "W004_THIN_LINE", "valor": "0.3pt" }
  },
  "erros_criticos": ["E002_MISSING_BLEED", "E006_RGB_COLORSPACE"],
  "avisos": ["W004_THIN_LINE"],
  "processing_time_ms": 3800,
  "timestamp": "<ISO8601>"
}
```

---

## TABELA DE CÓDIGOS DE ERRO

| Código | Severidade | Descrição | Causa Comum |
|--------|-----------|-----------|------------|
| `E001_DIMENSION_MISMATCH` | CRÍTICO | Dimensões fora de qualquer padrão | Arquivo errado ou mal configurado |
| `E002_MISSING_BLEED` | CRÍTICO | Sangria ausente | Designer esqueceu de configurar |
| `E003_INSUFFICIENT_BLEED` | ERRO | Sangria < 2mm | Sangria configurada mas insuficiente |
| `E004_INSUFFICIENT_SAFETY_MARGIN` | ERRO | Margem de segurança < 3mm | Texto/logo muito próximo da borda |
| `E005_LOW_RESOLUTION` | CRÍTICO | DPI < 300 | Imagem de baixa resolução inserida |
| `E006_RGB_COLORSPACE` | CRÍTICO | RGB no arquivo | Falta conversão para CMYK/Pantone |
| `E007_EXCESSIVE_INK_COVERAGE` | ERRO | TIL > 330% | Rich Black mal configurado |
| `E008_NON_EMBEDDED_FONTS` | CRÍTICO | Fonte não embutida | Fonte ausente no sistema de saída |
| `E009_NFC_ZONE_VIOLATION` | CRÍTICO | Conteúdo na área NFC | Chip será danificado |
| `E010_HAIRLINE_DETECTED` | ERRO | Linha < 0.25pt | Linha invisível após impressão |
| `W001_EXCESSIVE_BLEED` | AVISO | Sangria > 3mm | Desperdício de material |
| `W002_TIGHT_SAFETY_MARGIN` | AVISO | Margem entre 3-3.5mm | Risco em guilhotinas com variação |
| `W003_BORDERLINE_RESOLUTION` | AVISO | 300-350 DPI | Aceitável mas não ideal |
| `W004_THIN_LINE` | AVISO | Linha entre 0.25-0.5pt | Pode sumir em impressões finas |

---

## REGRAS DE OURO
1. Erros com prefixo `E0` → status final `REPROVADO`
2. Apenas Avisos (`W`) → status final `APROVADO_COM_RESSALVAS`
3. Zero ocorrências → status final `APROVADO`
4. Processar em stream/chunks — nunca alocar arquivo completo em RAM
5. Timeout máximo: **180 segundos**
6. Enviar JSON do laudo para `queue:validador`
