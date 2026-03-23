"""BM25Scorer implementation for lexical matching.

This module implements the BM25 (Best Matching 25) scoring algorithm,
which is a probabilistic ranking function used for information retrieval.

Reference:
- Docs/20-RerankEngine-Architecture.md Section 11.3
- SylphxAI/coderag: tfidf.ts#L265-L339
- Elasticsearch BM25: https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules-similarity.html

BM25 Formula:
    score(D, Q) = sum(IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgDl)))

Where:
    - IDF(qi) = log((N - n(qi) + 0.5) / (n(qi) + 0.5) + 1)  [Smoothed IDF]
    - f(qi, D) = term frequency of qi in document D
    - |D| = document length
    - avgDl = average document length in the corpus
    - k1 = term frequency saturation parameter (default 1.2)
    - b = document length normalization parameter (default 0.75)
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from typing import Any

import numpy as np

from ..core.scorer import BaseScorer

logger = logging.getLogger(__name__)


class BM25Scorer(BaseScorer):
    """BM25 scoring component.

    Computes relevance scores using the BM25 algorithm, which provides:
    - Term frequency saturation (controlled by k1)
    - Document length normalization (controlled by b)
    - Smoothed IDF to avoid zero weights for rare terms

    Attributes:
        k1: Term frequency saturation parameter (default 1.2)
        b: Document length normalization parameter (default 0.75)

    Example:
        >>> scorer = BM25Scorer(k1=1.2, b=0.75)
        >>> scores = scorer.compute_scores("machine learning", docs)
    """

    def __init__(self, k1: float = 1.2, b: float = 0.75):
        """Initialize BM25Scorer.

        Args:
            k1: Term frequency saturation parameter. Higher values mean
                term frequency has more influence. Default 1.2 (Elasticsearch default).
            b: Document length normalization parameter. 0 means no normalization,
                1 means full normalization. Default 0.75 (Elasticsearch default).
        """
        self.k1 = k1
        self.b = b
        self._idf_cache: dict[str, float] = {}
        self._avg_doc_len: float = 0.0
        self._doc_count: int = 0

    @property
    def name(self) -> str:
        """Scorer name identifier."""
        return "bm25"

    @property
    def supports_batch(self) -> bool:
        """BM25Scorer supports batch processing."""
        return True

    def compute_scores(
        self,
        query: str,
        documents: list[str],
    ) -> np.ndarray:
        """Compute BM25 relevance scores for query-document pairs.

        Args:
            query: The search query string.
            documents: List of document texts to score.

        Returns:
            NumPy array of shape (len(documents),) with scores normalized to [0, 1].
        """
        if not documents:
            return np.array([])

        if not query or not query.strip():
            return np.zeros(len(documents))

        # Tokenize query
        query_terms = self._tokenize(query)
        if not query_terms:
            return np.zeros(len(documents))

        # Precompute document statistics
        doc_tokens = [self._tokenize(doc) for doc in documents]
        doc_lengths = [len(tokens) for tokens in doc_tokens]
        avg_doc_len = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1.0

        # Compute term frequencies for each document
        doc_term_freqs = [Counter(tokens) for tokens in doc_tokens]

        # Compute document frequencies for query terms
        doc_freqs: dict[str, int] = {}
        for term in set(query_terms):
            doc_freqs[term] = sum(1 for tf in doc_term_freqs if term in tf)

        # Number of documents
        num_docs = len(documents)

        # Compute scores
        scores = np.zeros(len(documents))

        for i, (term_freq, doc_len) in enumerate(zip(doc_term_freqs, doc_lengths)):
            score = 0.0

            for term in query_terms:
                tf = term_freq.get(term, 0)
                if tf == 0:
                    continue

                # Compute IDF with smoothing
                df = doc_freqs.get(term, 0)
                idf = self._compute_idf(df, num_docs)

                # BM25 term score
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / avg_doc_len)

                score += idf * (numerator / denominator)

            scores[i] = score

        # Normalize scores to [0, 1]
        scores = self._normalize_scores(scores)

        return scores

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into lowercase terms.

        Handles both English (word-based) and CJK (character-based) text.
        For CJK characters, we tokenize by individual characters since
        they don't use whitespace as word boundaries.

        Args:
            text: Input text to tokenize.

        Returns:
            List of lowercase tokens.
        """
        text = text.lower()
        tokens = []

        # Split on whitespace and punctuation, keeping alphanumeric
        words = re.findall(r"\w+", text, re.UNICODE)

        for word in words:
            # Check if word contains CJK characters (Unicode range U+4E00-U+9FFF)
            if re.search(r"[\u4e00-\u9fff]", word):
                # For CJK text, split into individual characters
                # This is a simple approach; production systems may use jieba or similar
                cjk_chars = [c for c in word if "\u4e00" <= c <= "\u9fff"]
                tokens.extend(cjk_chars)
                # Also keep the full word for potential matching
                if len(word) > 1:
                    tokens.append(word)
            else:
                tokens.append(word)

        return tokens

    def _compute_idf(self, doc_freq: int, num_docs: int) -> float:
        """Compute smoothed IDF (Inverse Document Frequency).

        Uses BM25's smoothed IDF formula to avoid zero weights for rare terms:
            IDF = log((N - n + 0.5) / (n + 0.5) + 1)

        This ensures:
        - Rare terms (n ≈ 0) get IDF ≈ log(N + 0.5)
        - Common terms (n ≈ N) get IDF ≈ log(1.5) ≈ 0.405
        - No term gets zero weight

        Args:
            doc_freq: Number of documents containing the term.
            num_docs: Total number of documents.

        Returns:
            Smoothed IDF value.
        """
        if num_docs == 0:
            return 0.0

        # BM25 smoothed IDF formula
        idf = math.log((num_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
        return max(0.0, idf)  # Ensure non-negative

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Normalize scores to [0, 1] range using min-max normalization.

        Args:
            scores: Raw BM25 scores.

        Returns:
            Normalized scores in [0, 1] range.
        """
        if len(scores) == 0:
            return scores

        min_score = float(np.min(scores))
        max_score = float(np.max(scores))

        if max_score == min_score:
            # All scores are the same
            return np.ones_like(scores) if max_score > 0 else np.zeros_like(scores)

        # Min-max normalization
        normalized: np.ndarray = (scores - min_score) / (max_score - min_score)
        return normalized

    def get_config(self) -> dict[str, Any]:
        """Get scorer configuration for logging/debugging.

        Returns:
            Dictionary with scorer configuration.
        """
        return {
            "name": self.name,
            "supports_batch": self.supports_batch,
            "k1": self.k1,
            "b": self.b,
        }
