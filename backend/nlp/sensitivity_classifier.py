from sentence_transformers import SentenceTransformer, util
import torch
from dataclasses import dataclass
from typing import Dict, List, Tuple
from utils.logger import logger
from utils.gpu_utils import get_gpu_info

@dataclass
class SensitivityResult:
    category: str
    confidence: float
    reason: str
    document_type: str = "Unknown"

class SensitivityClassifier:
    def __init__(self):
        logger.info("Initializing NLP Sensitivity Classifier...")
        
        gpu_info = get_gpu_info()
        self.device = 'cuda' if gpu_info['pytorch_cuda'] else 'cpu'
        
        # Load lightweight embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2', device=self.device)
        logger.info(f"Loaded sentence-transformers model on {self.device}")
        
        # Define reference sentences for each category
        self.categories = {
            'safe': [
                "YouTube videos, movies, games, and entertainment",
                "Spotify music playlists and audio streaming",
                "casual browsing, social media scrolling, and Reddit",
                "general knowledge Wikipedia article and weather forecast",
                "public news article and reading"
            ],
            'medium': [
                "programming tutorial and technical documentation",
                "VS Code, PyCharm, or IntelliJ IDE coding session",
                "stack overflow debugging and software development",
                "college assignments and general emails",
                "casual emails and communication"
            ],
            'highly_confidential': [
                "ChatGPT, Gemini, Antigravity, or Claude AI chat interface",
                "bank account statement with balance and transaction history",
                "salary payroll spreadsheet and compensation details",
                "password manager vault with login credentials",
                "confidential company projects, resume, and CV",
                "API keys, authentication tokens and secret credentials",
                "social security number and personal identification"
            ]
        }
        
        # Pre-compute embeddings for references
        self.reference_embeddings = {}
        for category, texts in self.categories.items():
            self.reference_embeddings[category] = self.model.encode(texts, convert_to_tensor=True)
            
        # Fast-path keyword matching for robustness
        self.critical_keywords = [
            "chatgpt", "gemini", "antigravity", "claude", "openai", "copilot", 
            "confidential", "bank", "financial", "salary", "ssn", "password", 
            "secret", "api key", "resume", "cv", "credit card"
        ]
        
        self.medium_keywords = [
            "vs code", "vscode", "pycharm", "intellij", "studio", "github", "stack overflow"
        ]
        
    def _check_keywords(self, text: str) -> str:
        text_lower = text.lower()
        for kw in self.critical_keywords:
            if kw in text_lower:
                return "highly_confidential"
        for kw in self.medium_keywords:
            if kw in text_lower:
                return "medium"
        return "unknown"
            
    def classify(self, text: str, window_title: str = "") -> SensitivityResult:
        """
        Semantically classify text sensitivity using a hybrid keyword + semantic approach.
        """
        combined_text = f"{window_title}\n{text}" if window_title else text
        
        if not combined_text or len(combined_text.strip()) < 5:
            return SensitivityResult('safe', 1.0, "Insufficient text to analyze")
            
        # Fast path: check for obvious high-privacy keywords in the window title or text
        keyword_result = self._check_keywords(combined_text)
        if keyword_result == "highly_confidential":
            return SensitivityResult(
                category="highly_confidential",
                confidence=1.0,
                reason="High-privacy keyword detected (e.g. AI chat, financial, or confidential document).",
                document_type=window_title
            )
        elif keyword_result == "medium":
            return SensitivityResult(
                category="medium",
                confidence=1.0,
                reason="Medium-privacy keyword detected (e.g. coding IDE, technical docs).",
                document_type=window_title
            )
            
        # Optional: truncate text if it's too long to save computation
        max_chars = 2000
        if len(combined_text) > max_chars:
            combined_text = combined_text[:max_chars]
            
        # Encode the input text
        text_embedding = self.model.encode(combined_text, convert_to_tensor=True)
        
        best_category = 'safe'
        best_score = 0.0
        
        # Calculate cosine similarity against all references
        for category, ref_embeddings in self.reference_embeddings.items():
            # Calculate similarities against all references in this category
            cos_scores = util.cos_sim(text_embedding, ref_embeddings)[0]
            # Take the maximum similarity score for this category
            max_score = torch.max(cos_scores).item()
            
            if max_score > best_score:
                best_score = max_score
                best_category = category
                
        # Generate a simple reason
        reason_map = {
            'safe': "Content appears to be general, public, or entertainment.",
            'medium': "Content appears to be technical, coding, or work-related.",
            'highly_confidential': "Content contains highly sensitive financial, medical, AI chat, or security data."
        }
        
        reason = reason_map.get(best_category, "")
        
        return SensitivityResult(
            category=best_category,
            confidence=float(best_score),
            reason=reason,
            document_type=window_title if window_title else "general"
        )
