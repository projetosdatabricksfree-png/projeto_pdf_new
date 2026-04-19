# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**PrintGuard** is a SaaS preflight and PDF auto-correction engine for digital print shops. It analyzes uploaded PDFs against configurable presets (product dimensions) and validation profiles (rule sets), reports findings (e.g., wrong color space, insufficient DPI), auto-applies safe fixes, and generates reports/previews.

The codebase is pure **C++20**, built with **CMake**, and uses **QPDF** as the PDF engine.

---

## Build

### System dependencies (Ubuntu/Debian)

```bash
sudo apt-get install build-essential cmake git pkg-config \
    libssl-dev nlohmann-json3-dev libqpdf-dev zlib1g-dev \
    libjpeg-dev libpq-dev libpqxx-dev liblcms2-dev mupdf-tools
```

### Debug build (standard workflow)

```bash
# First build (also fetches FetchContent deps: spdlog, cpp-httplib, Catch2, libpqxx)
cmake -S printguard -B printguard/build -DCMAKE_BUILD_TYPE=Debug
cmake --build printguard/build -j$(nproc)

# Or use the convenience script:
./printguard/scripts/setup.sh
```

### Release / Docker build

```bash
docker build -t printguard ./printguard
```

---

## Testing

Tests use **Catch2 v3**. The test binary is `unit_tests`.

```bash
# Build and run all tests
cmake --build printguard/build --target unit_tests
cd printguard/build && ctest --output-on-failure

# Run with coverage (for SonarQube)
cmake -S printguard -B printguard/build_sonar -DCMAKE_BUILD_TYPE=Debug -DPRINTGUARD_COVERAGE=ON
cmake --build printguard/build_sonar --target unit_tests
cd printguard/build_sonar && ctest --output-on-failure
gcovr -r . --sonarqube build_sonar/coverage.xml
```

Test sources are in `printguard/tests/unit/` and link `printguard_common`, `printguard_domain`, and `printguard_pdf` libraries.

---

## Running the Applications

Four binaries are produced under `printguard/build/apps/`:

| Binary | Purpose |
|---|---|
| `printguard-api` | HTTP API server (cpp-httplib, port configurable via env) |
| `printguard-worker` | Poll-based async job processor |
| `printguard-cli` | Local batch processor — no database required |
| `printguard-inspect` | Debug tool to dump a PDF's canonical model |

**CLI (no DB needed):**
```bash
./printguard/build/apps/cli/printguard-cli <input_dir> <corrected_dir> <report_dir> [preset_id] [profile_id]
```

**Inspect a PDF:**
```bash
./printguard/build/apps/inspect/printguard-inspect path/to/file.pdf
```

**API + Worker (requires PostgreSQL):**
```bash
export PG_CONN_STR="host=localhost dbname=printguard user=pg password=pg"
export STORAGE_ROOT="./storage_data"
export PRESETS_PATH="./printguard/config/presets"
export PROFILES_PATH="./printguard/config/profiles"
./printguard/build/apps/api/printguard-api
# In another terminal:
./printguard/build/apps/worker/printguard-worker
```

---

## Architecture

### Module layout (`printguard/src/` + `printguard/include/printguard/`)

Each module is a separate CMake static library:

```
common/       — Logger (spdlog wrapper), Env, Crypto (SHA-256 via OpenSSL)
domain/       — Core value types: Job, Finding, FixRecord, ProductPreset, ValidationProfile,
                StateMachine; ConfigLoader reads JSON presets/profiles from disk
pdf/          — PdfLoader (wraps QPDF) → produces DocumentModel (canonical model of pages/boxes)
analysis/     — RuleEngine: takes DocumentModel + Preset + Profile → returns AnalysisResult (Findings)
fix/          — FixPlanner (builds FixPlan from Findings) + FixEngine (applies fixes to PDF)
orchestration/— JobOrchestrator (upload → store → DB record → worker pipeline)
              — LocalBatchProcessor (CLI mode, no DB: iterate directory, run full pipeline per file)
persistence/  — Database (libpqxx singleton), JobRepository (CRUD + claim_next_job)
storage/      — IStorage interface + LocalStorage implementation (files on disk keyed by job/tenant/type)
render/       — PreviewRenderer (page PNG previews via mupdf)
report/       — ReportBuilder (generates Markdown reports)
```

### Job lifecycle (API/Worker mode)

1. `POST /v1/jobs` → `JobOrchestrator::process_upload` → stores original PDF, creates DB row (`status=uploaded`)
2. `printguard-worker` polls `claim_next_job(uploaded → processing)`
3. `JobOrchestrator::run_pipeline(job_id)`:
   - Load PDF → `PdfLoader` → `DocumentModel`
   - Analyze → `RuleEngine::run` → `AnalysisResult` (Findings)
   - Plan fixes → `FixPlanner::build_plan`
   - Apply fixes → `FixEngine::execute` → corrected PDF artifact
   - Re-analyze corrected PDF (revalidation delta)
   - Render previews → `PreviewRenderer`
   - Build report → `ReportBuilder`
   - Update job `status=completed` or `failed`

### Finding severity and fixability

```cpp
enum class FindingSeverity { INFO, WARNING, ERROR };
enum class Fixability { NONE, AUTOMATIC_SAFE, AUTOMATIC_RISKY };
```

A Finding is "blocking" if `severity == ERROR`. `AUTOMATIC_SAFE` fixes are always applied; `AUTOMATIC_RISKY` fixes require explicit enablement. Unresolvable blocking findings leave the job in a `manual_review` state.

### Configuration (JSON, no DB)

- **Presets** (`config/presets/*.json`): product physical dimensions + color space constraints + min DPI
- **Profiles** (`config/profiles/*.json`): named rule sets with per-rule `enabled`, `severity`, and `params`

`ConfigLoader::load_presets(dir)` and `load_profiles(dir)` return `std::map<std::string, T>` keyed by `id`.

### Database schema

Three tables: `tenants`, `jobs`, `artifacts`. Migrations are in `printguard/db/migrations/`. Apply them manually in order with `psql`. The dev seed tenant id is `00000000-0000-0000-0000-000000000000` with `api_key=dev-key-123`.

---

## Compiler flags

All builds enforce `-Wall -Wextra -Werror -Wpedantic`, `-fstack-protector-strong`, and `-D_GLIBCXX_ASSERTIONS`. New code must compile clean with these flags.

## SonarQube

```bash
./printguard/scripts/run_sonar.sh <SONAR_TOKEN>
```

Requires a local SonarQube instance at `http://localhost:9000` and Docker for the scanner.
