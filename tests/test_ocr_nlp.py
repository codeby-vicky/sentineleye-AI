"""
Test suite for OCR and NLP modules.
Tests text extraction and sensitivity classification.
"""

import unittest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestSensitivityClassifier(unittest.TestCase):
    """Tests for the NLP SensitivityClassifier."""

    @classmethod
    def setUpClass(cls):
        """Initialize classifier (downloads model if needed)."""
        from nlp.sensitivity_classifier import SensitivityClassifier
        cls.classifier = SensitivityClassifier()

    def test_classifier_initialization(self):
        """Test classifier initializes correctly."""
        self.assertIsNotNone(self.classifier)

    def test_classify_safe_content(self):
        """Test that educational content is classified as safe."""
        text = "Python tutorial: How to use list comprehensions in Python programming language"
        result = self.classifier.classify(text)
        self.assertEqual(result.category, 'safe')

    def test_classify_personal_content(self):
        """Test that resume content is classified as personal."""
        text = "Resume: John Smith, Software Engineer. Experience: 5 years at Google. Skills: Python, Java. Phone: 555-0123. Email: john@email.com"
        result = self.classifier.classify(text)
        self.assertIn(result.category, ['personal', 'confidential'])

    def test_classify_confidential_content(self):
        """Test that API keys are classified as confidential."""
        text = "API_KEY=sk-proj-abc123def456 SECRET_TOKEN=ghp_xxxxxxxxxxxx DATABASE_PASSWORD=admin123"
        result = self.classifier.classify(text)
        self.assertIn(result.category, ['confidential', 'highly_confidential'])

    def test_classify_highly_confidential(self):
        """Test that financial data is classified as highly confidential."""
        text = "Bank Statement: Account 1234-5678. Balance: $45,230.00. Recent transactions: Salary deposit $5,000. Credit card payment $1,200."
        result = self.classifier.classify(text)
        self.assertEqual(result.category, 'highly_confidential')

    def test_classify_returns_reason(self):
        """Test that classification includes a reason."""
        text = "Employee salary: $85,000 per year. Performance bonus: $10,000."
        result = self.classifier.classify(text)
        self.assertIsNotNone(result.reason)
        self.assertGreater(len(result.reason), 0)

    def test_classify_empty_text(self):
        """Test classification of empty text."""
        result = self.classifier.classify("")
        self.assertIsNotNone(result)
        self.assertEqual(result.category, 'safe')

    def test_semantic_not_keyword(self):
        """Test that classification is semantic, not keyword-based."""
        # "bank" in river context should be safe
        text = "The children played on the bank of the river during the sunny afternoon."
        result = self.classifier.classify(text)
        self.assertEqual(result.category, 'safe')


class TestTextExtractor(unittest.TestCase):
    """Tests for the OCR TextExtractor."""

    @classmethod
    def setUpClass(cls):
        """Initialize text extractor."""
        from ocr.text_extractor import TextExtractor
        cls.extractor = TextExtractor()

    def test_extractor_initialization(self):
        """Test extractor initializes correctly."""
        self.assertIsNotNone(self.extractor)

    def test_extract_blank_image(self):
        """Test extraction from blank image."""
        blank = np.zeros((100, 400, 3), dtype=np.uint8)
        result = self.extractor.extract(blank)
        self.assertIsNotNone(result)
        self.assertIsInstance(result.full_text, str)

    def test_extract_returns_correct_format(self):
        """Test extraction result format."""
        img = np.zeros((100, 400, 3), dtype=np.uint8)
        result = self.extractor.extract(img)
        self.assertTrue(hasattr(result, 'full_text'))
        self.assertTrue(hasattr(result, 'blocks'))
        self.assertTrue(hasattr(result, 'extraction_time'))


if __name__ == '__main__':
    unittest.main()
