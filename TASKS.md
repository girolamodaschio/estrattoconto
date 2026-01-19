# estrattoconto - Implementation Tasks

This document contains granular, agent-ready tasks for implementing the estrattoconto enhancement roadmap.

## How to Use This File

1. **Pick a task** from the appropriate phase
2. **Create a GitHub issue** with the task details
3. **Assign yourself** or spawn an agent to work on it
4. **Create a branch** following the naming convention: `claude/task-<task-id>-<session-id>`
5. **Implement** following the detailed specifications in `docs/implementation/`
6. **Test** according to acceptance criteria
7. **Create PR** linking to the issue
8. **Mark complete** with ✅ when merged

---

## 📊 Task Status Legend

- ⬜ Not started
- 🔄 In progress
- ✅ Completed
- ⏸️ Blocked
- ⚠️ Needs review

---

## PHASE 1: Foundation & Bug Fixes (CRITICAL PRIORITY)

### Task 1.1: Fix extract_document_type() Loop Bug

**ID:** `TASK-001`
**Status:** ⬜
**Priority:** CRITICAL
**Effort:** 0.5 days
**Dependencies:** None

**Description:**
Fix bug in `converter.py:25-29` where function returns `UNSUPPORTED` on first non-match instead of checking all text elements.

**Files to Modify:**
- `estrattoconto/converter.py`

**Acceptance Criteria:**
- [ ] Loop continues through all text elements before returning UNSUPPORTED
- [ ] Test added in `tests/test_converter.py`
- [ ] All existing tests still pass

**Reference:** [Phase 1 Docs](docs/implementation/phase-1-bugfixes.md#task-11-fix-extract_document_type-loop-bug)

---

### Task 1.2: Add Missing Dependencies to pyproject.toml

**ID:** `TASK-002`
**Status:** ⬜
**Priority:** CRITICAL
**Effort:** 0.5 days
**Dependencies:** None

**Description:**
Add missing dependencies: pandas, numpy, openpyxl to `pyproject.toml`.

**Files to Modify:**
- `pyproject.toml`

**Acceptance Criteria:**
- [ ] All dependencies explicitly declared
- [ ] Clean install works: `poetry env remove python && poetry install`
- [ ] Excel export test passes
- [ ] All tests pass after fresh install

**Reference:** [Phase 1 Docs](docs/implementation/phase-1-bugfixes.md#task-12-add-missing-dependencies)

---

### Task 1.3: Add CLI Entry Point

**ID:** `TASK-003`
**Status:** ⬜
**Priority:** CRITICAL
**Effort:** 0.5 days
**Dependencies:** TASK-002

**Description:**
Add CLI entry point to `pyproject.toml` for the `estrattoconto` command.

**Files to Modify:**
- `pyproject.toml`

**Acceptance Criteria:**
- [ ] `[tool.poetry.scripts]` section added
- [ ] `estrattoconto` command works after install
- [ ] Help text displays correctly

**Reference:** [Phase 1 Docs](docs/implementation/phase-1-bugfixes.md#task-13-add-cli-entry-point)

---

### Task 1.4: Create Missing amount Column

**ID:** `TASK-004`
**Status:** ⬜
**Priority:** HIGH
**Effort:** 0.5 days
**Dependencies:** None

**Description:**
Add `amount` column creation in `enrichment.py` (currently mentioned in README but not implemented).

**Files to Modify:**
- `estrattoconto/enrichment.py`
- `tests/test_enrichment.py`

**Acceptance Criteria:**
- [ ] `amount` column created (AVERE_Numeric - DARE_Numeric)
- [ ] Positive for credits, negative for debits
- [ ] Test added and passing

**Reference:** [Phase 1 Docs](docs/implementation/phase-1-bugfixes.md#task-14-create-missing-amount-column)

---

### Task 1.5: Improve Error Handling

**ID:** `TASK-005`
**Status:** ⬜
**Priority:** HIGH
**Effort:** 1 day
**Dependencies:** None

**Description:**
Add comprehensive error handling throughout converter.py, enrichment.py, statement.py, and __main__.py.

**Files to Modify:**
- `estrattoconto/converter.py`
- `estrattoconto/enrichment.py`
- `estrattoconto/statement.py`
- `estrattoconto/__main__.py`
- `tests/test_converter.py`
- `tests/test_enrichment.py`
- `tests/test_statement.py`

**Acceptance Criteria:**
- [ ] All functions have appropriate error handling
- [ ] Clear, helpful error messages
- [ ] Different exception types for different errors
- [ ] CLI returns appropriate exit codes
- [ ] Tests for error conditions added

**Reference:** [Phase 1 Docs](docs/implementation/phase-1-bugfixes.md#task-15-improve-error-handling)

---

### Task 1.6: Add Input Validation

**ID:** `TASK-006`
**Status:** ⬜
**Priority:** MEDIUM
**Effort:** 1 day
**Dependencies:** None

**Description:**
Create validation.py module with data quality validation functions.

**Files to Create:**
- `estrattoconto/validation.py`
- `tests/test_validation.py`

**Files to Modify:**
- `estrattoconto/converter.py` (integrate validation)
- `estrattoconto/enrichment.py` (integrate validation)

**Acceptance Criteria:**
- [ ] validation.py module created
- [ ] Validation integrated into extraction pipeline
- [ ] Warnings displayed to users
- [ ] Critical issues raise exceptions
- [ ] Tests added

**Reference:** [Phase 1 Docs](docs/implementation/phase-1-bugfixes.md#task-16-add-input-validation)

---

## PHASE 2: Multi-Provider Architecture (HIGH PRIORITY)

### Task 2.1: Create Provider Base Class

**ID:** `TASK-007`
**Status:** ⬜
**Priority:** HIGH
**Effort:** 1 day
**Dependencies:** Phase 1 complete

**Description:**
Create abstract base class for bank statement providers.

**Files to Create:**
- `estrattoconto/providers/__init__.py`
- `estrattoconto/providers/base.py`

**Acceptance Criteria:**
- [ ] BankStatementProvider abstract base class created
- [ ] BankTables dataclass defined
- [ ] ProviderMetadata dataclass defined
- [ ] All abstract methods documented with type hints

**Reference:** [Phase 2 Docs](docs/implementation/phase-2-providers.md#task-21-create-provider-base-class)

---

### Task 2.2: Create Provider Registry

**ID:** `TASK-008`
**Status:** ⬜
**Priority:** HIGH
**Effort:** 1 day
**Dependencies:** TASK-007

**Description:**
Implement provider registry for automatic provider discovery and selection.

**Files to Modify:**
- `estrattoconto/providers/__init__.py`

**Files to Create:**
- `tests/test_providers.py`

**Acceptance Criteria:**
- [ ] ProviderRegistry class implemented
- [ ] Provider detection with confidence scores
- [ ] Global registry instance
- [ ] Tests added and passing

**Reference:** [Phase 2 Docs](docs/implementation/phase-2-providers.md#task-22-create-provider-registry)

---

### Task 2.3: Refactor CENTROVENETO into Provider

**ID:** `TASK-009`
**Status:** ⬜
**Priority:** HIGH
**Effort:** 2 days
**Dependencies:** TASK-008

**Description:**
Refactor existing CENTROVENETO logic into a provider implementation.

**Files to Create:**
- `estrattoconto/providers/centroveneto.py`

**Files to Modify:**
- `estrattoconto/converter.py` (move logic to provider)
- `estrattoconto/enrichment.py` (move logic to provider)

**Acceptance Criteria:**
- [ ] CentroVenetoProvider class created
- [ ] All abstract methods implemented
- [ ] Regex patterns moved from enrichment.py
- [ ] Table extraction logic moved from converter.py
- [ ] Original functionality preserved
- [ ] Tests updated and passing

**Reference:** [Phase 2 Docs](docs/implementation/phase-2-providers.md#task-23-refactor-centroveneto-into-provider)

---

### Task 2.4: Update Core to Use Providers

**ID:** `TASK-010`
**Status:** ⬜
**Priority:** HIGH
**Effort:** 1 day
**Dependencies:** TASK-009

**Description:**
Update converter.py and enrichment.py to use the provider system.

**Files to Modify:**
- `estrattoconto/converter.py`
- `estrattoconto/enrichment.py`

**Acceptance Criteria:**
- [ ] converter.py uses provider system
- [ ] enrichment.py uses provider system
- [ ] Backward compatibility maintained
- [ ] Deprecation warnings added
- [ ] All tests passing

**Reference:** [Phase 2 Docs](docs/implementation/phase-2-providers.md#task-24-update-core-to-use-providers)

---

### Task 2.5: Update Public API for Providers

**ID:** `TASK-011`
**Status:** ⬜
**Priority:** MEDIUM
**Effort:** 0.5 days
**Dependencies:** TASK-010

**Description:**
Update statement.py and __init__.py to expose provider system in public API.

**Files to Modify:**
- `estrattoconto/statement.py`
- `estrattoconto/__init__.py`
- `README.md`

**Acceptance Criteria:**
- [ ] Provider system accessible from main module
- [ ] Documentation updated
- [ ] Examples updated

**Reference:** [Phase 2 Docs](docs/implementation/phase-2-providers.md#task-25-update-public-api)

---

### Task 2.6: Create Provider Development Guide

**ID:** `TASK-012`
**Status:** ⬜
**Priority:** MEDIUM
**Effort:** 1 day
**Dependencies:** TASK-011

**Description:**
Create comprehensive documentation for adding new bank providers.

**Files to Create:**
- `estrattoconto/providers/README.md`
- `docs/guides/adding-a-provider.md`

**Acceptance Criteria:**
- [ ] Step-by-step provider creation guide
- [ ] Example provider implementation
- [ ] Testing guide for providers
- [ ] README.md updated with provider info

**Reference:** [Phase 2 Docs](docs/implementation/phase-2-providers.md#task-26-documentation)

---

## PHASE 3: Performance Optimization (HIGH PRIORITY)

### Task 3.1: Implement Caching System

**ID:** `TASK-013`
**Status:** ⬜
**Priority:** HIGH
**Effort:** 2 days
**Dependencies:** Phase 1 complete

**Description:**
Implement multi-level file-hash based caching system.

**Files to Create:**
- `estrattoconto/cache.py`
- `tests/test_cache.py`

**Files to Modify:**
- `estrattoconto/converter.py`
- `estrattoconto/statement.py`
- `estrattoconto/__main__.py`

**Acceptance Criteria:**
- [ ] CacheManager class implemented
- [ ] Multi-level caching (docling, tables, enriched)
- [ ] Integration with converter and statement
- [ ] CLI cache commands (--no-cache, --clear-cache, --cache-stats)
- [ ] Tests added and passing

**Reference:** [Phase 3 Docs](docs/implementation/phase-3-performance.md#task-31-implement-caching-system)

---

### Task 3.2: Implement Fast Extraction with pdfplumber

**ID:** `TASK-014`
**Status:** ⬜
**Priority:** HIGH
**Effort:** 2 days
**Dependencies:** TASK-013

**Description:**
Implement fast extraction using pdfplumber with validation and fallback to docling.

**Files to Create:**
- `estrattoconto/extractors/__init__.py`
- `estrattoconto/extractors/fast.py`
- `estrattoconto/extractors/docling.py`
- `estrattoconto/extractors/hybrid.py`
- `tests/test_hybrid.py`

**Files to Modify:**
- `estrattoconto/converter.py`
- `pyproject.toml` (add pdfplumber dependency)

**Acceptance Criteria:**
- [ ] FastExtractor implemented with validation
- [ ] DoclingExtractor wrapper created
- [ ] HybridExtractor with fallback logic
- [ ] Integration with converter
- [ ] Statistics tracking
- [ ] Tests added

**Reference:** [Hybrid Approaches Docs](docs/implementation/hybrid-approaches.md#approach-1-fast-preprocessing--selective-docling)

---

### Task 3.3: Implement Template-Based Extraction

**ID:** `TASK-015`
**Status:** ⬜
**Priority:** MEDIUM
**Effort:** 3 days
**Dependencies:** TASK-014

**Description:**
Implement coordinate-based template extraction for known bank formats.

**Files to Create:**
- `estrattoconto/extractors/template.py`
- `tests/test_template.py`

**Files to Modify:**
- `estrattoconto/extractors/hybrid.py` (add template support)

**Acceptance Criteria:**
- [ ] TemplateExtractor class implemented
- [ ] Template format defined
- [ ] At least one template created (CENTROVENETO)
- [ ] Integration with enhanced hybrid
- [ ] Tests added

**Reference:** [Hybrid Approaches Docs](docs/implementation/hybrid-approaches.md#approach-2-template-based-extraction)

---

### Task 3.4: Implement Async Support

**ID:** `TASK-016`
**Status:** ⬜
**Priority:** HIGH
**Effort:** 2 days
**Dependencies:** TASK-013

**Description:**
Add async/await support for non-blocking processing.

**Files to Create:**
- `estrattoconto/async_api.py`
- `tests/test_async.py`

**Files to Modify:**
- `estrattoconto/__init__.py`

**Acceptance Criteria:**
- [ ] Async API implemented with convert_async()
- [ ] ProcessPoolExecutor for CPU-bound work
- [ ] Progress callback support
- [ ] Examples for Django added
- [ ] Tests added

**Reference:** [Phase 3 Docs](docs/implementation/phase-3-performance.md#task-32-implement-async-support)

---

### Task 3.5: Implement Batch Processing

**ID:** `TASK-017`
**Status:** ⬜
**Priority:** MEDIUM
**Effort:** 1 day
**Dependencies:** TASK-013

**Description:**
Implement parallel batch processing for multiple PDFs.

**Files to Create:**
- `estrattoconto/batch.py`
- `tests/test_batch.py`

**Files to Modify:**
- `estrattoconto/__main__.py` (add batch command)
- `pyproject.toml` (add tqdm dependency)

**Acceptance Criteria:**
- [ ] batch_process() function implemented
- [ ] Progress bar with tqdm
- [ ] Error handling for partial failures
- [ ] CLI batch command
- [ ] Tests added

**Reference:** [Phase 3 Docs](docs/implementation/phase-3-performance.md#task-33-implement-batch-processing)

---

### Task 3.6: Performance Benchmarking

**ID:** `TASK-018`
**Status:** ⬜
**Priority:** LOW
**Effort:** 1 day
**Dependencies:** TASK-014, TASK-015

**Description:**
Create comprehensive performance benchmarks comparing all extraction methods.

**Files to Create:**
- `benchmarks/performance.py`
- `benchmarks/README.md`

**Acceptance Criteria:**
- [ ] Benchmarks for all extraction methods
- [ ] Performance comparison table
- [ ] Results documented
- [ ] Automated benchmark script

**Reference:** [Hybrid Approaches Docs](docs/implementation/hybrid-approaches.md#performance-comparison)

---

## PHASE 4: ML-Based Classification (MEDIUM PRIORITY)

### Task 4.1: Implement ML Bank Detector

**ID:** `TASK-019`
**Status:** ⬜
**Priority:** MEDIUM
**Effort:** 5 days
**Dependencies:** Phase 2 complete

**Description:**
Implement machine learning based bank format detection.

**Files to Create:**
- `estrattoconto/ml/__init__.py`
- `estrattoconto/ml/detector.py`
- `scripts/collect_training_data.py`
- `tests/test_ml_detector.py`

**Files to Modify:**
- `estrattoconto/providers/__init__.py`
- `pyproject.toml` (add sklearn, joblib dependencies)

**Acceptance Criteria:**
- [ ] MLBankDetector class implemented
- [ ] Feature extraction from PDFs
- [ ] Training script created
- [ ] Integration with provider registry
- [ ] Model evaluation metrics
- [ ] Tests added

**Reference:** [Phase 4 Docs](docs/implementation/phase-4-ml.md#task-41-ml-based-bank-detection)

---

### Task 4.2: Implement NER for Entity Extraction

**ID:** `TASK-020`
**Status:** ⬜
**Priority:** MEDIUM
**Effort:** 7 days
**Dependencies:** Phase 2 complete

**Description:**
Use spaCy NER to extract payer/payee entities instead of regex.

**Files to Create:**
- `estrattoconto/ml/ner.py`
- `tests/test_ner.py`

**Files to Modify:**
- `estrattoconto/providers/centroveneto.py` (optional NER support)
- `pyproject.toml` (add spacy dependency)

**Acceptance Criteria:**
- [ ] BankingNER class implemented
- [ ] Italian spaCy model integrated
- [ ] Fallback to regex if confidence low
- [ ] Comparison with regex accuracy
- [ ] Tests added

**Reference:** [Phase 4 Docs](docs/implementation/phase-4-ml.md#task-42-ner-for-entity-extraction)

---

### Task 4.3: Implement Transaction Categorization

**ID:** `TASK-021`
**Status:** ⬜
**Priority:** MEDIUM
**Effort:** 4 days
**Dependencies:** Phase 2 complete

**Description:**
Implement ML-based transaction categorization using transformers.

**Files to Create:**
- `estrattoconto/ml/categorizer.py`
- `tests/test_categorizer.py`

**Files to Modify:**
- `estrattoconto/enrichment.py` (optional categorization)
- `pyproject.toml` (add transformers dependency)

**Acceptance Criteria:**
- [ ] TransactionCategorizer implemented
- [ ] Zero-shot classification working
- [ ] Bulk categorization support
- [ ] Integration with enrichment
- [ ] Tests added

**Reference:** [Phase 4 Docs](docs/implementation/phase-4-ml.md#task-43-transaction-categorization)

---

## PHASE 5: Django Integration (MEDIUM PRIORITY)

### Task 5.1: Create Django Package Structure

**ID:** `TASK-022`
**Status:** ⬜
**Priority:** MEDIUM
**Effort:** 3 days
**Dependencies:** Phase 3 complete (async support)

**Description:**
Create separate Django package for integration with models, views, tasks.

**Files to Create:**
- `estrattoconto-django/` (entire package structure)
- Django models, views, serializers, tasks, admin
- Tests for Django integration

**Acceptance Criteria:**
- [ ] Django package created with proper structure
- [ ] Models for BankStatement and Transaction
- [ ] Celery tasks for background processing
- [ ] Views for upload and display
- [ ] REST API with DRF
- [ ] Admin interface
- [ ] Tests for all components

**Reference:** [Phase 5 Docs](docs/implementation/phase-5-django.md#task-51-create-django-package-structure)

---

### Task 5.2: Implement WebSocket Support

**ID:** `TASK-023`
**Status:** ⬜
**Priority:** LOW
**Effort:** 2 days
**Dependencies:** TASK-022

**Description:**
Add real-time progress updates using Django Channels.

**Files to Create:**
- `estrattoconto-django/estrattoconto_django/consumers.py`
- `estrattoconto-django/estrattoconto_django/routing.py`

**Files to Modify:**
- `estrattoconto-django/estrattoconto_django/tasks.py` (send updates)

**Acceptance Criteria:**
- [ ] Django Channels configured
- [ ] WebSocket consumer for progress updates
- [ ] Real-time updates working
- [ ] Frontend JavaScript example
- [ ] Tests added

**Reference:** [Phase 5 Docs](docs/implementation/phase-5-django.md#task-52-websocket-support-for-real-time-progress)

---

### Task 5.3: Create Example Django Project

**ID:** `TASK-024`
**Status:** ⬜
**Priority:** LOW
**Effort:** 2 days
**Dependencies:** TASK-022

**Description:**
Create complete example Django project demonstrating estrattoconto-django usage.

**Files to Create:**
- `examples/django-family-house/` (entire example project)

**Acceptance Criteria:**
- [ ] Working Django project
- [ ] Integration with estrattoconto-django
- [ ] README with setup instructions
- [ ] Example templates and views
- [ ] Docker Compose setup

**Reference:** [Phase 5 Docs](docs/implementation/phase-5-django.md)

---

## PHASE 6: Production Readiness (MEDIUM PRIORITY)

### Task 6.1: Set Up CI/CD Pipeline

**ID:** `TASK-025`
**Status:** ⬜
**Priority:** MEDIUM
**Effort:** 1 day
**Dependencies:** None

**Description:**
Set up GitHub Actions for testing, linting, and automated releases.

**Files to Create:**
- `.github/workflows/test.yml`
- `.github/workflows/release.yml`
- `.github/workflows/lint.yml`

**Acceptance Criteria:**
- [ ] GitHub Actions workflows created
- [ ] Tests run on push/PR
- [ ] Linting (pylint, ruff, mypy) automated
- [ ] Code coverage reporting (codecov)
- [ ] Automated releases on tag

**Reference:** [ROADMAP](ROADMAP.md#phase-6-production-readiness-)

---

### Task 6.2: Generate API Documentation

**ID:** `TASK-026`
**Status:** ⬜
**Priority:** LOW
**Effort:** 2 days
**Dependencies:** Phase 2 complete

**Description:**
Generate comprehensive API documentation using Sphinx or MkDocs.

**Files to Create:**
- `docs/api/` (API documentation)
- `mkdocs.yml` or `docs/conf.py`

**Acceptance Criteria:**
- [ ] API docs generated
- [ ] All public APIs documented
- [ ] Examples included
- [ ] Hosted on GitHub Pages or ReadTheDocs

**Reference:** [ROADMAP](ROADMAP.md#phase-6-production-readiness-)

---

### Task 6.3: Publish to PyPI

**ID:** `TASK-027`
**Status:** ⬜
**Priority:** LOW
**Effort:** 1 day
**Dependencies:** Phase 1, Phase 2 complete

**Description:**
Publish estrattoconto package to PyPI.

**Files to Modify:**
- `pyproject.toml` (package metadata)
- `README.md` (PyPI description)

**Files to Create:**
- `CHANGELOG.md`
- `.github/workflows/publish.yml`

**Acceptance Criteria:**
- [ ] Package metadata complete
- [ ] Published to PyPI
- [ ] Installation via `pip install estrattoconto` works
- [ ] Version management configured
- [ ] CHANGELOG maintained

**Reference:** [ROADMAP](ROADMAP.md#phase-6-production-readiness-)

---

## Task Assignment Guidelines

### For Human Developers:
1. Pick a task matching your skill level
2. Create GitHub issue with task ID
3. Create branch and implement
4. Submit PR with tests

### For AI Agents:
1. Task can be assigned via: `@agent please work on TASK-XXX`
2. Agent should:
   - Read task description
   - Read referenced documentation
   - Implement according to acceptance criteria
   - Run tests
   - Create PR

### Priority Order:
1. **CRITICAL** (Phase 1) - Do first
2. **HIGH** (Phase 2-3) - Core functionality
3. **MEDIUM** (Phase 4-5) - Enhancement features
4. **LOW** (Phase 6) - Polish and distribution

---

## Progress Tracking

| Phase | Tasks Complete | Total Tasks | Progress |
|-------|----------------|-------------|----------|
| Phase 1 | 0 | 6 | ⬜⬜⬜⬜⬜⬜ 0% |
| Phase 2 | 0 | 6 | ⬜⬜⬜⬜⬜⬜ 0% |
| Phase 3 | 0 | 6 | ⬜⬜⬜⬜⬜⬜ 0% |
| Phase 4 | 0 | 3 | ⬜⬜⬜ 0% |
| Phase 5 | 0 | 3 | ⬜⬜⬜ 0% |
| Phase 6 | 0 | 3 | ⬜⬜⬜ 0% |
| **Total** | **0** | **27** | **0%** |

---

## Quick Start for Agents

```bash
# 1. Read the task
cat TASKS.md | grep "TASK-001" -A 20

# 2. Read detailed specs
cat docs/implementation/phase-1-bugfixes.md

# 3. Implement changes
# ... make changes ...

# 4. Run tests
poetry run pytest -v

# 5. Create PR
git add .
git commit -m "feat: implement TASK-001 - fix extract_document_type loop bug"
git push -u origin claude/task-001-<session-id>
```

---

**Last Updated:** 2026-01-18
**Total Tasks:** 27
**Estimated Total Effort:** 55-75 days
