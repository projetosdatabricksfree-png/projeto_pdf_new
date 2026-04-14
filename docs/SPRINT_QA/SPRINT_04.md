# Sprint 4 — Refinement & Edge Cases
**Duration:** 2 weeks
**Goal:** Resolve transparency CS rules, image-mask edge cases, ICC profile validation, CTM-derived line width, OpenType + per-variant text size, shading patterns, and ipybox sandbox isolation — bringing the engine to a green Ghent Output Suite 5.0 reference run.
**Functional Areas:** IM, TR, IC, LW, FO, SH, SY-04
**Depends on:** Sprint 1, 2, 3

---

## Stories

### IM-03 — JPEG2000 image policy (§4.28 + Ghent 17.0/17.3)
**As** the engine, **I must** flag JPEG2000 (`/JPXDecode`) images per §4.28 — prohibited in PDF/X-4 Classic; permitted in PDF/X-4 only when bit depth ≤ 8 and no advanced features (multiple layers/regions),
**So that** RIP compatibility is preserved.

**Acceptance Criteria:**
- [x] AC1: JPEG2000 image, PDF/X-4 Classic delivery → `ERRO`, codigo `E_JPEG2000_FORBIDDEN`.
- [x] AC2: JPEG2000 image with bit depth 16, PDF/X-4 → `ERRO`.
- [x] AC3: JPEG2000 image, 8-bit, single layer, PDF/X-4 → `OK`.

**Files to modify:** `compression_checker.py`
**Logic change:** detect `/JPXDecode`, parse JP2 codestream header for bit depth + layers; gate by delivery method (Classic vs 2015).
**Unit tests:** 3 ACs.
**Effort:** M
**Severity:** Erro
**Dependencies:** CO-03 (delivery-method context)

---

### IM-04 — Image masks & soft-mask CS (Ghent 18.x)
**As** the engine, **I must** verify that 1-bit image masks use a valid CS and soft-mask images do not reference prohibited color spaces per Ghent 18.x,
**So that** transparency masking renders consistently.

**Acceptance Criteria:**
- [x] AC1: 1-bit ImageMask referencing DeviceRGB current color → `ERRO` if variant is CMYK-only.
- [x] AC2: SMask with luminosity image in DeviceRGB → `ERRO`, codigo `E_SMASK_RGB`.
- [x] AC3: SMask in DeviceGray → `OK`.

**Files to modify:** `compression_checker.py`, `transparency_checker.py`
**Logic change:** ImageMask / SMask detection + CS validation against variant matrix.
**Unit tests:** 3 ACs.
**Effort:** M
**Severity:** Erro
**Dependencies:** SY-10, CO-03

---

### TR-01 — Transparency group CS = DeviceCMYK (§4.25)
**As** the engine, **I must** flag `ERRO` when a transparency group dict's `CS` key is not `DeviceCMYK` (or absent) per §4.25,
**So that** blend space is unambiguous and CMYK.

**Acceptance Criteria:**
- [x] AC1: Page with Group dict missing `CS` → `ERRO`, codigo `E_TGROUP_CS_MISSING`.
- [x] AC2: Page with Group `CS=DeviceRGB` → `ERRO`, codigo `E_TGROUP_CS_RGB`.
- [x] AC3: Page with Group `CS=DeviceCMYK` → `OK`.

**Files to modify:** `transparency_checker.py`
**Logic change:** inspect `page.Group.CS`.
**Unit tests:** 3 ACs.
**Effort:** S
**Severity:** Erro
**Dependencies:** none

---

### TR-02 — Soft-mask Luminosity G dict CS (§4.25)
**As** the engine, **I must** flag `ERRO` when a soft mask of type Luminosity has a `G` dict whose CS ∉ {DeviceCMYK, DeviceGray} per §4.25,
**So that** luminosity masks blend in compliant space.

**Acceptance Criteria:**
- [x] AC1: SMask Luminosity with `G.CS = DeviceRGB` → `ERRO`.
- [x] AC2: SMask Luminosity with `G.CS = DeviceGray` → `OK`.
- [x] AC3: SMask Alpha (no G dict CS rule) → not subject.

**Files to modify:** `transparency_checker.py`
**Logic change:** SMask traversal.
**Unit tests:** 3 ACs.
**Effort:** S
**Severity:** Erro
**Dependencies:** none

---

### TR-03 — SMask Luminosity referencing objects outside group (Ghent 16.x)
**As** the engine, **I must** flag `AVISO` when a Luminosity SMask references content drawn outside its parent transparency group,
**So that** unpredictable rendering across RIPs is surfaced.

**Acceptance Criteria:**
- [x] AC1: Ghent 16.x out-of-group SMask patch → `AVISO`, codigo `W_SMASK_OUT_OF_GROUP`.
- [x] AC2: In-group SMask → `OK`.

**Files to modify:** `transparency_checker.py`
**Logic change:** scope analysis on SMask `G` content references.
**Unit tests:** 2 ACs (Ghent patches).
**Effort:** M
**Severity:** Warning
**Dependencies:** none

---

### IC-04 — OutputIntent ICC profile is parseable (§4.30)
**As** the engine, **I must** validate that `OutputIntent.DestOutputProfile` is a parseable ICC profile per §4.30,
**So that** corrupt or non-ICC blobs are caught early.

**Acceptance Criteria:**
- [x] AC1: Valid ICC v2 CMYK profile → `OK`.
- [x] AC2: Truncated profile (first 100 bytes only) → `ERRO`, codigo `E_OUTPUTINTENT_INVALID`.
- [x] AC3: Wrong profile colorspace (RGB instead of CMYK) → `ERRO`, codigo `E_OUTPUTINTENT_NOT_CMYK`.

**Files to modify:** `icc_checker.py`
**Logic change:** parse ICC header (128 bytes); validate signature `acsp` and color space `CMYK`.
**Unit tests:** 3 ACs.
**Effort:** S
**Severity:** Erro
**Dependencies:** none

---

### IC-05 — Multiple OutputIntents must be identical (§4.30)
**As** the engine, **I must** verify all OutputIntent profiles in the document are byte-identical when more than one exists per §4.30,
**So that** ambiguous color targets are rejected.

**Acceptance Criteria:**
- [x] AC1: 2 OutputIntents with identical profile bytes → `OK`.
- [x] AC2: 2 OutputIntents with different profile bytes → `ERRO`, codigo `E_OUTPUTINTENT_DIVERGENT`.

**Files to modify:** `icc_checker.py`
**Logic change:** SHA256 each profile; assert single hash.
**Unit tests:** 2 ACs.
**Effort:** S
**Severity:** Erro
**Dependencies:** IC-04

---

### LW-02 — Effective line width via CTM (§3.12)
**As** the engine, **I must** compute effective line width as `linewidth × min(|sx|, |sy|)` of the current CTM (and for visually-linear rectangles, `min(height, width) × CTM_scale`) per §3.12,
**So that** scaled-down strokes are correctly evaluated against thresholds.

**Acceptance Criteria:**
- [x] AC1: Stroke with linewidth=1pt under CTM scale 0.25 → effective 0.25pt → triggers hairline check.
- [x] AC2: Rectangular path filled+stroked same color, w=2pt h=0.5pt under CTM 1.0 → effective width = 0.5pt → triggers thin-path check (OV-06 trigger).
- [x] AC3: Stroke 3pt under CTM 1.0 → effective 3pt → no trigger.

**Files to modify:** `font_checker.check_hairlines`, `opm_checker.py`
**Logic change:** central helper `effective_line_width(linewidth, ctm) -> float` with rectangle visual-line heuristic.
**Unit tests:** 3 ACs + 1 nested `q/Q` graphics-state stack test.
**Effort:** L
**Severity:** Erro
**Dependencies:** SY-11

---

### FO-03 — OpenType (CFF + TrueType) embedding (§4.1 + Ghent 9.1)
**As** the engine, **I must** verify all OpenType fonts (subtype Type0 with CFF or TrueType backing) are fully embedded with valid font programs per §4.1 + Ghent 9.1,
**So that** RIPs render text consistently.

**Acceptance Criteria:**
- [x] AC1: PDF with embedded OpenType-CFF font → `OK`.
- [x] AC2: PDF with referenced-but-not-embedded OpenType → `ERRO`, codigo `E_FONT_NOT_EMBEDDED`.
- [x] AC3: PDF with embedded OpenType missing FontFile3 stream → `ERRO`.

**Files to modify:** `font_checker.py`
**Logic change:** check `FontDescriptor.FontFile3` presence + stream non-empty.
**Unit tests:** 3 ACs (Ghent 9.1 patch).
**Effort:** M
**Severity:** Erro
**Dependencies:** none

---

### FO-04 — Per-variant minimum text size (§4.16)
**As** the engine, **I must** apply minimum text size per variant: Magazine/WebCmyk ≥ 9.0pt, Newspaper/WebCmykNews ≥ 10.0pt, SheetCmyk ≥ 8.0pt per §4.16,
**So that** small text isn't allowed where a variant's print process would render it illegibly.

**Acceptance Criteria:**
- [x] AC1: 8pt text in `MagazineAds_CMYK` → `AVISO`, codigo `W_TEXT_TOO_SMALL`, found=8.0, expected="≥9.0".
- [x] AC2: 10pt text in `NewspaperAds_CMYK` → `OK`.
- [x] AC3: 8pt text in `SheetCmyk_CMYK` → `OK`.

**Files to modify:** `font_checker.py`
**Logic change:** read `min_text_pt` from variant config (SY-10).
**Unit tests:** 3 ACs across 3 variants.
**Effort:** S
**Severity:** Warning
**Dependencies:** SY-10

---

### SH-01 — Shading patterns detected & not classified as 100% Black (§3.11 + Ghent 6.0/6.1)
**As** the engine, **I must** detect Shading Patterns (Type 2/3) and exclude them from "100% Black" overprint rules per §3.11,
**So that** smooth-shaded fills aren't false-positively flagged for missing overprint.

**Acceptance Criteria:**
- [x] AC1: Page with axial shading pattern fill → detected; OPM checks skip it.
- [x] AC2: Ghent 6.0/6.1 patches → `OK`.
- [x] AC3: Solid K=1.0 fill on same page still subject to overprint rules.

**Files to modify:** `opm_checker.py`
**Logic change:** content-stream walker recognizes `sh` operator and Pattern colorspace; tag those objects as exempt.
**Unit tests:** 3 ACs.
**Effort:** M
**Severity:** Erro (correctness — prevents false positives)
**Dependencies:** none

---

### SY-04 — ipybox sandbox isolation
**As** the engineering team, **we must** execute deep-script analysis (e.g., post-mortem PDF parsers, custom validation scripts) inside an `ipybox` Docker container with no host filesystem write access and a 60s wall clock,
**So that** untrusted PDFs cannot exfiltrate or persist data.

**Acceptance Criteria:**
- [x] AC1: `ipybox.run("import os; os.system('touch /host/x')")` cannot create `/host/x`.
- [x] AC2: Script exceeding 60s wall-clock is killed with `TIMEOUT` status.
- [x] AC3: Worker calls deep-script analysis exclusively through `ipybox.run()` (grep gate in CI).

**Files to modify:** `agentes/operarios/shared_tools/ipybox_runner.py` (new), `workers/tasks.py`
**Logic change:** Docker SDK wrapper; bind-mount only PDF read-only; pid limits; network=none.
**Unit tests:** 3 ACs (1 escape attempt, 1 timeout, 1 grep gate).
**Effort:** L
**Severity:** Referência (security)
**Dependencies:** none

---

## Sprint 4 Exit Gate (CI-verifiable)

1. `pytest tests/sprint4/ -v` — all 12 stories green.
2. `pytest tests/gwg_suite/ghent_full -v` — Ghent PDF Output Suite 5.0 reference report ≥ 95% green.
3. `pytest tests/sprint1 tests/sprint2 tests/sprint3 -v` — zero regressions.
4. `docker run --rm graphic-pro-ipybox python -c "import os; print(os.access('/host', os.W_OK))"` returns `False`.
