#!/bin/bash

# Script to create GitHub issues for estrattoconto enhancement roadmap
# Usage: ./create_issues.sh <github_token>
# Or set GITHUB_TOKEN environment variable

set -e

GITHUB_TOKEN="${1:-$GITHUB_TOKEN}"
REPO_OWNER="girolamodaschio"
REPO_NAME="estrattoconto"
API_URL="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/issues"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GitHub token required"
    echo "Usage: $0 <github_token>"
    echo "Or set GITHUB_TOKEN environment variable"
    exit 1
fi

# Function to create an issue
create_issue() {
    local title="$1"
    local body="$2"
    local labels="$3"

    echo "Creating issue: $title"

    curl -s -X POST "$API_URL" \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -d "$(jq -n \
            --arg title "$title" \
            --arg body "$body" \
            --argjson labels "$labels" \
            '{title: $title, body: $body, labels: $labels}')" | jq -r '.html_url // .message'
}

echo "Creating issues for estrattoconto enhancement roadmap..."
echo ""

# ============================================================================
# PHASE 1: Foundation & Bug Fixes
# ============================================================================

create_issue \
    "[TASK-001] Fix extract_document_type() Loop Bug" \
    "## 🐛 Bug Fix

**Priority:** CRITICAL
**Effort:** 0.5 days
**Phase:** 1 - Foundation & Bug Fixes

## Description
Fix bug in \`converter.py:25-29\` where function returns \`UNSUPPORTED\` on first non-match instead of checking all text elements.

## Current Issue
\`\`\`python
def extract_document_type(converted_result):
    for el in converted_result.document.texts:
        if CENTROVENETO in el.text:
            return CENTROVENETO
        return UNSUPPORTED  # BUG: Returns too early!
\`\`\`

## Solution
Loop should continue through all text elements before returning UNSUPPORTED.

## Files to Modify
- \`estrattoconto/converter.py\`
- \`tests/test_converter.py\` (add test)

## Acceptance Criteria
- [ ] Loop continues through all text elements
- [ ] Returns UNSUPPORTED only after checking everything
- [ ] Test added for bank identifier in second element
- [ ] All existing tests still pass

## Reference
See: \`docs/implementation/phase-1-bugfixes.md#task-11-fix-extract_document_type-loop-bug\`" \
    '["bug", "priority: critical", "phase-1"]'

create_issue \
    "[TASK-002] Add Missing Dependencies to pyproject.toml" \
    "## 📦 Dependencies

**Priority:** CRITICAL
**Effort:** 0.5 days
**Phase:** 1 - Foundation & Bug Fixes

## Description
Add missing dependencies to \`pyproject.toml\`: pandas, numpy, openpyxl.

## Problem
Critical dependencies are implicitly used but not declared:
- \`pandas\` - used throughout
- \`numpy\` - implicit via pandas
- \`openpyxl\` - required for Excel export

## Solution
Update \`pyproject.toml\` dependencies:
\`\`\`toml
[tool.poetry.dependencies]
python = \"^3.10\"
docling = \"^2.58.0\"
pandas = \"^2.0.0\"
numpy = \"^1.24.0\"
openpyxl = \"^3.1.0\"
\`\`\`

## Files to Modify
- \`pyproject.toml\`

## Acceptance Criteria
- [ ] All dependencies explicitly declared
- [ ] Clean install works: \`poetry env remove python && poetry install\`
- [ ] Excel export functionality works
- [ ] All tests pass after fresh install

## Testing
\`\`\`bash
poetry env remove python
poetry install
poetry run pytest tests/test_statement.py::TestEstrattoConto::test_to_excel
\`\`\`

## Reference
See: \`docs/implementation/phase-1-bugfixes.md#task-12-add-missing-dependencies\`" \
    '["dependencies", "priority: critical", "phase-1"]'

create_issue \
    "[TASK-003] Add CLI Entry Point" \
    "## 🔧 Configuration

**Priority:** CRITICAL
**Effort:** 0.5 days
**Phase:** 1 - Foundation & Bug Fixes
**Dependencies:** TASK-002

## Description
Add CLI entry point to \`pyproject.toml\` for the \`estrattoconto\` command.

## Problem
No entry point defined, making CLI harder to use after installation.

## Solution
Add to \`pyproject.toml\`:
\`\`\`toml
[tool.poetry.scripts]
estrattoconto = \"estrattoconto.__main__:main\"
\`\`\`

## Files to Modify
- \`pyproject.toml\`

## Acceptance Criteria
- [ ] \`[tool.poetry.scripts]\` section added
- [ ] \`estrattoconto\` command works after install
- [ ] Works with \`poetry run estrattoconto\`
- [ ] Works after \`pip install -e .\`
- [ ] Help text displays correctly

## Testing
\`\`\`bash
poetry install
poetry run estrattoconto --help
\`\`\`

## Reference
See: \`docs/implementation/phase-1-bugfixes.md#task-13-add-cli-entry-point\`" \
    '["enhancement", "priority: critical", "phase-1"]'

create_issue \
    "[TASK-004] Create Missing amount Column" \
    "## 🐛 Bug Fix

**Priority:** HIGH
**Effort:** 0.5 days
**Phase:** 1 - Foundation & Bug Fixes

## Description
Add \`amount\` column creation in \`enrichment.py\` (currently mentioned in README but not implemented).

## Problem
README.md:87 mentions \`amount\` column but it's never created.

## Solution
Add to \`enrich_data()\`:
\`\`\`python
# Create combined amount column
enriched_table['amount'] = (
    enriched_table['AVERE_Numeric'].fillna(0) -
    enriched_table['DARE_Numeric'].fillna(0)
)
\`\`\`

## Files to Modify
- \`estrattoconto/enrichment.py\`
- \`tests/test_enrichment.py\` (add test)

## Acceptance Criteria
- [ ] \`amount\` column created (AVERE_Numeric - DARE_Numeric)
- [ ] Positive for credits (AVERE)
- [ ] Negative for debits (DARE)
- [ ] Test added and passing
- [ ] Update README if needed

## Reference
See: \`docs/implementation/phase-1-bugfixes.md#task-14-create-missing-amount-column\`" \
    '["bug", "priority: high", "phase-1"]'

create_issue \
    "[TASK-005] Improve Error Handling" \
    "## 🔧 Enhancement

**Priority:** HIGH
**Effort:** 1 day
**Phase:** 1 - Foundation & Bug Fixes

## Description
Add comprehensive error handling throughout converter.py, enrichment.py, statement.py, and __main__.py.

## Problem
Limited error handling leads to cryptic errors when things go wrong.

## Solution
Add error handling with:
- File existence validation
- PDF format validation
- Meaningful exception types (FileNotFoundError, ValueError, RuntimeError)
- Clear error messages
- Proper CLI exit codes

## Files to Modify
- \`estrattoconto/converter.py\`
- \`estrattoconto/enrichment.py\`
- \`estrattoconto/statement.py\`
- \`estrattoconto/__main__.py\`
- \`tests/test_converter.py\` (add error tests)
- \`tests/test_enrichment.py\` (add error tests)
- \`tests/test_statement.py\` (add error tests)

## Acceptance Criteria
- [ ] All functions have appropriate error handling
- [ ] Clear, helpful error messages
- [ ] Different exception types for different errors
- [ ] CLI returns appropriate exit codes (1-4)
- [ ] Tests for error conditions added
- [ ] No regression in existing functionality

## Reference
See: \`docs/implementation/phase-1-bugfixes.md#task-15-improve-error-handling\`" \
    '["enhancement", "priority: high", "phase-1"]'

create_issue \
    "[TASK-006] Add Input Validation" \
    "## ✅ Validation

**Priority:** MEDIUM
**Effort:** 1 day
**Phase:** 1 - Foundation & Bug Fixes

## Description
Create validation.py module with data quality validation functions.

## Solution
Create \`estrattoconto/validation.py\` with:
- \`validate_transaction_data()\` - check extracted data
- \`validate_enriched_data()\` - check enrichment quality
- \`ValidationError\` exception class

## Files to Create
- \`estrattoconto/validation.py\`
- \`tests/test_validation.py\`

## Files to Modify
- \`estrattoconto/converter.py\` (integrate validation)
- \`estrattoconto/enrichment.py\` (integrate validation)

## Acceptance Criteria
- [ ] validation.py module created
- [ ] Validation functions check data quality
- [ ] Integrated into extraction pipeline
- [ ] Warnings displayed to users
- [ ] Critical issues raise exceptions
- [ ] Tests added

## Reference
See: \`docs/implementation/phase-1-bugfixes.md#task-16-add-input-validation\`" \
    '["enhancement", "priority: medium", "phase-1"]'

# ============================================================================
# PHASE 2: Multi-Provider Architecture
# ============================================================================

create_issue \
    "[TASK-007] Create Provider Base Class" \
    "## 🏗️ Architecture

**Priority:** HIGH
**Effort:** 1 day
**Phase:** 2 - Multi-Provider Architecture
**Dependencies:** Phase 1 complete

## Description
Create abstract base class for bank statement providers.

## Solution
Create provider system with:
- \`BankStatementProvider\` abstract base class
- \`BankTables\` dataclass
- \`ProviderMetadata\` dataclass

## Files to Create
- \`estrattoconto/providers/__init__.py\`
- \`estrattoconto/providers/base.py\`

## Acceptance Criteria
- [ ] BankStatementProvider abstract base class created
- [ ] Abstract methods: \`detect()\`, \`extract_tables()\`, \`enrich_data()\`
- [ ] BankTables dataclass defined
- [ ] ProviderMetadata dataclass defined
- [ ] All methods documented with type hints
- [ ] Docstrings with examples

## Reference
See: \`docs/implementation/phase-2-providers.md#task-21-create-provider-base-class\`" \
    '["architecture", "priority: high", "phase-2"]'

create_issue \
    "[TASK-008] Create Provider Registry" \
    "## 🏗️ Architecture

**Priority:** HIGH
**Effort:** 1 day
**Phase:** 2 - Multi-Provider Architecture
**Dependencies:** TASK-007

## Description
Implement provider registry for automatic provider discovery and selection.

## Solution
Create \`ProviderRegistry\` class with:
- Provider registration
- Automatic detection with confidence scores
- Provider lookup by name
- Global registry instance

## Files to Modify
- \`estrattoconto/providers/__init__.py\`

## Files to Create
- \`tests/test_providers.py\`

## Acceptance Criteria
- [ ] ProviderRegistry class implemented
- [ ] \`detect_provider()\` returns best match
- [ ] Confidence threshold support
- [ ] Global registry instance
- [ ] Tests added and passing

## Reference
See: \`docs/implementation/phase-2-providers.md#task-22-create-provider-registry\`" \
    '["architecture", "priority: high", "phase-2"]'

create_issue \
    "[TASK-009] Refactor CENTROVENETO into Provider" \
    "## ♻️ Refactoring

**Priority:** HIGH
**Effort:** 2 days
**Phase:** 2 - Multi-Provider Architecture
**Dependencies:** TASK-008

## Description
Refactor existing CENTROVENETO logic into a provider implementation.

## Solution
Create \`CentroVenetoProvider\` class implementing:
- Bank detection
- Table extraction
- Data enrichment
- All regex patterns

## Files to Create
- \`estrattoconto/providers/centroveneto.py\`

## Files to Modify
- \`estrattoconto/converter.py\` (move logic to provider)
- \`estrattoconto/enrichment.py\` (move logic to provider)
- \`tests/test_converter.py\` (update)
- \`tests/test_enrichment.py\` (update)

## Acceptance Criteria
- [ ] CentroVenetoProvider class created
- [ ] All abstract methods implemented
- [ ] Regex patterns moved from enrichment.py
- [ ] Table extraction logic moved from converter.py
- [ ] Original functionality preserved
- [ ] All tests updated and passing

## Reference
See: \`docs/implementation/phase-2-providers.md#task-23-refactor-centroveneto-into-provider\`" \
    '["refactor", "priority: high", "phase-2"]'

create_issue \
    "[TASK-010] Update Core to Use Providers" \
    "## ♻️ Refactoring

**Priority:** HIGH
**Effort:** 1 day
**Phase:** 2 - Multi-Provider Architecture
**Dependencies:** TASK-009

## Description
Update converter.py and enrichment.py to use the provider system.

## Solution
- converter.py uses provider for extraction
- enrichment.py uses provider for enrichment
- Maintain backward compatibility
- Add deprecation warnings

## Files to Modify
- \`estrattoconto/converter.py\`
- \`estrattoconto/enrichment.py\`

## Acceptance Criteria
- [ ] converter.py uses provider system
- [ ] enrichment.py uses provider system
- [ ] Backward compatibility maintained
- [ ] Deprecation warnings added for old methods
- [ ] All tests passing

## Reference
See: \`docs/implementation/phase-2-providers.md#task-24-update-core-to-use-providers\`" \
    '["refactor", "priority: high", "phase-2"]'

create_issue \
    "[TASK-011] Update Public API for Providers" \
    "## 📚 API

**Priority:** MEDIUM
**Effort:** 0.5 days
**Phase:** 2 - Multi-Provider Architecture
**Dependencies:** TASK-010

## Description
Update statement.py and __init__.py to expose provider system in public API.

## Files to Modify
- \`estrattoconto/statement.py\`
- \`estrattoconto/__init__.py\`
- \`README.md\`

## Acceptance Criteria
- [ ] Provider system accessible from main module
- [ ] \`EstrattoConto.from_pdf()\` accepts \`provider_name\` parameter
- [ ] Provider classes exported in \`__init__.py\`
- [ ] Documentation updated
- [ ] Examples updated

## Reference
See: \`docs/implementation/phase-2-providers.md#task-25-update-public-api\`" \
    '["api", "priority: medium", "phase-2"]'

create_issue \
    "[TASK-012] Create Provider Development Guide" \
    "## 📖 Documentation

**Priority:** MEDIUM
**Effort:** 1 day
**Phase:** 2 - Multi-Provider Architecture
**Dependencies:** TASK-011

## Description
Create comprehensive documentation for adding new bank providers.

## Files to Create
- \`estrattoconto/providers/README.md\`
- \`docs/guides/adding-a-provider.md\`

## Files to Modify
- \`README.md\` (add provider info)

## Acceptance Criteria
- [ ] Step-by-step provider creation guide
- [ ] Example provider implementation (e.g., Intesa Sanpaolo)
- [ ] Testing guide for providers
- [ ] Template code for new providers
- [ ] README.md updated with provider info

## Reference
See: \`docs/implementation/phase-2-providers.md#task-26-documentation\`" \
    '["documentation", "priority: medium", "phase-2"]'

# ============================================================================
# PHASE 3: Performance Optimization
# ============================================================================

create_issue \
    "[TASK-013] Implement Caching System" \
    "## ⚡ Performance

**Priority:** HIGH
**Effort:** 2 days
**Phase:** 3 - Performance Optimization
**Dependencies:** Phase 1 complete

## Description
Implement multi-level file-hash based caching system.

## Solution
Create \`CacheManager\` with:
- File-hash based keys
- Multi-level caching (docling, tables, enriched)
- Cache invalidation
- Statistics tracking

## Expected Impact
**Instant** for cached PDFs (∞x speedup)

## Files to Create
- \`estrattoconto/cache.py\`
- \`tests/test_cache.py\`

## Files to Modify
- \`estrattoconto/converter.py\` (integrate caching)
- \`estrattoconto/statement.py\` (integrate caching)
- \`estrattoconto/__main__.py\` (add CLI commands)

## Acceptance Criteria
- [ ] CacheManager class implemented
- [ ] Multi-level caching works
- [ ] CLI cache commands: \`--no-cache\`, \`--clear-cache\`, \`--cache-stats\`
- [ ] Tests added and passing
- [ ] Cache stats display properly

## Reference
See: \`docs/implementation/phase-3-performance.md#task-31-implement-caching-system\`" \
    '["performance", "priority: high", "phase-3"]'

create_issue \
    "[TASK-014] Implement Fast Extraction with pdfplumber" \
    "## ⚡ Performance

**Priority:** HIGH
**Effort:** 2 days
**Phase:** 3 - Performance Optimization
**Dependencies:** TASK-013

## Description
Implement fast extraction using pdfplumber with validation and fallback to docling.

## Solution
Create hybrid extraction system:
1. Try fast extraction (pdfplumber)
2. Validate results
3. Fall back to docling if validation fails

## Expected Impact
**10-50x speedup** for simple, clean PDFs

## Files to Create
- \`estrattoconto/extractors/__init__.py\`
- \`estrattoconto/extractors/fast.py\`
- \`estrattoconto/extractors/docling.py\`
- \`estrattoconto/extractors/hybrid.py\`
- \`tests/test_hybrid.py\`

## Files to Modify
- \`estrattoconto/converter.py\` (use hybrid extractor)
- \`pyproject.toml\` (add pdfplumber dependency)

## Acceptance Criteria
- [ ] FastExtractor with comprehensive validation
- [ ] DoclingExtractor wrapper
- [ ] HybridExtractor with fallback logic
- [ ] Statistics tracking (fast vs docling usage)
- [ ] Integration with converter
- [ ] Tests added

## Reference
See: \`docs/implementation/hybrid-approaches.md#approach-1-fast-preprocessing--selective-docling\`" \
    '["performance", "priority: high", "phase-3"]'

create_issue \
    "[TASK-015] Implement Template-Based Extraction" \
    "## ⚡ Performance

**Priority:** MEDIUM
**Effort:** 3 days
**Phase:** 3 - Performance Optimization
**Dependencies:** TASK-014

## Description
Implement coordinate-based template extraction for known bank formats.

## Solution
Create template system:
- Define coordinate templates for known banks
- Fast extraction using exact coordinates
- Template learning tool (optional)

## Expected Impact
**50-100x speedup** for known bank formats

## Files to Create
- \`estrattoconto/extractors/template.py\`
- \`tests/test_template.py\`

## Files to Modify
- \`estrattoconto/extractors/hybrid.py\` (add template support)

## Acceptance Criteria
- [ ] TemplateExtractor class implemented
- [ ] Template format defined
- [ ] At least one template created (CENTROVENETO)
- [ ] Integration with enhanced hybrid
- [ ] Template validation
- [ ] Tests added

## Reference
See: \`docs/implementation/hybrid-approaches.md#approach-2-template-based-extraction\`" \
    '["performance", "priority: medium", "phase-3"]'

create_issue \
    "[TASK-016] Implement Async Support" \
    "## ⚡ Performance

**Priority:** HIGH
**Effort:** 2 days
**Phase:** 3 - Performance Optimization
**Dependencies:** TASK-013

## Description
Add async/await support for non-blocking processing.

## Solution
Create async API with:
- \`convert_async()\` function
- ProcessPoolExecutor for CPU-bound work
- Progress callback support

## Expected Impact
**Non-blocking** processing for Django/web apps

## Files to Create
- \`estrattoconto/async_api.py\`
- \`tests/test_async.py\`

## Files to Modify
- \`estrattoconto/__init__.py\` (export async functions)

## Acceptance Criteria
- [ ] Async API implemented
- [ ] ProcessPoolExecutor for CPU-bound work
- [ ] Progress callback support
- [ ] Examples for Django added
- [ ] Tests added

## Reference
See: \`docs/implementation/phase-3-performance.md#task-32-implement-async-support\`" \
    '["performance", "priority: high", "phase-3"]'

create_issue \
    "[TASK-017] Implement Batch Processing" \
    "## ⚡ Performance

**Priority:** MEDIUM
**Effort:** 1 day
**Phase:** 3 - Performance Optimization
**Dependencies:** TASK-013

## Description
Implement parallel batch processing for multiple PDFs.

## Solution
Create batch processing with:
- Multiprocessing for parallel execution
- Progress bars with tqdm
- Error handling for partial failures

## Files to Create
- \`estrattoconto/batch.py\`
- \`tests/test_batch.py\`

## Files to Modify
- \`estrattoconto/__main__.py\` (add batch command)
- \`pyproject.toml\` (add tqdm dependency)

## Acceptance Criteria
- [ ] \`batch_process()\` function implemented
- [ ] Progress bar with tqdm
- [ ] Error handling for partial failures
- [ ] CLI batch command
- [ ] Tests added

## Reference
See: \`docs/implementation/phase-3-performance.md#task-33-implement-batch-processing\`" \
    '["performance", "priority: medium", "phase-3"]'

create_issue \
    "[TASK-018] Performance Benchmarking" \
    "## 📊 Benchmarks

**Priority:** LOW
**Effort:** 1 day
**Phase:** 3 - Performance Optimization
**Dependencies:** TASK-014, TASK-015

## Description
Create comprehensive performance benchmarks comparing all extraction methods.

## Solution
Create benchmarking suite with:
- Benchmarks for all extraction methods
- Performance comparison tables
- Automated benchmark script

## Files to Create
- \`benchmarks/performance.py\`
- \`benchmarks/README.md\`

## Acceptance Criteria
- [ ] Benchmarks for docling, fast, template, hybrid
- [ ] Performance comparison documented
- [ ] Results in table format
- [ ] Automated benchmark script
- [ ] Instructions for running benchmarks

## Reference
See: \`docs/implementation/hybrid-approaches.md#performance-comparison\`" \
    '["benchmarks", "priority: low", "phase-3"]'

# ============================================================================
# PHASE 4: ML-Based Classification
# ============================================================================

create_issue \
    "[TASK-019] Implement ML Bank Detector" \
    "## 🤖 Machine Learning

**Priority:** MEDIUM
**Effort:** 5 days
**Phase:** 4 - ML-Based Classification
**Dependencies:** Phase 2 complete

## Description
Implement machine learning based bank format detection.

## Solution
Create ML detector with:
- Feature extraction from PDFs
- Random Forest classifier
- Training data collection script
- Model saving/loading

## Expected Impact
Automatic bank detection without hardcoded rules

## Files to Create
- \`estrattoconto/ml/__init__.py\`
- \`estrattoconto/ml/detector.py\`
- \`scripts/collect_training_data.py\`
- \`tests/test_ml_detector.py\`

## Files to Modify
- \`estrattoconto/providers/__init__.py\` (integrate ML detection)
- \`pyproject.toml\` (add sklearn, joblib dependencies)

## Acceptance Criteria
- [ ] MLBankDetector class implemented
- [ ] Feature extraction from document structure
- [ ] Training script created
- [ ] Integration with provider registry
- [ ] Model evaluation metrics
- [ ] Tests added

## Reference
See: \`docs/implementation/phase-4-ml.md#task-41-ml-based-bank-detection\`" \
    '["ml", "priority: medium", "phase-4"]'

create_issue \
    "[TASK-020] Implement NER for Entity Extraction" \
    "## 🤖 Machine Learning

**Priority:** MEDIUM
**Effort:** 7 days
**Phase:** 4 - ML-Based Classification
**Dependencies:** Phase 2 complete

## Description
Use spaCy NER to extract payer/payee entities instead of regex.

## Solution
Create NER system with:
- Italian spaCy model
- Entity extraction (payer, payee, organization)
- Fallback to regex if confidence low

## Expected Impact
More accurate entity extraction

## Files to Create
- \`estrattoconto/ml/ner.py\`
- \`tests/test_ner.py\`

## Files to Modify
- \`estrattoconto/providers/centroveneto.py\` (optional NER)
- \`pyproject.toml\` (add spacy dependency)

## Acceptance Criteria
- [ ] BankingNER class implemented
- [ ] Italian spaCy model integrated
- [ ] Fallback to regex patterns
- [ ] Comparison with regex accuracy
- [ ] Tests added

## Reference
See: \`docs/implementation/phase-4-ml.md#task-42-ner-for-entity-extraction\`" \
    '["ml", "priority: medium", "phase-4"]'

create_issue \
    "[TASK-021] Implement Transaction Categorization" \
    "## 🤖 Machine Learning

**Priority:** MEDIUM
**Effort:** 4 days
**Phase:** 4 - ML-Based Classification
**Dependencies:** Phase 2 complete

## Description
Implement ML-based transaction categorization using transformers.

## Solution
Create categorization system with:
- Zero-shot classification
- Predefined categories
- Bulk categorization support

## Files to Create
- \`estrattoconto/ml/categorizer.py\`
- \`tests/test_categorizer.py\`

## Files to Modify
- \`estrattoconto/enrichment.py\` (optional categorization)
- \`pyproject.toml\` (add transformers dependency)

## Acceptance Criteria
- [ ] TransactionCategorizer implemented
- [ ] Zero-shot classification working
- [ ] Bulk categorization support
- [ ] Integration with enrichment
- [ ] Tests added

## Reference
See: \`docs/implementation/phase-4-ml.md#task-43-transaction-categorization\`" \
    '["ml", "priority: medium", "phase-4"]'

# ============================================================================
# PHASE 5: Django Integration
# ============================================================================

create_issue \
    "[TASK-022] Create Django Package Structure" \
    "## 🌐 Django Integration

**Priority:** MEDIUM
**Effort:** 3 days
**Phase:** 5 - Django Integration
**Dependencies:** Phase 3 complete (async support)

## Description
Create separate Django package for integration with models, views, tasks.

## Solution
Create \`estrattoconto-django\` package with:
- Django models (BankStatement, Transaction)
- Celery tasks for background processing
- Views for upload and display
- REST API with Django REST Framework
- Admin interface

## Files to Create
Complete package structure:
- \`estrattoconto-django/estrattoconto_django/\`
  - models.py
  - views.py
  - tasks.py
  - serializers.py
  - admin.py
  - urls.py
  - forms.py
  - templates/
- Tests

## Acceptance Criteria
- [ ] Django package created
- [ ] Models for BankStatement and Transaction
- [ ] Celery tasks for processing
- [ ] Views and forms for upload
- [ ] REST API with DRF
- [ ] Admin interface configured
- [ ] Tests for all components

## Reference
See: \`docs/implementation/phase-5-django.md#task-51-create-django-package-structure\`" \
    '["django", "priority: medium", "phase-5"]'

create_issue \
    "[TASK-023] Implement WebSocket Support" \
    "## 🌐 Django Integration

**Priority:** LOW
**Effort:** 2 days
**Phase:** 5 - Django Integration
**Dependencies:** TASK-022

## Description
Add real-time progress updates using Django Channels.

## Solution
Implement WebSocket support with:
- Django Channels configuration
- WebSocket consumer for progress updates
- Integration with Celery tasks

## Files to Create
- \`estrattoconto-django/estrattoconto_django/consumers.py\`
- \`estrattoconto-django/estrattoconto_django/routing.py\`

## Files to Modify
- \`estrattoconto-django/estrattoconto_django/tasks.py\` (send updates)

## Acceptance Criteria
- [ ] Django Channels configured
- [ ] WebSocket consumer implemented
- [ ] Real-time updates working
- [ ] Frontend JavaScript example
- [ ] Tests added

## Reference
See: \`docs/implementation/phase-5-django.md#task-52-websocket-support-for-real-time-progress\`" \
    '["django", "websocket", "priority: low", "phase-5"]'

create_issue \
    "[TASK-024] Create Example Django Project" \
    "## 📖 Documentation

**Priority:** LOW
**Effort:** 2 days
**Phase:** 5 - Django Integration
**Dependencies:** TASK-022

## Description
Create complete example Django project demonstrating estrattoconto-django usage.

## Solution
Create example project with:
- Complete Django setup
- Integration with estrattoconto-django
- Docker Compose setup
- README with instructions

## Files to Create
- \`examples/django-family-house/\` (entire project)

## Acceptance Criteria
- [ ] Working Django project
- [ ] Integration with estrattoconto-django
- [ ] README with setup instructions
- [ ] Example templates and views
- [ ] Docker Compose setup
- [ ] Instructions for running locally

## Reference
See: \`docs/implementation/phase-5-django.md\`" \
    '["documentation", "example", "priority: low", "phase-5"]'

# ============================================================================
# PHASE 6: Production Readiness
# ============================================================================

create_issue \
    "[TASK-025] Set Up CI/CD Pipeline" \
    "## 🚀 CI/CD

**Priority:** MEDIUM
**Effort:** 1 day
**Phase:** 6 - Production Readiness

## Description
Set up GitHub Actions for testing, linting, and automated releases.

## Solution
Create workflows for:
- Testing on multiple Python versions
- Linting (pylint, ruff, mypy)
- Code coverage reporting
- Automated releases

## Files to Create
- \`.github/workflows/test.yml\`
- \`.github/workflows/release.yml\`
- \`.github/workflows/lint.yml\`

## Acceptance Criteria
- [ ] GitHub Actions workflows created
- [ ] Tests run on push/PR (Python 3.10-3.13)
- [ ] Linting automated
- [ ] Code coverage reporting (codecov)
- [ ] Automated releases on tag

## Reference
See: \`ROADMAP.md#phase-6-production-readiness-\`" \
    '["ci-cd", "priority: medium", "phase-6"]'

create_issue \
    "[TASK-026] Generate API Documentation" \
    "## 📖 Documentation

**Priority:** LOW
**Effort:** 2 days
**Phase:** 6 - Production Readiness
**Dependencies:** Phase 2 complete

## Description
Generate comprehensive API documentation using Sphinx or MkDocs.

## Files to Create
- \`docs/api/\` (API documentation)
- \`mkdocs.yml\` or \`docs/conf.py\`

## Acceptance Criteria
- [ ] API docs generated
- [ ] All public APIs documented
- [ ] Examples included
- [ ] Hosted on GitHub Pages or ReadTheDocs
- [ ] Automatic updates on push

## Reference
See: \`ROADMAP.md#phase-6-production-readiness-\`" \
    '["documentation", "priority: low", "phase-6"]'

create_issue \
    "[TASK-027] Publish to PyPI" \
    "## 📦 Distribution

**Priority:** LOW
**Effort:** 1 day
**Phase:** 6 - Production Readiness
**Dependencies:** Phase 1, Phase 2 complete

## Description
Publish estrattoconto package to PyPI.

## Solution
- Complete package metadata
- Create CHANGELOG.md
- Set up automated publishing workflow

## Files to Modify
- \`pyproject.toml\` (package metadata)
- \`README.md\` (PyPI description)

## Files to Create
- \`CHANGELOG.md\`
- \`.github/workflows/publish.yml\`

## Acceptance Criteria
- [ ] Package metadata complete
- [ ] Published to PyPI
- [ ] Installation via \`pip install estrattoconto\` works
- [ ] Version management configured
- [ ] CHANGELOG maintained

## Reference
See: \`ROADMAP.md#phase-6-production-readiness-\`" \
    '["distribution", "priority: low", "phase-6"]'

echo ""
echo "============================================"
echo "✅ All 27 issues created successfully!"
echo "============================================"
echo ""
echo "View issues at: https://github.com/${REPO_OWNER}/${REPO_NAME}/issues"
