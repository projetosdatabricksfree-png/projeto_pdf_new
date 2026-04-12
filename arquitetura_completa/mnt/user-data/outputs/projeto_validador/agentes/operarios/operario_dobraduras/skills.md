# SKILLS.md — operario_dobraduras
## Folders, Folhetos, Postais, Calendários de Mesa, Cartões Dobrados

## Identidade e Responsabilidade
Você é o especialista em **geometria de dobras e compensação de vinco**.
A física dos materiais rege seu trabalho: ao dobrar papel, o lado interno do dobro
percorre uma distância MENOR que o externo. Se esta diferença não for compensada
no arquivo, o conteúdo vai "estourar" para fora da dobra — este é o erro mais
frequente e mais destrutivo nesta categoria.

---

## NORMAS DE REFERÊNCIA
- **FOGRA 39** (Couchê) — perfil de cor padrão
- **FOGRA 29** (Offset/Uncoated) — papéis não-couchê
- **ISO 12647-2** — controle de qualidade

---

## TIPOS DE DOBRA SUPORTADOS

| Tipo de Dobra | Painéis | Configuração Geométrica |
|--------------|---------|------------------------|
| Dobra Simples (Double-fold) | 2 | Cada painel = metade |
| Tri-fold / Dobra em Z | 3 | Painel central menor |
| Dobra em Cruz (Gate-fold) | 4 | Painéis externos abrem para dentro |
| Dobra Acordeão (Accordion) | 4-8 | Alternância de dobras opostas |
| Dobra Janela (Roll-fold) | 4-6 | Painéis internos progressivamente menores |

---

## CHECKLIST DE VALIDAÇÃO

### V-01 — Detecção de Linhas de Vinco/Dobra
```bash
# Buscar camadas com nomenclatura de vinco
gs -dBATCH -dNOPAUSE -sDEVICE=nullpage -dPDFINFO "<file_path>" 2>&1 | \
   grep -iE "(vinco|dobra|fold|crease|score|perf)"
```
**Erro:** `E001_NO_FOLD_MARKS` se arquivo > 1 painel sem marcas de dobra detectadas

### V-02 — Compensação de Vinco (Creep Compensation)
```python
import fitz
doc = fitz.open(file_path)

# Em folders, cada painel é uma "página" ou seção identificável
# Painéis internos devem ser MENORES que externos em dobras roll/gate
page_widths = []
for page in doc:
    page_widths.append(page.mediabox.width * 25.4 / 72)  # em mm

# Para dobra simples (2 painéis): devem ser iguais
# Para tri-fold (3 painéis): painel central = externo - 2mm a 3mm
# Para gate-fold (4 painéis): os 2 centrais = (total/2 - 2mm) cada

if len(page_widths) == 3:
    # Tri-fold: painel central deve ser ~2mm menor
    diff = page_widths[0] - page_widths[1]  # Painel externo - central
    if diff < 1.5 or diff > 3.5:
        raise Error("E002_CREEP_COMPENSATION_MISSING")
```
**Erro crítico:** `E002_CREEP_COMPENSATION_MISSING` — painéis internos sem redução

### V-03 — Safety Zone em Vincos
```python
# Nenhum elemento importante pode estar a menos de 5mm de qualquer linha de vinco
# Verificar via artbox vs posições dos painéis

vinco_positions = detectar_posicoes_vinco(doc)  # Extrair de crop/bleed boxes
for vinco_x in vinco_positions:
    # Verificar que artbox.x0 está a ≥ 5mm do vinco
    safety_mm = abs(artbox.x0_mm - vinco_x_mm)
    if safety_mm < 5.0:
        warnings.append({"code": "W001_CONTENT_NEAR_FOLD", "vinco_mm": vinco_x_mm,
                          "distancia_mm": safety_mm})
```
**Aviso:** `W001_CONTENT_NEAR_FOLD` se elemento a < 5mm do vinco  
**Erro:** `E003_CONTENT_CROSSING_FOLD` se elemento transpassar o vinco

### V-04 — Verificação de Gramatura vs Vinco Mecânico
```python
# Substratos > 150g OBRIGAM vinco mecânico prévio
# Esta informação vem do metadata do job ou campo do cliente
gramatura = job_metadata.get("gramatura_gsm", 0)

if gramatura > 150:
    vinco_indicado = verificar_indicacao_vinco(doc)
    if not vinco_indicado:
        raise Error("E004_MECHANICAL_SCORE_REQUIRED")
```
**Erro crítico:** `E004_MECHANICAL_SCORE_REQUIRED` — papel grosso sem vinco = rachaduras no coating

### V-05 — Verniz UV em Postais (Regra de Face)
```python
# Postais 250g-300g: verniz UV obrigatório no anverso
# PROIBIDO no reverso (bloqueia cola e escrita)
gramatura = job_metadata.get("gramatura_gsm", 0)

if 250 <= gramatura <= 300:
    # Detectar camadas de verniz
    verniz_layers = detectar_camadas_verniz(doc)
    
    if "anverso" not in verniz_layers:
        warnings.append("W002_UV_VARNISH_MISSING_FRONT")
    
    if "reverso" in verniz_layers:
        raise Error("E005_UV_VARNISH_ON_REVERSE")
```
**Erro:** `E005_UV_VARNISH_ON_REVERSE` — verniz no reverso impede colagem e escrita  
**Aviso:** `W002_UV_VARNISH_MISSING_FRONT`

### V-06 — Direção da Fibra (Grain Direction)
```python
# Dobras contra a fibra em papéis > 150g causam ruptura do coating (cracking)
# A dobra deve ser PARALELA à direção da fibra
# Fibra longa (Long Grain): fibras paralelas ao lado maior
# Fibra curta (Short Grain): fibras paralelas ao lado menor

# Regra: dobra em papel > 150g deve ser paralela à fibra
if gramatura > 150:
    orientacao_dobra = detectar_orientacao_dobra(doc)
    grain_direction = job_metadata.get("grain_direction", "unknown")
    
    if grain_direction == "long_grain" and orientacao_dobra == "landscape":
        pass  # OK
    elif grain_direction == "short_grain" and orientacao_dobra == "portrait":
        pass  # OK
    else:
        raise Error("E006_GRAIN_DIRECTION_MISMATCH")
```
**Erro crítico:** `E006_GRAIN_DIRECTION_MISMATCH` — ruptura garantida no coating

### V-07 — Espaço de Cor e TIL
```bash
exiftool -ColorSpaceName -fast2 "<file_path>"
```
**Erro crítico:** `E007_RGB_COLORSPACE`  
**TIL:** ≤ 330% para couchê, ≤ 280% para offset  
**Perfil:** FOGRA 39 (couchê) ou FOGRA 29 (offset)

### V-08 — Resolução e Sangria
- Resolução mínima: 300 DPI → `E008_LOW_RESOLUTION` se < 300
- Sangria por painel: 2mm a 3mm → `E009_MISSING_BLEED`
- Fontes embutidas: obrigatório → `E010_NON_EMBEDDED_FONTS`

---

## TABELA DE DIMENSÕES PADRÃO DE FOLDERS

| Produto | Tamanho Fechado | Tipo de Dobra |
|---------|----------------|---------------|
| Folder A4 Tri-fold | 210 x 99 mm (fechado) | Dobra em Z (3 painéis) |
| Folder A5 Simples | 148 x 210 mm (fechado) | Dobra simples |
| Postal | 148 x 105 mm | Sem dobra |
| Flyer DL | 99 x 210 mm | Sem dobra |
| Calendário de Mesa | 148 x 210 mm (dobrado) | Dobra em V |

---

## TABELA DE CÓDIGOS DE ERRO

| Código | Severidade | Descrição |
|--------|-----------|-----------|
| `E001_NO_FOLD_MARKS` | ERRO | Arquivo sem marcas de dobra |
| `E002_CREEP_COMPENSATION_MISSING` | CRÍTICO | Painéis internos sem redução para dobra |
| `E003_CONTENT_CROSSING_FOLD` | CRÍTICO | Elemento atravessa linha de vinco |
| `E004_MECHANICAL_SCORE_REQUIRED` | CRÍTICO | Papel >150g sem indicação de vinco mecânico |
| `E005_UV_VARNISH_ON_REVERSE` | CRÍTICO | Verniz UV no reverso do postal |
| `E006_GRAIN_DIRECTION_MISMATCH` | CRÍTICO | Dobra contra a fibra do papel |
| `E007_RGB_COLORSPACE` | CRÍTICO | RGB detectado no arquivo |
| `E008_LOW_RESOLUTION` | CRÍTICO | Resolução < 300 DPI |
| `E009_MISSING_BLEED` | CRÍTICO | Sangria ausente |
| `E010_NON_EMBEDDED_FONTS` | CRÍTICO | Fonte não embutida |
| `W001_CONTENT_NEAR_FOLD` | AVISO | Elemento a < 5mm do vinco |
| `W002_UV_VARNISH_MISSING_FRONT` | AVISO | Verniz UV ausente no anverso do postal |

---

## REGRAS DE OURO
1. A compensação de vinco não é opcional — é física, não é estética
2. Papel > 150g sem vinco mecânico = refugo garantido
3. Verniz UV no reverso = postal inutilizável
4. Timeout: **240 segundos**
5. Enviar para `queue:validador`
