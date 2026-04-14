# Sprint 1 — Foundation
**Duration:** 2 weeks
**Goal:** Replace every numeric constant and the TAC algorithm in the engine with values and logic literally drawn from GWG2015, so all downstream checks operate on a compliant baseline.
**Functional Areas:** DELTA fixes, SY (System), TAC engine, variant routing
**Depends on:** none (foundational)

> [!IMPORTANT]
> **Status de Validação (Benchmark Ghent V50 — 2026-04-14):**
> - **SY-08 (TAC Window):** PENDENTE. O motor ainda reporta pico global de pixel, ignorando a janela de 15mm².
> - **SY-10 (Variant Mapping):** CONCLUÍDO. 14 variantes mapeadas e funcionais.
> - **DELTA-01/02/03:** CONCLUÍDO. Thresholds dinâmicos via perfis GWG.
> - **Messages:** PENDENTE. Falta tradução/humanização para códigos `G002`, `E_WHITE_OVERPRINT`, etc.

---

## Stories

### DELTA-01 — TAC threshold MagazineAds = 305%
**As** the GWG2015 compliance engine,
**I must** apply TAC limit = 305% (mean within any 15mm² square) for variants `MagazineAds_CMYK` and `MagazineAds_CMYK+RGB` per §4.22 / §5.1–5.2,
**So that** a job with TAC=306% in a 16mm² region is rejected and a job with TAC=305% in any region passes.

**Acceptance Criteria:**
- [x] AC1: Given a synthetic 1-page A4 PDF with a 20mm × 20mm patch at C=80 M=80 Y=80 K=70 (TAC=310%), when checked against `MagazineAds_CMYK`, then status = `ERRO`, `codigo = E_TAC_EXCEEDED`, `found_value = 310`, `expected_value = "≤305"`. (§4.22)
- [x] AC2: Given the same patch at C=76 M=76 Y=76 K=77 (TAC=305%), then status = `OK`.
- [x] AC3: Performance: check completes < 800ms on GPU, < 3s on CPU for a 1-page A4 @300dpi.

**Files to modify:** `agentes/operarios/shared_tools/gwg/profile_matcher.py`, `agentes/operarios/shared_tools/gwg/color_checker.py`
**Logic change:** Replace `"magazine_ads": {"tac_limit": 300, ...}` with the variant table (see SY-10). Threshold lookup must read from variant config, not a hardcoded literal in `_check_tac_vips_turbo`.
**Unit tests:** `test_tac_magazine_at_limit_passes`, `test_tac_magazine_above_limit_fails`, `test_tac_magazine_just_below_limit_passes` (all using literal §5.1 value 305).
**Effort:** S
**Severity:** Erro
**Dependencies:** SY-08 (sliding window), SY-10 (variant map)

**Delta Fix:**
- Current: `"magazine_ads": {"tac_limit": 300, ...}` flat global pixel max
- Correct: 305% mean inside 15mm² sliding window (§4.22, §5.1)
- Fix: parametrize threshold from variant config + use SY-08 windowed engine
- Regression risk: Medium (changes behavior for any current Magazine job)
- Regression test: synthetic PDF that previously failed at 301% must now pass; one at 306% must fail.

---

### DELTA-02 — TAC threshold Newspaper = 245%
**As** the engine, **I must** apply TAC ≤ 245% for `NewspaperAds_*` and `WebCmykNews_*` variants per §4.22 / §5.13–5.14,
**So that** newspaper jobs at 246% are rejected and at 245% pass.

**Acceptance Criteria:**
- [x] AC1: Given a 30mm patch at TAC=246%, variant `NewspaperAds_CMYK`, status = `ERRO`, found=246, expected="≤245".
- [x] AC2: TAC=245% returns `OK`.
- [x] AC3: Same performance budget as DELTA-01.

**Files to modify:** `profile_matcher.py`
**Logic change:** variant config: `"NewspaperAds_CMYK": {"tac_limit": 245, ...}`
**Unit tests:** 3 tests with literal 245 boundary.
**Effort:** S
**Severity:** Erro
**Dependencies:** SY-08, SY-10

**Delta Fix:**
- Current: 240%
- Correct: 245% (§5.13)
- Fix: variant config update
- Regression risk: Low (loosens threshold)
- Regression test: PDF at 243% previously failed → now passes; at 246% still fails.

---

### DELTA-03 — TAC threshold SheetCmyk = 320%
**As** the engine, **I must** apply TAC ≤ 320% for `SheetCmyk_*` per §4.22 / §5.7–5.8,
**So that** sheetfed jobs at 320% pass (currently false-positive).

**Acceptance Criteria:**
- [x] AC1: TAC=321% in a 15mm² region → `ERRO`, found=321, expected="≤320".
- [x] AC2: TAC=320% → `OK`.
- [x] AC3: A real-world reference PDF (`tests/fixtures/sheet_cmyk_at_310pct.pdf`) currently failing must now pass.

**Files to modify:** `profile_matcher.py`
**Logic change:** `"SheetCmyk_CMYK": {"tac_limit": 320, ...}`
**Unit tests:** boundary @ 320, 321, 319.
**Effort:** S
**Severity:** Erro
**Dependencies:** SY-08, SY-10

**Delta Fix:**
- Current: 300% (false positive on legitimate sheetfed jobs)
- Correct: 320% (§5.7)
- Fix: variant config update
- Regression risk: Low (loosens threshold; may unblock real customers)
- Regression test: 305%/310%/315% must now pass for SheetCmyk; 321% must still fail.

---

### DELTA-04 — Resolution Magazine: dual Error/Warning thresholds
**As** the engine, **I must** apply CT image resolution Error < 149ppi and Warning < 224ppi for `MagazineAds_*`/`SheetCmyk_*`/`WebCmyk_*` per §4.26 / §5.x,
**So that** marginal images (e.g., 200ppi) emit `AVISO` and only severely under-resolution images (e.g., 100ppi) emit `ERRO`.

**Acceptance Criteria:**
- [x] AC1: Image @ 148ppi, variant `MagazineAds_CMYK` → `ERRO`, found=148, expected="≥224 (warn) / ≥149 (err)".
- [x] AC2: Image @ 200ppi → `AVISO`, found=200, expected="≥224".
- [x] AC3: Image @ 224ppi → `OK`.
- [x] AC4: Image ≤16px in either dimension → `SKIP` regardless of ppi (§4.26 exception).

**Files to modify:** `compression_checker.py` (image inventory), new `image_resolution_checker.py` or extend existing
**Logic change:** lookup `(error_min_ppi, warn_min_ppi)` per variant; emit two-tier status.
**Unit tests:** 4 tests covering ERROR / WARN / OK / SKIP boundaries with literal 149/224/16.
**Effort:** M
**Severity:** Erro / Warning
**Dependencies:** SY-10, SY-11

**Delta Fix:**
- Current: single threshold 225ppi, no warn split
- Correct: Error < 149 · Warning < 224 (§4.26)
- Fix: dual-threshold function + 16px exception
- Regression risk: Medium
- Regression test: image @ 200ppi previously failed → now warns; @ 100ppi still fails.

---

### DELTA-05 — Resolution Newspaper: dual Error/Warning thresholds
**As** the engine, **I must** apply Error < 99ppi · Warning < 149ppi for `NewspaperAds_*` / `WebCmykNews_*` per §4.26,
**So that** newsprint jobs aren't rejected at 120ppi (which is acceptable as a warning).

**Acceptance Criteria:**
- [x] AC1: Image @ 98ppi, variant `NewspaperAds_CMYK` → `ERRO`, found=98, expected="≥149 (warn) / ≥99 (err)".
- [x] AC2: Image @ 120ppi → `AVISO`, found=120.
- [x] AC3: Image @ 149ppi → `OK`.

**Files to modify:** same as DELTA-04
**Logic change:** variant lookup
**Unit tests:** 3 boundary tests at literal 99 / 149.
**Effort:** S
**Severity:** Erro / Warning
**Dependencies:** DELTA-04 (shares implementation)

**Delta Fix:**
- Current: 150ppi single threshold
- Correct: Error < 99 · Warning < 149
- Fix: variant lookup
- Regression risk: Low
- Regression test: 120ppi newspaper image previously failed → now warns.

---

### DELTA-06 — Max Spot Colors SheetFed = 0
**As** the engine, **I must** report `ERRO` for any spot color in `SheetCmyk_*` / `MagazineAds_*` / `WebCmyk_*` (CMYK-only variants) per §4.18,
**So that** CMYK-only delivery routes don't silently accept Pantone separations.

**Acceptance Criteria:**
- [x] AC1: PDF with 1 spot color (PANTONE 185 C), variant `SheetCmyk_CMYK` → `ERRO`, codigo `E_SPOT_FORBIDDEN`, found=1, expected=0.
- [x] AC2: PDF with 0 spot colors, same variant → `OK`.
- [x] AC3: Same PDF with variant `SheetSpot_CMYK+RGB` → `OK` (allowed).

**Files to modify:** `devicen_checker.py`, `profile_matcher.py`
**Logic change:** variant config: `"max_spot_colors": 0` for all CMYK-only variants
**Unit tests:** 3 spot-count tests across 2 variants.
**Effort:** S
**Severity:** Erro
**Dependencies:** SY-10

**Delta Fix:**
- Current: SheetFed allows up to 2 spots (false negative)
- Correct: 0 (§4.18, §5.7)
- Fix: variant config
- Regression risk: Medium (will newly fail jobs that previously passed silently)
- Regression test: PDF with 1 spot in SheetCmyk previously OK → now ERRO.

---

### DELTA-07 — Max Spot Colors NewspaperAds = 1
**As** the engine, **I must** allow exactly 1 spot color in `NewspaperAds_CMYK` per §4.18 / §5.13,
**So that** the standard "spot black" newspaper layout passes.

**Acceptance Criteria:**
- [x] AC1: PDF with 1 spot, variant `NewspaperAds_CMYK` → `OK`.
- [x] AC2: PDF with 2 spots → `ERRO`, found=2, expected=1.

**Files to modify:** `profile_matcher.py`
**Logic change:** variant config
**Unit tests:** 2 boundary tests.
**Effort:** S
**Severity:** Erro
**Dependencies:** SY-10

**Delta Fix:**
- Current: 0 (false positive, blocks valid newspaper jobs)
- Correct: 1 (§5.13)
- Fix: variant config
- Regression risk: Low (loosens)
- Regression test: 1-spot newspaper PDF previously failed → now passes.

---

### SY-08 / DELTA-08 — TAC sliding-window engine (15mm²)
**As** the engine, **I must** compute TAC as the **mean** of (C+M+Y+K) inside any **15mm² (≈ 3.873mm × 3.873mm)** sliding square per §4.22, not as a per-pixel global maximum,
**So that** isolated single-pixel hot spots don't reject jobs and large areas of high coverage do.

**Acceptance Criteria:**
- [x] AC1: PDF with one rogue pixel @ TAC=400% surrounded by C=0 M=0 Y=0 K=0 → window mean ≪ limit → `OK`.
- [x] AC2: PDF with a 20mm × 20mm patch @ TAC=325% under SheetCmyk (limit 320) → `ERRO`, found=325, expected="≤320".
- [x] AC3: PDF with a 14mm × 14mm patch @ 325% (smaller than window) → window mean diluted by surrounding 0% → `OK`.
- [x] AC4: Performance: 1-page A4 @300dpi: < 3s CPU / < 800ms GPU.
- [x] AC5: Multi-page (10 pages A4 @300dpi): < 25s total parallel via billiard.Pool.

**Files to modify:** `agentes/operarios/shared_tools/gwg/color_checker.py` (`_check_tac_vips_turbo`)
**Logic change:**
```
1. Render page CMYK at 150dpi (target speed). Keep DPI = config-driven.
2. For each plane, run integral image (vips.recomb / boxcar) using a kernel of W mm in pixels.
3. Sum 4 planes → mean per window.
4. Find max(mean) across all windows.
5. Compare max(mean) to variant threshold.
```
Use libvips `boxcar` (separable rolling mean) → O(N) per plane regardless of window size.
**Unit tests:** 5 tests: hot-pixel, just-too-big patch, sub-window patch, multi-page parallelism, GPU vs CPU parity (results must match within ±0.5%).
**Effort:** XL
**Severity:** Erro
**Dependencies:** none (lands first; DELTA-01..03 build on this)

**Delta Fix:**
- Current: per-pixel global max (`vips.max`) — wrong algorithm
- Correct: rolling mean of summed CMYK planes inside any 15mm² window (§4.22)
- Fix: rewrite `_check_tac_vips_turbo` with boxcar; document GPU/CPU parity contract
- Regression risk: High (changes verdicts on every job)
- Regression test: full reference PDF set must be re-baselined; both directions (now-fail and now-pass) must be inspected.

---

### SY-10 — Full 14-variant mapping
**As** the engine, **I must** support the 14 GWG2015 variants (`MagazineAds_CMYK`, `MagazineAds_CMYK+RGB`, `NewspaperAds_CMYK`, `NewspaperAds_CMYK+RGB`, `SheetCmyk_CMYK`, `SheetCmyk_CMYK+RGB`, `SheetSpot_CMYK`, `SheetSpot_CMYK+RGB`, `WebCmyk_CMYK`, `WebCmyk_CMYK+RGB`, `WebSpot_CMYK`, `WebSpot_CMYK+RGB`, `WebCmykNews_CMYK`, `WebCmykNews_CMYK+RGB`) per §5.1–§5.14,
**So that** thresholds correctly route by job type.

**Acceptance Criteria:**
- [x] AC1: `profile_matcher.GWG_VARIANTS` exposes a dict with 14 keys, each holding `{tac_limit, image_resolution_error_ppi, image_resolution_warn_ppi, max_spot_colors, min_text_pt, rich_black_ratio_max, allow_rgb}` literally per §5.x.
- [x] AC2: `detect_variant(pdf_path) -> str` returns one of the 14 keys or raises with code `W_VARIANT_AMBIGUOUS`.
- [x] AC3: For an existing fixture currently classified as `sheetfed_offset`, `detect_variant` returns `SheetCmyk_CMYK`.

**Files to modify:** `profile_matcher.py`
**Logic change:** Build canonical table (literal copy of §5.1–§5.14). Detection chain: OutputIntent string → metadata `GTS_PDFX` → file naming convention → user override → ambiguous.
**Unit tests:** 14 entries × at least 1 detection test each; 1 ambiguity-fallback test.
**Effort:** L
**Severity:** Erro (engine-wide)
**Dependencies:** none

---

### SY-11 — GWG rounding rules §3.15
**As** the engine, **I must** round numeric values per §3.15 (Text = 1 decimal · Image = 0 decimals · Path = 3 decimals) before any comparison,
**So that** edge values like 11.95pt text are not falsely rejected against a 12.0pt threshold.

**Acceptance Criteria:**
- [x] AC1: `gwg_round(11.96, kind="text") == 12.0` → comparison `>= 12.0` succeeds.
- [x] AC2: `gwg_round(148.7, kind="image") == 149` → fails `>= 149` check.
- [x] AC3: `gwg_round(0.2495, kind="path") == 0.250` → fails `>= 0.250` check.
- [x] AC4: All existing checkers (font, image, hairline, geometry, line-width) call `gwg_round` before threshold comparisons.

**Files to modify:** new `agentes/operarios/shared_tools/gwg/rounding.py`; refactor `font_checker.py`, `compression_checker.py`, `geometry_checker.py`, `color_checker.py`.
**Logic change:** central helper `gwg_round(value: float, kind: Literal["text","image","path"]) -> float` using `decimal.ROUND_HALF_UP`.
**Unit tests:** 9 tests (3 per kind: just-below / exact / just-above boundary).
**Effort:** M
**Severity:** Erro (correctness foundation)
**Dependencies:** none — lands on day 1 of sprint.

---

## Sprint 1 Exit Gate (CI-verifiable)

1. `pytest tests/sprint1/regression -v` runs 8 reference PDFs (one per DELTA) → all green.
2. `pytest tests/sprint1/perf -v --benchmark-min-rounds=5` validates TAC ≤3s CPU / ≤800ms GPU.
3. `python -c "from profile_matcher import GWG_VARIANTS; assert len(GWG_VARIANTS) == 14"` returns 0.
4. Coverage on touched files ≥ 85%.
5. `pytest tests/ -v` (full suite) shows zero net regressions vs. pre-sprint baseline.
