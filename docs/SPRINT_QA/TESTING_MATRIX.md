# Testing Matrix — GWG2015 + PDF/X-4 Compliance Engine

Legend: ✅ required · ⬜ not required · 🅖 = synthesized PDF (no Ghent patch exists)

| Check ID | Sprint | Unit | Integration | E2E (Ghent 5.0 patch) | CI Gate (blocks merge?) | Ghent patch / fixture |
|---|---|---|---|---|---|---|
| **GE-01** | S1 (partial) | ✅ | ⬜ | ⬜ 🅖 | Y | `tests/fixtures/userunit_*.pdf` |
| GE-02 | S3 | ✅ | ✅ | ⬜ 🅖 | Y | `cropbox_eq_mediabox.pdf` |
| GE-03 | S3 | ✅ | ✅ | ⬜ 🅖 | Y | `mixed_trimbox_4p.pdf` |
| GE-04 | S3 | ✅ | ⬜ | ⬜ 🅖 | N (warning) | `empty_page_2of3.pdf` |
| GE-05 | S3 | ✅ | ⬜ | ⬜ 🅖 | Y | `magazine_2pages.pdf` |
| **CO-01 (TAC)** | S1 | ✅ | ✅ | Ghent 11.x (TAC patches) | Y | `gwg_suite/patches/11_*` |
| CO-02 | S1 (var) | ✅ | ✅ | Ghent 7.x | Y | `gwg_suite/patches/07_*` |
| CO-03 | S2 | ✅ (10 rows) | ✅ | Ghent 8.x | Y | `gwg_suite/patches/08_*` |
| CO-04 | S4 (TR-01/02) | ✅ | ✅ | Ghent 16.x | Y | `gwg_suite/patches/16_*` |
| **OV-01..03** (existing) | done | ✅ | ✅ | Ghent 1.0/1.1/19.2 | Y | `gwg_suite/patches/01_*`, `19_2_*` |
| OV-04 | S2 | ✅ | ✅ | ⬜ 🅖 | Y | `black_text_8pt_no_op.pdf` |
| OV-05 | S2 | ✅ | ⬜ | ⬜ 🅖 | Y | `black_text_devicegray.pdf` |
| OV-06 | S2 | ✅ | ✅ | ⬜ 🅖 | Y | `thin_black_path_no_op.pdf` |
| OV-07 | S2 | ✅ | ⬜ | ⬜ 🅖 | Y | `thin_black_devicegray.pdf` |
| OV-09 | S3 | ✅ | ✅ | Ghent 1.0 | Y | `gwg_suite/patches/01_0_*` |
| OV-10 | S3 | ✅ | ⬜ | Ghent 19.2 | Y | `gwg_suite/patches/19_2_*` |
| **FO-01..02** (existing) | done | ✅ | ✅ | Ghent 9.0 | Y | `gwg_suite/patches/09_0_*` |
| FO-03 | S4 | ✅ | ✅ | Ghent 9.1 | Y | `gwg_suite/patches/09_1_*` |
| FO-04 | S4 | ✅ | ⬜ | ⬜ 🅖 | N (warning) | `text_8pt_magazine.pdf` |
| FO-05 | post-MVP | — | — | — | — | — |
| **IM-01** | S1 (DELTA-04/05) | ✅ | ✅ | ⬜ 🅖 | Y | `image_148ppi_magazine.pdf` |
| IM-02 | S1 (var) | ✅ | ⬜ | ⬜ 🅖 | Y | `image_548ppi_1bit.pdf` |
| IM-03 | S4 | ✅ | ✅ | Ghent 17.0/17.3 | Y | `gwg_suite/patches/17_*` |
| IM-04 | S4 | ✅ | ✅ | Ghent 18.x | Y | `gwg_suite/patches/18_*` |
| **SP-01** (existing) | done | ✅ | ⬜ | Ghent 14.0 | Y | `gwg_suite/patches/14_0_*` |
| SP-02 | S3 | ✅ | ⬜ | ⬜ 🅖 | Y | `spot_named_All.pdf` |
| SP-03 | S3 | ✅ | ✅ | ⬜ 🅖 | Y | `spot_ambiguous_2pages.pdf` |
| SP-04 | S3 | ✅ | ✅ | ⬜ 🅖 | Y | `3spots_in_sheetspot.pdf` |
| SP-05 | post-MVP | — | — | — | — | — |
| **TR-01** | S4 | ✅ | ✅ | Ghent 16.x | Y | `gwg_suite/patches/16_0_*` |
| TR-02 | S4 | ✅ | ✅ | Ghent 16.x | Y | `gwg_suite/patches/16_1_*` |
| TR-03 | S4 | ✅ | ⬜ | Ghent 16.x | N (warning) | `gwg_suite/patches/16_2_*` |
| **IC-01..03** (existing) | done | ✅ | ✅ | Ghent 12.x | Y | `gwg_suite/patches/12_*` |
| IC-04 | S4 | ✅ | ⬜ | ⬜ 🅖 | Y | `outputintent_corrupt.pdf` |
| IC-05 | S4 | ✅ | ⬜ | ⬜ 🅖 | Y | `outputintent_2_divergent.pdf` |
| **OC-01** | S2 | ✅ | ⬜ | ⬜ 🅖 | Y | `oc_with_configs.pdf` |
| OC-02 | S2 | ✅ | ✅ | Ghent 15.0 | Y | `gwg_suite/patches/15_0_*` |
| OC-03 | S3 | ✅ | ✅ | Ghent 15.0/15.1/15.2 | Y | `gwg_suite/patches/15_*` |
| **LW-01** (existing) | done | ✅ | ⬜ | ⬜ 🅖 | Y | `hairline_0.2pt.pdf` |
| LW-02 | S4 | ✅ | ✅ | Ghent 6.x (line patches) | Y | `gwg_suite/patches/06_*` |
| **SH-01** | S4 | ✅ | ✅ | Ghent 6.0/6.1 | Y | `gwg_suite/patches/06_0_*`, `06_1_*` |
| **SY-01..07** (system, existing) | done | ✅ | ✅ | n/a | Y | n/a |
| SY-04 | S4 | ✅ | ✅ | n/a | Y | docker integration |
| SY-08 (TAC sliding window) | S1 | ✅ (parity GPU/CPU) | ✅ (perf) | Ghent 11.x | Y | `gwg_suite/patches/11_*` |
| SY-10 (14 variants) | S1 | ✅ | ✅ | n/a | Y | unit + fixtures one per variant |
| SY-11 (rounding) | S1 | ✅ | ⬜ | n/a | Y | unit only |
| SY-13 (OCG filter universal) | S3 | ⬜ | ✅ (3-layer) | Ghent 15.0 | Y | `gwg_suite/patches/15_0_*` |

---

## Notes

- **🅖 (synthesized)** = no Ghent Output Suite 5.0 patch directly exists; team must produce a minimal synthetic PDF (target ≤ 4KB). All listed in `tests/fixtures/`.
- **CI Gate Y/N** column: `Y` = checker failure blocks merge to `main`. `N` = warning surfaces in CI report but does not block.
- **Ghent patch numbering** follows `GhentPDFOutputSuite50_ReadMes.pdf` ToC.
- **Performance tests** (TAC sliding window, image resolution scan) live in `tests/perf/` and run nightly, not on every PR.
- **Regression bundle** for DELTA-01..08 lives in `tests/sprint1/regression/` and runs on every PR (target < 30s total).
