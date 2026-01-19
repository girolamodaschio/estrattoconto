# estrattoconto - Enhancement Roadmap

This document outlines the comprehensive plan to evolve estrattoconto from a single-bank PDF extractor into a robust, multi-provider, production-ready library for Italian bank statement processing.

## 🎯 Vision

Transform estrattoconto into:
- **Multi-provider system** supporting all major Italian banks
- **High-performance tool** with 10-100x speedup through hybrid approaches
- **Production-ready library** for Django/web integration
- **ML-powered solution** for automatic bank detection and classification

## 📊 Current State Analysis

### Strengths
- ✅ Clean architecture with separation of concerns
- ✅ Modern Python practices (Poetry, type hints, comprehensive docs)
- ✅ Dual API design (OO + functional)
- ✅ Rich data extraction (payers, payees, classification)
- ✅ Well-documented (AGENTS.md, README, docstrings)

### Critical Weaknesses
- ❌ **Hardcoded single-bank design** - All logic assumes CENTROVENETO format
- ❌ **Performance limitations** - No optimization strategies for slow docling
- ❌ **Missing dependencies** - pandas, numpy, openpyxl not in pyproject.toml
- ❌ **Code bugs** - extract_document_type() loop bug, missing amount column
- ❌ **No Django integration** - No async support, models, or Celery tasks

## 🗺️ Implementation Phases

### PHASE 1: Foundation & Bug Fixes ⚡ (Priority: CRITICAL)
**Duration:** 1-2 days | **Impact:** HIGH - Stability

Fix critical bugs and stabilize current functionality:
- Fix `extract_document_type()` loop bug
- Add missing dependencies to pyproject.toml
- Create `amount` column in enrichment
- Add CLI entry point
- Improve error handling
- Add validation

**See:** [docs/implementation/phase-1-bugfixes.md](docs/implementation/phase-1-bugfixes.md)

---

### PHASE 2: Multi-Provider Architecture 🏦 (Priority: HIGH)
**Duration:** 3-5 days | **Impact:** VERY HIGH - Extensibility

Create provider abstraction layer for multi-bank support:
- Design `BankStatementProvider` abstract base class
- Implement `ProviderRegistry` with auto-discovery
- Refactor CENTROVENETO into provider
- Add configuration system (YAML)
- Create provider creation guide

**Benefits:**
- Add new banks without modifying core code
- Each bank's logic isolated
- Plugin architecture for custom providers

**See:** [docs/implementation/phase-2-providers.md](docs/implementation/phase-2-providers.md)

---

### PHASE 3: Performance Optimization ⚡ (Priority: HIGH)
**Duration:** 4-7 days | **Impact:** VERY HIGH - Speed

Implement hybrid approaches to achieve 10-100x speedup:

#### 3.1 Caching Strategy
- File-hash based caching
- Multi-level cache (docling results, enriched data)
- Smart invalidation

#### 3.2 Hybrid Fast Extraction
- Try pdfplumber first (10-50x faster)
- Fall back to docling if validation fails
- Template-based extraction for known formats

#### 3.3 Selective Processing
- Fast page classification
- Process only transaction pages with docling
- Skip headers/footers/summaries

#### 3.4 Async Support
- Async/await API for Django
- ProcessPoolExecutor for CPU-bound work
- Progress callbacks

#### 3.5 Batch Processing
- Parallel processing with multiprocessing
- Progress bars with tqdm

**Expected Results:**
- 2-10x speedup with caching
- 10-50x speedup with hybrid approaches
- Instant for repeated processing

**See:**
- [docs/implementation/phase-3-performance.md](docs/implementation/phase-3-performance.md)
- [docs/implementation/hybrid-approaches.md](docs/implementation/hybrid-approaches.md)

---

### PHASE 4: ML-Based Classification 🤖 (Priority: MEDIUM)
**Duration:** 7-15 days | **Impact:** HIGH - Automation

Replace hardcoded rules with machine learning:

#### 4.1 Bank Format Detection
- Train classifier on document features
- Automatic bank identification
- Confidence scores

#### 4.2 Transaction Classification (NER)
- Use spaCy or transformers for entity extraction
- Extract payer/payee with ML instead of regex
- Italian banking terminology model

#### 4.3 Transaction Categorization
- Zero-shot classification
- Custom category classifier
- User-defined categories

**See:** [docs/implementation/phase-4-ml.md](docs/implementation/phase-4-ml.md)

---

### PHASE 5: Django/Web Integration 🌐 (Priority: MEDIUM)
**Duration:** 5-10 days | **Impact:** HIGH - Production readiness

Make it production-ready for Django applications:

#### 5.1 Django Package
- Django models for storing results
- File upload views
- Celery tasks for background processing
- REST API with DRF
- WebSocket support for progress
- Django admin integration

#### 5.2 Web UI (Optional)
- Upload interface
- Transaction listing/filtering
- Export functionality
- Dashboard with statistics

**See:** [docs/implementation/phase-5-django.md](docs/implementation/phase-5-django.md)

---

### PHASE 6: Production Readiness 🚀 (Priority: MEDIUM)
**Duration:** 3-7 days | **Impact:** MEDIUM - Quality

#### 6.1 CI/CD Pipeline
- GitHub Actions for testing
- Automated linting (pylint, ruff, mypy)
- Code coverage reporting
- Automated releases
- Security scanning

#### 6.2 Documentation
- API docs with Sphinx/MkDocs
- Comprehensive examples
- Video tutorials
- Provider creation guide
- Troubleshooting guide

#### 6.3 Packaging & Distribution
- Publish to PyPI
- Docker image
- Version management
- CHANGELOG.md
- Release notes automation

---

### PHASE 7: Advanced Features ✨ (Priority: LOW)
**Duration:** 10-20 days | **Impact:** MEDIUM - Enhancement

#### 7.1 Advanced Analytics
- Spending analytics and trends
- Anomaly detection
- Budget tracking
- Visualization
- Recurring transaction detection

#### 7.2 Multi-Format Support
- CSV bank exports
- Excel exports
- QIF format (Quicken)
- OFX format (Open Financial Exchange)

#### 7.3 Data Privacy & Security
- Encryption for stored PDFs
- PII redaction options
- GDPR compliance features
- Audit logging
- Data retention policies

---

## 🎯 Recommended Implementation Order

### Immediate (Weeks 1-2)
1. ✅ **Phase 1**: Fix bugs, stabilize (2 days)
2. ✅ **Phase 2**: Multi-provider architecture (4 days)
3. ✅ **Phase 3.2**: Caching (2 days)
4. ✅ **Phase 3.3**: Async support (3 days)

**Why:** Fixes critical issues, enables multi-bank support, speeds up processing

### Short-term (Months 1-2)
5. **Phase 5.1**: Django integration (7 days)
6. **Phase 3.1**: Hybrid extraction (3 days)
7. **Phase 6.1**: CI/CD (2 days)
8. **Phase 2.2**: Configuration system (2 days)

**Why:** Production-ready for Django applications

### Medium-term (Months 2-4)
9. **Phase 4.1**: ML bank detection (7 days)
10. **Phase 6.2**: Documentation (5 days)
11. **Phase 7.3**: Security features (7 days)

**Why:** Automation and security for production use

### Long-term (Months 4+)
12. **Phase 4.2-4.3**: Advanced ML features (10+ days)
13. **Phase 7.1**: Analytics (10 days)
14. **Phase 5.2**: Web UI (10 days)

**Why:** Nice-to-have enhancements after core is solid

---

## 📈 Expected Outcomes

After implementing priority phases:

| Metric | Current | After Phase 1-2 | After Phase 1-5 |
|--------|---------|-----------------|-----------------|
| Supported banks | 1 | 3-5 | 10+ (with ML) |
| Processing speed | X | X (same) | 10-100x faster |
| Django-ready | No | No | Yes |
| Production-ready | No | No | Yes |
| Extensibility | Low | High | Very High |

---

## 🤔 Key Architectural Decisions

### 1. Provider Architecture
**Decision:** Compiled providers initially, plugin support later
**Rationale:** Simpler to implement, easier to test, sufficient for most use cases

### 2. Performance Strategy
**Decision:** Hybrid approach (fast methods + docling fallback)
**Rationale:** Docling's core speed is limited by algorithms. Avoiding it when possible is more effective than optimizing it.

### 3. ML Model Hosting
**Decision:** Optional dependency, download on first use
**Rationale:** Keeps package size small, users without ML needs don't pay the cost

### 4. Caching Strategy
**Decision:** File-based cache for CLI, Django ORM for web app
**Rationale:** Different use cases need different persistence mechanisms

### 5. API Design
**Decision:** Sync-first with async wrappers
**Rationale:** Backward compatible, most users expect synchronous APIs

---

## 📚 Documentation Structure

```
docs/
├── implementation/
│   ├── phase-1-bugfixes.md          # Detailed Phase 1 specs
│   ├── phase-2-providers.md         # Provider architecture design
│   ├── phase-3-performance.md       # Performance optimization guide
│   ├── hybrid-approaches.md         # Hybrid extraction strategies
│   ├── phase-4-ml.md                # ML implementation specs
│   └── phase-5-django.md            # Django integration guide
├── guides/
│   ├── adding-a-provider.md         # How to add new bank support
│   ├── performance-tuning.md        # Performance optimization guide
│   └── django-integration.md        # Using with Django
└── architecture/
    ├── provider-system.md           # Provider architecture details
    └── data-flow.md                 # Data processing pipeline
```

---

## 🚀 Getting Started

1. **Review this roadmap** to understand the overall plan
2. **Check [TASKS.md](TASKS.md)** for granular, agent-ready tasks
3. **Read phase documentation** in `docs/implementation/` for detailed specs
4. **Pick a task** and create an issue/PR
5. **Implement and test** following the specifications
6. **Submit PR** linking to the tracking issue

---

## 📞 Questions & Discussion

For questions or discussions about this roadmap:
- Open an issue with the `roadmap` label
- Reference specific phase documentation
- Propose alternatives with clear rationale

---

**Last Updated:** 2026-01-18
**Status:** Draft - Ready for review and implementation
