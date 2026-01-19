# Phase 4: ML-Based Classification

**Priority:** MEDIUM
**Duration:** 7-15 days
**Impact:** HIGH - Automation and accuracy

## Overview

Replace hardcoded rules with machine learning for automatic bank detection, entity extraction, and transaction categorization.

---

## Task 4.1: ML-Based Bank Detection

### Overview

**Duration:** 5-7 days
**Impact:** HIGH - Automatic multi-bank support

Train a classifier to automatically detect bank format from PDF structure.

### Implementation

#### estrattoconto/ml/detector.py

```python
"""ML-based bank format detection."""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
from typing import Dict, Tuple
from docling.document_converter import ConversionResult


class MLBankDetector:
    """ML classifier for bank format detection."""

    def __init__(self, model_path: str = None):
        if model_path:
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(model_path.replace('.pkl', '_scaler.pkl'))
        else:
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.scaler = StandardScaler()

    def extract_features(self, document: ConversionResult) -> Dict[str, float]:
        """
        Extract features from document for classification.

        Features:
        - Number of tables
        - Number of pages
        - Text density
        - Table structure patterns
        - Keyword presence
        """
        features = {}

        # Table features
        features['num_tables'] = len(document.document.tables)
        features['avg_table_rows'] = np.mean([
            len(t.export_to_dataframe()) for t in document.document.tables
        ]) if document.document.tables else 0

        # Text features
        texts = document.document.texts
        features['num_text_blocks'] = len(texts)
        features['avg_text_length'] = np.mean([
            len(t.text) for t in texts
        ]) if texts else 0

        # Keyword features
        all_text = ' '.join([t.text for t in texts])
        keywords = {
            'has_estratto_conto': 'ESTRATTO CONTO' in all_text,
            'has_saldo': 'SALDO' in all_text,
            'has_bonifico': 'BONIFICO' in all_text,
            'has_addebito': 'ADDEBITO' in all_text,
        }
        features.update({k: float(v) for k, v in keywords.items()})

        # Layout features
        if document.document.tables:
            first_table = document.document.tables[0].export_to_dataframe()
            features['first_table_cols'] = len(first_table.columns)
            features['first_table_rows'] = len(first_table)

        return features

    def predict(self, document: ConversionResult) -> Tuple[str, float]:
        """
        Predict bank type.

        Returns:
            (bank_name, confidence) tuple
        """
        features = self.extract_features(document)
        feature_vector = self._dict_to_vector(features)

        # Scale and predict
        feature_scaled = self.scaler.transform([feature_vector])
        proba = self.model.predict_proba(feature_scaled)[0]

        bank_idx = np.argmax(proba)
        bank_name = self.model.classes_[bank_idx]
        confidence = proba[bank_idx]

        return bank_name, confidence

    def _dict_to_vector(self, features: Dict) -> np.ndarray:
        """Convert feature dict to vector."""
        # Ensure consistent ordering
        feature_names = sorted(features.keys())
        return np.array([features[name] for name in feature_names])

    def train(self, X: list, y: list):
        """
        Train the model.

        Args:
            X: List of feature dictionaries
            y: List of bank names
        """
        # Convert to vectors
        X_vectors = [self._dict_to_vector(x) for x in X]

        # Scale
        X_scaled = self.scaler.fit_transform(X_vectors)

        # Train
        self.model.fit(X_scaled, y)

    def save(self, path: str):
        """Save model to disk."""
        joblib.dump(self.model, path)
        joblib.dump(self.scaler, path.replace('.pkl', '_scaler.pkl'))
```

### Training Data Collection

```python
# scripts/collect_training_data.py
"""Collect training data for ML bank detector."""

import json
from pathlib import Path
from estrattoconto.ml.detector import MLBankDetector
from docling.document_converter import DocumentConverter

def collect_training_data(pdf_dirs: dict) -> tuple:
    """
    Collect features from labeled PDFs.

    Args:
        pdf_dirs: Dict mapping bank name to directory of PDFs
                  e.g., {'CENTROVENETO': 'data/centroveneto/'}

    Returns:
        (features, labels) tuple
    """
    detector = MLBankDetector()
    converter = DocumentConverter()

    X = []  # Features
    y = []  # Labels

    for bank_name, pdf_dir in pdf_dirs.items():
        pdf_path = Path(pdf_dir)

        for pdf_file in pdf_path.glob('*.pdf'):
            print(f"Processing {pdf_file.name}...")

            # Convert
            result = converter.convert(str(pdf_file))

            # Extract features
            features = detector.extract_features(result)

            X.append(features)
            y.append(bank_name)

    return X, y

# Usage:
# X, y = collect_training_data({
#     'CENTROVENETO': 'training_data/centroveneto/',
#     'INTESA_SANPAOLO': 'training_data/intesa/',
#     'UNICREDIT': 'training_data/unicredit/',
# })
# detector.train(X, y)
# detector.save('models/bank_detector.pkl')
```

### Integration with Provider System

```python
# Update providers/__init__.py
from ..ml.detector import MLBankDetector

class MLProviderRegistry(ProviderRegistry):
    """Registry with ML-based detection."""

    def __init__(self, model_path: str = None):
        super().__init__()
        self.ml_detector = MLBankDetector(model_path) if model_path else None

    def detect_provider(self, document, min_confidence=0.8):
        """Detect using ML first, fall back to rule-based."""
        if self.ml_detector:
            bank_name, confidence = self.ml_detector.predict(document)

            if confidence >= min_confidence:
                provider = self.get_provider_by_name(bank_name.lower())
                if provider:
                    print(f"✓ ML detected: {bank_name} ({confidence:.2%})")
                    return provider

        # Fall back to rule-based detection
        return super().detect_provider(document, min_confidence)
```

### Acceptance Criteria
- [ ] MLBankDetector implemented
- [ ] Feature extraction comprehensive
- [ ] Training script created
- [ ] Integration with provider system
- [ ] Model evaluation metrics
- [ ] Documentation for training

---

## Task 4.2: NER for Entity Extraction

### Overview

**Duration:** 7-10 days
**Impact:** MEDIUM-HIGH - More accurate extraction

Use Named Entity Recognition to extract payer/payee instead of regex.

### Implementation

```python
# estrattoconto/ml/ner.py
"""NER-based entity extraction."""

import spacy
from typing import Dict, Optional

class BankingNER:
    """NER for banking entities."""

    def __init__(self, model_name: str = "it_core_news_lg"):
        # Load Italian spaCy model
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            print(f"Downloading {model_name}...")
            import subprocess
            subprocess.run(['python', '-m', 'spacy', 'download', model_name])
            self.nlp = spacy.load(model_name)

    def extract_entities(self, description: str) -> Dict[str, Optional[str]]:
        """
        Extract entities from transaction description.

        Returns:
            Dictionary with 'payer', 'payee', 'amount', etc.
        """
        doc = self.nlp(description)

        entities = {
            'payer': None,
            'payee': None,
            'organization': None,
            'amount': None,
        }

        # Extract named entities
        for ent in doc.ents:
            if ent.label_ == 'PER':  # Person
                if not entities['payer']:
                    entities['payer'] = ent.text
                elif not entities['payee']:
                    entities['payee'] = ent.text

            elif ent.label_ == 'ORG':  # Organization
                entities['organization'] = ent.text

            elif ent.label_ == 'MONEY':
                entities['amount'] = ent.text

        # Fallback to pattern matching if NER fails
        if not entities['payer']:
            entities['payer'] = self._pattern_extract_payer(description)

        return entities

    def _pattern_extract_payer(self, text: str) -> Optional[str]:
        """Fallback pattern matching."""
        import re
        match = re.search(r'Ordinante:\s*(.*?)\s*Causale', text)
        return match.group(1) if match else None
```

### Acceptance Criteria
- [ ] BankingNER implemented
- [ ] Italian spaCy model integrated
- [ ] Fallback to regex patterns
- [ ] Comparison with regex accuracy
- [ ] Tests added

---

## Task 4.3: Transaction Categorization

### Overview

**Duration:** 4-5 days
**Impact:** MEDIUM - Better insights

Automatic transaction categorization using ML.

### Implementation

```python
# estrattoconto/ml/categorizer.py
"""ML-based transaction categorization."""

from transformers import pipeline

class TransactionCategorizer:
    """Categorize transactions using transformers."""

    def __init__(self):
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )

        self.categories = [
            "bill payment",
            "salary",
            "bank fee",
            "transfer",
            "withdrawal",
            "deposit",
            "subscription",
            "purchase",
            "refund",
        ]

    def categorize(self, description: str) -> Dict:
        """
        Categorize transaction.

        Returns:
            Dict with category and confidence
        """
        result = self.classifier(
            description,
            self.categories,
            multi_label=False
        )

        return {
            'category': result['labels'][0],
            'confidence': result['scores'][0],
            'all_categories': dict(zip(result['labels'], result['scores']))
        }

    def categorize_bulk(self, descriptions: list) -> list:
        """Categorize multiple transactions."""
        return [self.categorize(desc) for desc in descriptions]
```

### Acceptance Criteria
- [ ] TransactionCategorizer implemented
- [ ] Categories defined
- [ ] Bulk categorization support
- [ ] Integration with enrichment
- [ ] Tests added

---

## Summary Checklist

Phase 4 complete when:

- [ ] ML bank detector implemented and trained
- [ ] NER for entity extraction implemented
- [ ] Transaction categorization implemented
- [ ] All integrated with existing code
- [ ] Model training documented
- [ ] Performance comparison with rule-based
- [ ] Tests passing

---

**Next:** [Phase 5: Django Integration](phase-5-django.md)
