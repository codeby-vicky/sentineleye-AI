import re
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ContextResult:
    document_type: str
    density_score: float
    keywords_found: List[str]

class ContextAnalyzer:
    def __init__(self):
        # Patterns for detecting document types
        self.patterns = {
            'code': [r'def\s+\w+\s*\(', r'function\s+\w+\s*\(', r'class\s+\w+', r'import\s+\w+', r'#include'],
            'email': [r'From:', r'To:', r'Subject:', r'Regards,'],
            'financial': [r'\$\d+', r'Balance', r'Account Number', r'Invoice', r'Total Amount'],
            'resume': [r'Experience', r'Education', r'Skills', r'Phone:', r'Email:']
        }
        
    def analyze(self, text: str) -> ContextResult:
        """Analyze text structure and content to provide context hints."""
        if not text:
            return ContextResult("Unknown", 0.0, [])
            
        doc_type = "Unknown"
        max_matches = 0
        found_keywords = []
        
        # Determine document type by regex pattern matching
        for dtype, patterns in self.patterns.items():
            matches = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
            if matches > max_matches and matches >= 2:  # Need at least 2 matches to be confident
                max_matches = matches
                doc_type = dtype.capitalize()
                
        # Calculate information density (non-whitespace chars / total chars)
        total_chars = len(text)
        if total_chars > 0:
            density = len(re.sub(r'\s+', '', text)) / total_chars
        else:
            density = 0.0
            
        return ContextResult(doc_type, density, found_keywords)
