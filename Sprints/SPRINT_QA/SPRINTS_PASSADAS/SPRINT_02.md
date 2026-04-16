# Sprint 2 — Critical Missing Checks
**Duration:** 2 weeks
**Goal:** Implement the high-impact GWG2015 checks that have zero coverage today: mandatory-overprint for small black, 2015 Delivery Method color-space gates, and Optional Content foundation.
**Functional Areas:** OV (Overprint), CO (Color), OC (Optional Content)
**Depends on:** Sprint 1 (variant routing, rounding rules, TAC engine)

---

## Stories

### OV-04 — 100% Black text < 12pt MUST overprint
**As** the engine,
**I must** verify that every text-show operator with K=1.0 (C=M=Y=0) and `gwg_round(effective_font_size, "text") < 12.0` has `op=true` (fill overprint), `OP=true` (stroke overprint), and `OPM=1` in its ExtGState when color space is DeviceCMYK, per §4.10,
**So that** small black type doesn't knock out CMYK background and produce misregistration halos.

**Acceptance Criteria:**
- [x] AC1: PDF with 8pt text, K=1.0 in DeviceCMYK, `op=false` → `ERRO`, codigo `E_BLACK_TEXT_NO_OVERPRINT`, found="op=false @ 8.0pt", expected="op=true @ <12pt".
- [x] AC2: PDF with 14pt text, K=1.0, `op=false` → `OK` (above threshold).
- [x] AC3: PDF with 8pt text, K=1.0, `op=true OP=true OPM=1` → `OK`.
- [x] AC4: PDF with 8pt text, K=1.0, `op=true` but OPM=0 → `ERRO`, codigo `E_OPM_MISSING`.

**Files to modify:** `agentes/operarios/shared_tools/gwg/opm_checker.py`
**Logic change:** Walk content stream via PyMuPDF; for each `Tj`/`TJ` op, snapshot current GS (font size × CTM scale), color, ExtGState op/OP/OPM. Compare against per-variant `min_text_pt` (from SY-10) — defaults 12.0pt for §4.10 trigger.
**Unit tests:** 4 ACs above + 1 with K=0.99 (not "100% black") → not subject to rule.
**Effort:** L
**Severity:** Erro
**Dependencies:** SY-10, SY-11

---

### OV-05 — 100% Black text < 12pt MUST NOT use DeviceGray
**As** the engine, **I must** flag `ERRO` when text with K=1.0 and effective size < 12pt is set in DeviceGray color space per §4.11,
**So that** type intended as overprinting CMYK black isn't silently rendered as gray on-press.

**Acceptance Criteria:**
- [x] AC1: 8pt text, gray=0.0 (=K=1.0), color space DeviceGray → `ERRO`, codigo `E_BLACK_TEXT_DEVICEGRAY`.
- [x] AC2: Same text in DeviceCMYK → `OK` (handled by OV-04).
- [x] AC3: 14pt text in DeviceGray → `OK` (above threshold).

**Files to modify:** `opm_checker.py`
**Logic change:** colorspace inspection added to OV-04 walker.
**Unit tests:** 3 ACs.
**Effort:** S
**Severity:** Erro
**Dependencies:** OV-04

---

### OV-06 — 100% Black thin strokes/fills MUST overprint
**As** the engine, **I must** verify that any path with K=1.0 and `effective_line_width = gwg_round(linewidth × CTM_scale, "path") < 2.0pt` has `OP=true` (stroke), `op=true` (fill), and `OPM=1` if DeviceCMYK, per §4.12,
**So that** thin black rules and keylines don't knock out backgrounds.

**Acceptance Criteria:**
- [x] AC1: 0.5pt black stroke in DeviceCMYK with `OP=false` → `ERRO`, codigo `E_BLACK_THIN_NO_OVERPRINT`, found="OP=false @ 0.5pt".
- [x] AC2: 2.5pt stroke `OP=false` → `OK`.
- [x] AC3: 0.5pt stroke `OP=true OPM=1` → `OK`.
- [x] AC4: Path under CTM scale 0.5 with declared linewidth 3pt → effective 1.5pt → triggers rule.

**Files to modify:** `opm_checker.py`, depends on LW-02 spike (CTM access via `page.get_drawings()`)
**Logic change:** drawings walker; multiply linewidth by min(|sx|, |sy|) of CTM.
**Unit tests:** 4 ACs + 1 dashed-stroke edge case.
**Effort:** L
**Severity:** Erro
**Dependencies:** SY-11; partial overlap with LW-02 (S4)

---

### OV-07 — 100% Black thin paths MUST NOT use DeviceGray
**As** the engine, **I must** flag `ERRO` for any path with K=1.0, effective width < 2.0pt, in DeviceGray per §4.13.

**Acceptance Criteria:**
- [x] AC1: 0.5pt path, gray=0.0, DeviceGray → `ERRO`, codigo `E_BLACK_PATH_DEVICEGRAY`.
- [x] AC2: Same in DeviceCMYK → handled by OV-06.

**Files to modify:** `opm_checker.py`
**Logic change:** colorspace inspection on path walker.
**Unit tests:** 2 ACs.
**Effort:** S
**Severity:** Erro
**Dependencies:** OV-06

---

### CO-03 — 2015 Delivery Method color-space gate (§4.24)
**As** the engine, **I must** enforce, for `*_CMYK+RGB` variants, the 2015 Delivery Method prohibitions per §4.24:
- **Images:** no DeviceRGB, ICCbasedGray, CalGray, ICCbasedCMYK
- **Non-image content:** same as above + Lab
- **Spot/DeviceN alternate spaces:** no DeviceRGB, ICCbasedGray, CalGray, ICCbasedCMYK,

**So that** RGB delivery is permitted only where §4.24 explicitly allows it.

**Acceptance Criteria:**
- [x] AC1: PDF (variant `MagazineAds_CMYK+RGB`) with one DeviceRGB image → `OK` (RGB allowed for images? — see matrix; match exact spec text).
- [x] AC2: PDF with one DeviceRGB image in `MagazineAds_CMYK` (CMYK-only) → `ERRO`, codigo `E_RGB_IMAGE_FORBIDDEN`.
- [x] AC3: PDF with Lab non-image content under `*_CMYK+RGB` → `ERRO`.
- [x] AC4: PDF with spot color whose alternate is ICCbasedCMYK → `ERRO`.
- [x] AC5: 10-row matrix table in test file enumerates all combos with expected verdict (literal §4.24 text).

**Files to modify:** `color_checker.py`
**Logic change:** New `_check_delivery_method_2015(pdf, variant)`. Build a permission matrix `{(content_type, colorspace, variant_kind): allowed_bool}` literally from §4.24.
**Unit tests:** 10 rows of the matrix as parametrized tests.
**Effort:** L
**Severity:** Erro
**Dependencies:** SY-10

---

### OC-01 — OCProperties must not contain Configs key (§4.29)
**As** the engine, **I must** flag `ERRO` if the document catalog's OCProperties dict contains the `Configs` array per §4.29,
**So that** alternate visibility configs cannot hide non-conformant content from press operators.

**Acceptance Criteria:**
- [x] AC1: PDF with `OCProperties.Configs` present → `ERRO`, codigo `E_OC_CONFIGS_PRESENT`, found="Configs[3 entries]", expected="absent".
- [x] AC2: PDF with only `OCProperties.D` → `OK`.
- [x] AC3: PDF without OCProperties → `OK`.

**Files to modify:** new `agentes/operarios/shared_tools/gwg/optional_content_checker.py`; register in `run_full_suite.RUNNERS`.
**Logic change:** PyMuPDF `doc.pdf_catalog()` → resolve OCProperties → check key set.
**Unit tests:** 3 ACs.
**Effort:** S
**Severity:** Erro
**Dependencies:** none

---

### OC-02 — Optional Content visibility filter (§3.16) [foundation]
**As** the engine, **I must** apply OCG default-config (`D`) visibility filtering as a pre-processing decorator that all 9 checkers consume, per §3.16,
**So that** invisible/off-by-default layers are not analyzed and don't cause spurious errors.

**Acceptance Criteria:**
- [x] AC1: PDF with a hidden layer containing a 100% RGB image, variant `SheetCmyk_CMYK` → `OK` (hidden content excluded).
- [x] AC2: Same PDF after toggling layer to ON in default config → `ERRO` (content now visible).
- [x] AC3: All 9 RUNNERS in `run_full_suite.RUNNERS` accept and use a `visible_content_filter` argument (or equivalent decorator).
- [x] AC4: Integration test: 3-layer PDF (layer A=on, B=off, C=ON) → only A and C content is checked.

**Files to modify:** new `agentes/operarios/shared_tools/gwg/oc_filter.py`; thin wrapper in each checker; `run_full_suite.py` injects filter into invocation.
**Logic change:** Helper builds set of visible OCG ids from `OCProperties.D.ON / OFF`. Each checker consults filter when iterating page objects.
**Unit tests:** unit (visible-set computation: 4 cases) + integration (3-layer PDF).
**Effort:** L
**Severity:** Erro (foundational; affects all checks)
**Dependencies:** none, but OC-03 (S3) and SY-13 (S3) build on this.

---

## Sprint 2 Exit Gate (CI-verifiable)

1. `pytest tests/sprint2/overprint -v` — all 4 OV stories' synthetic PDFs return expected verdicts.
2. `pytest tests/sprint2/co_03_matrix.py -v` — full 10-row matrix passes.
3. `pytest tests/sprint2/oc_filter_integration.py -v` — 3-layer PDF integration test green.
4. Re-run `pytest tests/sprint1/` — zero regressions.
5. `grep -r "RUNNERS" agentes/operarios/shared_tools/gwg/run_full_suite.py` shows 11 entries (9 original + OC-01 + OC-02 wrapper).
