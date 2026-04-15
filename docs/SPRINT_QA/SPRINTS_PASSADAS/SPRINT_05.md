# Sprint 5 — Code Quality & Debt Clearance

**Duration:** 1 week
**Goal:** Achieve a "Zero Debt" state by resolving all 53 technical issues identified by the Sonar/Ruff audit across the project root. This ensures the codebase is industry-ready, maintainable, and free of logical bugs like undefined names.
**Functional Areas:** All modules (api, agentes, scripts, workers, tests)
**Depends on:** Sprint 1, 2, 3, 4

---

## Stories

### QA-01 — Critical Bug Fix: Undefined Name (F821)
**As** a developer, **I must** resolve the `F821 Undefined name Any` in `exiftool_reader.py`,
**So that** the metadata extraction doesn't crash during runtime due to missing type hints.

**Acceptance Criteria:**
- [x] AC1: Fix `F821` in `agentes/gerente/tools/exiftool_reader.py`.
- [ ] AC2: Verify via `ruff check agentes/gerente/tools/exiftool_reader.py`.

**Effort:** XS
**Severity:** Crítico

---

### QA-02 — Cleanup: Unused Imports & Variables (F401, F841)
**As** the engine, **I must** remove the 30 unused imports and 3 unused variables across the codebase,
**So that** memory footprint is minimized and code legibility is improved.

**Acceptance Criteria:**
- [x] AC1: Remove `F401` issues in `scripts/`, `tests/`, and `workers/tasks.py`.
- [x] AC2: Remove `F841` unused variables in `app/api/routes_jobs.py` and `tests/test_api.py`.

**Effort:** S
**Severity:** Baixo

---

### QA-03 — Legibility: Multiple Statements on One Line (E701)
**As** the engine, **I must** refactor one-liners into proper PEP8 blocks in `richblack_detector.py`, `hairline_detector.py`, and `pdf_generator.py`,
**So that** the code follows industry-standard formatting.

**Acceptance Criteria:**
- [x] AC1: Fix `E701` in all identified files.
- [ ] AC2: Verify with `ruff check`.

**Effort:** S
**Severity:** Médio

---

### QA-04 — Syntax: Extraneous f-strings (F541)
**As** a developer, **I must** remove the `f` prefix from strings that don't contain placeholders in `certificador_gwg.py`, `diagnostico_gwg.py`, and `tasks.py`,
**So that** the code reflects intentional string formatting.

**Acceptance Criteria:**
- [x] AC1: Fix all 6 `F541` occurrences.

**Effort:** XS
**Severity:** Baixo

---

### QA-05 — Architecture: Module Level Imports (E402)
**As** a developer, **I must** review the 9 occurrences of `E402` and either move them to the top or explicitly mark them as intentional (e.g., `# noqa: E402`),
**So that** the module loading sequence is predictable.

**Acceptance Criteria:**
- [x] AC1: Move imports where possible (e.g., `app/main.py`).
- [x] AC2: Annotate intentional lazy-imports in `hairline_detector.py` and `workers/tasks.py`.

**Effort:** S
**Severity:** Médio (Arquitetura)

---

## Sprint 5 Exit Gate

1. `docker exec projeto_validador-worker-1 ruff check /app/` returns **0 errors**.
2. `pytest tests/` - full regression pass with Zero Debts.
3. SonarQube / local quality dashboard reflects **Grade A**.
