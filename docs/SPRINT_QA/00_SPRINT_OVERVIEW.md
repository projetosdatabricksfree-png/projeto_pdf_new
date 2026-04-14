# Sprint Overview — GWG2015 + PDF/X-4 MVP Compliance Engine

**Scope:** 28 pending GWG checks + 9 partial + 8 DELTA fixes + 6 system items, organized into **4 two-week sprints**.
**Target MVP exit:** Engine produces results numerically identical to the GWG2015 specification for all 14 variants.

---

## Sprint Map

| Sprint | Duration | Goal | Items Covered | Exit Criterion |
|---|---|---|---|---|
| **S1 — Foundation** | 2 weeks | Correct the numeric/algorithmic core so every downstream check operates on valid thresholds and a compliant TAC engine. | DELTA-01..08, SY-08, SY-10, SY-11 | CI: regression suite of 8 reference PDFs (one per DELTA) passes; TAC sliding-window benchmark < 3s CPU / < 800ms GPU on 1-page A4 @300dpi; all 14 variant profiles loaded and selected by `profile_matcher.detect_variant()`. |
| **S2 — Critical Missing Checks** | 2 weeks | Implement the legally/visually high-impact checks that are entirely absent today. | OV-04, OV-05, OV-06, OV-07, CO-03, OC-01, OC-02 | CI: all OV-0x synthetic PDFs flagged correctly; CO-03 matrix of 10 prohibited combos returns expected verdict; OC-02 decorator applied to all 9 checkers and verified by integration test. |
| **S3 — Completeness** | 2 weeks | Close geometry + spot + remaining overprint + OC patches gaps. | GE-02..05, SP-02, SP-03, SP-04, OV-09, OV-10, SY-13, OC-03 | CI: Ghent 15.x patches return expected verdict; spot color counter respects per-variant limit; geometry tolerance enforced at ±0.011mm. |
| **S4 — Refinement & Edge Cases** | 2 weeks | Resolve transparency CS, image masks, ICC validation, CTM line width, shadings, sandbox isolation. | IM-03, IM-04, TR-01, TR-02, TR-03, IC-04, IC-05, LW-02, FO-03, FO-04, SH-01, SY-04 | CI: full Ghent PDF Output Suite 5.0 reference run produces a green report ≥ 95%; ipybox container executes a compliance script in isolation. |

Total: **4 sprints / 8 weeks / 38 stories**.

---

## Prioritization Rationale

1. **DELTA fixes ship first.** Every result emitted today by `profile_matcher.py` and `_check_tac_vips_turbo()` is numerically wrong for at least 3 of 4 currently-supported variants. Until corrected, every other check builds on a poisoned baseline — a "passed" report is meaningless. Sprint 1 also includes SY-10 (full 14-variant mapping) and SY-11 (rounding rules) because every numeric check downstream uses these constants.
2. **TAC sliding-window (SY-08) is in S1, not deferred.** Current `pyvips` global-max approach is not just a numeric bug — it is the wrong algorithm. GWG §4.22 requires *mean over any 15mm² square*. Fixing thresholds without fixing the algorithm would still produce wrong verdicts. This is an algorithmic rewrite, hence why it is sized XL.
3. **OV-04..07 (mandatory overprint) lead Sprint 2.** These are responsible for the most common real-world misregistration complaints in offset printing (small black text knocking out CMYK). Zero implementation today.
4. **OC-02 lands in Sprint 2 as a foundational decorator.** §3.16 mandates that *all* checkers operate only on visible (default-config) content. Implementing it later would require revisiting every checker — costlier.
5. **Refinement checks (S4) deferred** because they are statistically rarer (JPEG2000, soft masks, CTM-line-width edge cases) and have lower customer-visible blast radius.

---

## Risk Register

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | TAC sliding-window rewrite blows performance budget on multi-page PDFs (>50 pages @300dpi) | High | High — could regress existing OK throughput | Build benchmark harness in S1 day 1; profile pyvips integral-image approach (`vips.linear` + `vips.morph`); have CPU and GPU code paths; fallback to tile-based parallel processing |
| R2 | OC-02 decorator breaks existing checkers that assume "all content is visible" | Medium | High — silent regression on any PDF using layers | Add OC-fixture integration test with a 3-layer PDF before refactor; require all 9 checkers' tests to be re-run after decorator merge |
| R3 | Variant detection (SY-10) ambiguity — many real PDFs declare no GTS_PDFX variant explicitly | High | Medium | Explicit fallback chain: OutputIntent → metadata → user-supplied profile; emit `W_VARIANT_AMBIGUOUS` instead of guessing |
| R4 | Effective line width (LW-02) requires CTM tracking through nested `q/Q` graphics state — non-trivial in PyMuPDF | Medium | Medium | Spike in S1 (4h) to validate `page.get_drawings()` exposes CTM; if not, plan parser-level workaround for S4 |
| R5 | Ghent Output Suite 5.0 reference PDFs may include patches the engine isn't designed to handle (e.g., OPI references) | Medium | Low | Flag unsupported patches as `SKIP` rather than fail; track in BACKLOG_POST_MVP |

---

## Definition of Done (applies to every story, every sprint)

- [ ] All Acceptance Criteria pass in CI (no manual verification)
- [ ] Unit tests use **literal GWG2015 spec values** as inputs/expected outputs (no mocked thresholds, no magic numbers without `# §4.x` comment)
- [ ] No regression: full pre-existing test suite (`pytest tests/ -v`) passes
- [ ] Performance budget met (where stated in the story)
- [ ] PR reviewed by a second engineer with prepress domain awareness
- [ ] Checker emits structured result with `codigo`, `status`, `found_value`, `expected_value`, `meta` keys (matches `_normalize()` contract in `run_full_suite.py`)
- [ ] Logged via `progress_bus.update_stage()` so the frontend stage tracker reflects the new check
- [ ] If the check has a Ghent Suite 5.0 patch counterpart, the patch is added to `tests/gwg_suite/` and asserted

---

## Technical Debt Deferred Post-MVP (with rationale)

| Item | Why deferred |
|---|---|
| FO-05 (Rich Black ratios per variant) | Already partial; §4.15 ratio table is per-variant and intersects FO-04 work — bundle into v1.1 for atomic per-variant text quality release |
| SP-05 (DeviceN >1 non-process colorant) | Niche; affects packaging only, which is not in the 14-variant MVP scope |
| Multi-language colorant naming normalization | §4.20 requires UTF-8 token validation; multi-lingual print shops are post-MVP |
| Real OPI / DeviceN with NChannel image data | Out of scope of GWG2015 for press jobs |
| Streaming TAC over very large posters (> 1m × 1m) | MVP target is up to A2 @300dpi; oversize tile-stream support → v1.2 |

See `BACKLOG_POST_MVP.md` for the full deferred list with effort estimates.
