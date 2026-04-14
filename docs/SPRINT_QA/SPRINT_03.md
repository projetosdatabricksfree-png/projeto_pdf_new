# Sprint 3 — Completeness
**Duration:** 2 weeks
**Goal:** Close the geometry, spot color, remaining overprint and Optional-Content-patch gaps so the engine reports against the full §4 surface for the 14 variants.
**Functional Areas:** GE, SP, OV (image overprint), OC (patches), SY-13 (OCG filter usage)
**Depends on:** Sprint 1 (variants, rounding), Sprint 2 (OC-02 decorator)

---

## Stories

### GE-02 — CropBox == MediaBox (±0.011mm, 3-decimal)
**As** the engine, **I must** verify on every page that `CropBox` equals `MediaBox` within ±0.011mm using path-rounding (3 decimal digits) per §4.3 + §3.15,
**So that** trim/bleed information isn't visually masked by a smaller CropBox at preview/imposition.

**Acceptance Criteria:**
- [ ] AC1: PDF page with CropBox = MediaBox → `OK`.
- [ ] AC2: PDF page with CropBox 1.0mm smaller than MediaBox → `ERRO`, codigo `E_CROPBOX_NEQ_MEDIABOX`, found="ΔX=1.000mm", expected="≤0.011mm".
- [ ] AC3: PDF page with CropBox absent → `OK` (defaults to MediaBox per PDF spec).
- [ ] AC4: 0.010mm difference → `OK` (within tolerance).

**Files to modify:** `geometry_checker.py`
**Logic change:** add CropBox vs MediaBox comparator using `gwg_round(_, "path")`.
**Unit tests:** 4 ACs.
**Effort:** S
**Severity:** Erro
**Dependencies:** SY-11

---

### GE-03 — TrimBox identical across pages; Rotate=0
**As** the engine, **I must** verify that all pages share an identical TrimBox (within tolerance) and `Rotate=0` per §4.4 / §4.5,
**So that** imposition tools don't ingest mixed orientations or sizes.

**Acceptance Criteria:**
- [ ] AC1: 4-page PDF with identical TrimBox + Rotate=0 on all → `OK`.
- [ ] AC2: 4-page PDF where page 3 has TrimBox 1mm wider → `ERRO`, codigo `E_TRIMBOX_INCONSISTENT`, found="page 3 differs by 1.000mm".
- [ ] AC3: 2-page PDF with Rotate=90 on page 2 → `ERRO`, codigo `E_PAGE_ROTATED`, found="page 2 Rotate=90".

**Files to modify:** `geometry_checker.py`
**Logic change:** iterate pages; cross-compare TrimBox; assert Rotate property.
**Unit tests:** 3 ACs.
**Effort:** S
**Severity:** Erro
**Dependencies:** SY-11

---

### GE-04 — No empty pages inside BleedBox/TrimBox
**As** the engine, **I must** flag pages where the content rendered inside BleedBox is empty per §4.6,
**So that** accidentally blank pages are caught before press.

**Acceptance Criteria:**
- [ ] AC1: 3-page PDF where page 2 has zero drawn content within BleedBox → `AVISO`, codigo `W_EMPTY_PAGE`, found="page 2".
- [ ] AC2: PDF with content present on every page → `OK`.

**Files to modify:** `geometry_checker.py`
**Logic change:** render each page region to 1-bit pixmap @ 24dpi; check non-zero pixel count.
**Unit tests:** 2 ACs.
**Effort:** M
**Severity:** Warning
**Dependencies:** none

---

### GE-05 — page_count == 1 for ad variants
**As** the engine, **I must** assert exactly 1 page when variant ∈ {`MagazineAds_*`, `NewspaperAds_*`} per §4.7 / §5.1–5.4,
**So that** ad-delivery jobs aren't multi-page (which the receiving system can't impose).

**Acceptance Criteria:**
- [ ] AC1: 2-page PDF, variant `MagazineAds_CMYK` → `ERRO`, codigo `E_PAGE_COUNT_INVALID`, found=2, expected=1.
- [ ] AC2: 1-page PDF, same variant → `OK`.
- [ ] AC3: 5-page PDF, variant `SheetCmyk_CMYK` → `OK` (rule does not apply).

**Files to modify:** `geometry_checker.py`
**Logic change:** variant-conditional check.
**Unit tests:** 3 ACs.
**Effort:** S
**Severity:** Erro
**Dependencies:** SY-10

---

### SP-02 — Spot color naming validation (§4.20)
**As** the engine, **I must** verify that every Separation/DeviceN colorant name is a valid UTF-8 token and is **not** "All" or "None" per §4.20,
**So that** colorant names route correctly in downstream RIPs.

**Acceptance Criteria:**
- [ ] AC1: Spot color named "All" → `ERRO`, codigo `E_SPOT_RESERVED_NAME`.
- [ ] AC2: Spot color with name containing invalid UTF-8 byte sequence → `ERRO`, codigo `E_SPOT_NAME_NOT_UTF8`.
- [ ] AC3: Spot color named "PANTONE 185 C" → `OK`.

**Files to modify:** `devicen_checker.py`
**Logic change:** for each Separation/DeviceN, decode name as UTF-8; reject reserved tokens.
**Unit tests:** 3 ACs + edge case "all" lowercase (still allowed; rule is exact match).
**Effort:** S
**Severity:** Erro
**Dependencies:** none

---

### SP-03 — Ambiguous Spot Color (§4.21)
**As** the engine, **I must** flag `ERRO` if the same spot color name appears with different alternate color spaces across pages per §4.21,
**So that** color management is unambiguous.

**Acceptance Criteria:**
- [ ] AC1: PDF with "PANTONE 185 C" using Lab on p.1 and DeviceCMYK on p.2 → `ERRO`, codigo `E_SPOT_AMBIGUOUS`.
- [ ] AC2: Same name + same alternate space across all pages → `OK`.

**Files to modify:** `devicen_checker.py`
**Logic change:** build `{name: set(alt_space_signature)}`; |set|>1 → ambiguous.
**Unit tests:** 2 ACs.
**Effort:** M
**Severity:** Erro
**Dependencies:** none

---

### SP-04 — Per-variant Max Spot Colors (§4.18)
**As** the engine, **I must** enforce per-variant spot color count limits per §4.18 / §5.x: MagazineAds=0, SheetCmyk=0, NewspaperAds=1, SheetSpot=2, WebSpot=2, others=0,
**So that** spot-color delivery routes are honored.

**Acceptance Criteria:**
- [ ] AC1: 3 spots in `SheetSpot_CMYK` → `ERRO`, found=3, expected=2.
- [ ] AC2: 2 spots in `SheetSpot_CMYK` → `OK`.
- [ ] AC3: 1 spot in `MagazineAds_CMYK` → `ERRO`, found=1, expected=0.

**Files to modify:** `devicen_checker.py`
**Logic change:** read `max_spot_colors` from variant config (SY-10).
**Unit tests:** 3 ACs across 3 variants.
**Effort:** S
**Severity:** Erro
**Dependencies:** SY-10, DELTA-06, DELTA-07

---

### OV-09 — CMYK images must NOT overprint CMYK objects (Ghent GWG 1.0)
**As** the engine, **I must** flag `ERRO` for any CMYK image XObject (including image masks) drawn with `OP=true` or `op=true`,
**So that** image overprint doesn't visually erase background CMYK content.

**Acceptance Criteria:**
- [ ] AC1: CMYK image drawn with `op=true` → `ERRO`, codigo `E_IMAGE_OVERPRINT`.
- [ ] AC2: CMYK image with `op=false OP=false` → `OK`.
- [ ] AC3: Grayscale image with `op=true` → `OK` (rule scoped to CMYK images).

**Files to modify:** `opm_checker.py`
**Logic change:** content-stream walker: when `Do` op references an XObject of subtype Image with CS DeviceCMYK or ICCBased(N=4), inspect current GS op/OP.
**Unit tests:** 3 ACs.
**Effort:** M
**Severity:** Erro
**Dependencies:** none

---

### OV-10 — DeviceN with all colorants = 0 (white) must not overprint (Ghent 19.2)
**As** the engine, **I must** flag `ERRO` if a DeviceN fill with all components 0.0 (rendering as white) is drawn with `op=true`,
**So that** "invisible white overprint" tricks are caught.

**Acceptance Criteria:**
- [ ] AC1: DeviceN [0,0,0,0] fill, `op=true` → `ERRO`, codigo `E_DEVICEN_WHITE_OVERPRINT`.
- [ ] AC2: Same fill `op=false` → `OK`.

**Files to modify:** `opm_checker.py` or `devicen_checker.py`
**Logic change:** detection of zero-tint DeviceN with overprint.
**Unit tests:** 2 ACs.
**Effort:** S
**Severity:** Erro
**Dependencies:** none

---

### SY-13 — OCG visibility filter applied to all checkers
**As** the engine, **I must** ensure all 11 RUNNERS use the OC-02 filter so hidden content is excluded from analysis,
**So that** §3.16 is honored project-wide.

**Acceptance Criteria:**
- [ ] AC1: Integration test with a 3-layer PDF (1 hidden RGB image, variant `SheetCmyk_CMYK`) returns `OK` for color check.
- [ ] AC2: Toggling layer ON in default config makes the same checker return `ERRO`.
- [ ] AC3: Code grep: every checker module imports `oc_filter.is_visible`.

**Files to modify:** all checker modules.
**Logic change:** thread `visible_filter` into each check loop.
**Unit tests:** integration (1) + grep gate (1).
**Effort:** M
**Severity:** Erro
**Dependencies:** OC-02

---

### OC-03 — Ghent OCG patches 15.0 / 15.1 / 15.2
**As** the engine, **I must** correctly process Ghent's OCCD (15.0), RBGroup (15.1), and OCMD (15.2) reference patches,
**So that** layered, radio-button-grouped, and membership-dict-controlled content is handled per spec.

**Acceptance Criteria:**
- [ ] AC1: Ghent patch 15.0 PDF → all checks pass with expected default-config visible content.
- [ ] AC2: Ghent patch 15.1 → only one of N radio-grouped layers is treated as visible.
- [ ] AC3: Ghent patch 15.2 → OCMD AND/OR/NOT logic resolved correctly.

**Files to modify:** `oc_filter.py`
**Logic change:** extend visibility resolver with RBGroups + OCMD logic.
**Unit tests:** 3 ACs (Ghent patches loaded from `tests/gwg_suite/patches/15_*`).
**Effort:** L
**Severity:** Erro
**Dependencies:** OC-02

---

## Sprint 3 Exit Gate (CI-verifiable)

1. `pytest tests/sprint3/geometry -v` — 4 stories pass.
2. `pytest tests/sprint3/spot -v` — 3 stories pass.
3. `pytest tests/sprint3/overprint -v` — OV-09, OV-10 pass.
4. `pytest tests/sprint3/oc_patches -v` — Ghent 15.x reference PDFs return expected verdict.
5. `pytest tests/sprint1 tests/sprint2 -v` — zero regressions.
