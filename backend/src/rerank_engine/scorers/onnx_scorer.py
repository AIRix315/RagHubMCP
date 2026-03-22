"""ONNXScorer - Local ONNX model-based rerank scoring.

This module provides a scorer that uses ONNX Runtime for efficient
CPU-based reranking without requiring PyTorch or GPU.

Reference: Docs/20-RerankEngine-Architecture.md Section 4.4.1
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from ..core.scorer import BaseScorer

logger = logging.getLogger(__name__)


class ONNXScorer(BaseScorer):
    """ONNX model-based rerank scorer.

    Uses ONNX Runtime for efficient, CPU-based document reranking.
    Supports FlashRank-format models (TinyBERT, MiniLM, etc.).

    Attributes:
        model_path: Path to ONNX model file.
        tokenizer_path: Path to tokenizer config file.
        max_length: Maximum token sequence length.
        batch_size: Batch size for inference.
        providers: ONNX execution providers.

    Example:
        >>> scorer = ONNXScorer(
        ...     model_path="./models/tinybert.onnx",
        ...     tokenizer_path="./models/tokenizer.json",
        ... )
        >>> scores = scorer.compute_scores("query", ["doc1", "doc2"])
    """

    def __init__(
        self,
        model_path: str,
        tokenizer_path: str,
        max_length: int = 512,
        batch_size: int = 32,
        providers: list[str] | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ONNX scorer.

        Args:
            model_path: Path to ONNX model file.
            tokenizer_path: Path to tokenizer JSON file.
            max_length: Maximum token sequence length.
            batch_size: Batch size for inference.
            providers: ONNX execution providers (default: CPU).
            config: Additional configuration.
        """
        self._model_path = Path(model_path)
        self._tokenizer_path = Path(tokenizer_path)
        self._max_length = max_length
        self._batch_size = batch_size
        self._config = config or {}
        self._providers = providers or ["CPUExecutionProvider"]

        # Lazy initialization
        self._session = None
        self._tokenizer = None

    @property
    def name(self) -> str:
        """Scorer name based on model file."""
        return f"onnx_{self._model_path.stem}"

    @property
    def supports_batch(self) -> bool:
        """ONNX scorer supports batch processing."""
        return True

    def _ensure_initialized(self) -> None:
        """Lazy initialization of model and tokenizer."""
        if self._session is not None:
            return

        try:
            import onnxruntime as ort

            # Create session
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = (
                ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            )

            self._session = ort.InferenceSession(
                str(self._model_path),
                sess_options,
                providers=self._providers,
            )

            logger.info(f"Loaded ONNX model from {self._model_path}")

        except ImportError:
            raise ImportError(
                "onnxruntime is required for ONNXScorer. "
                "Install with: pip install onnxruntime"
            )

        try:
            from tokenizers import Tokenizer

            self._tokenizer = Tokenizer.from_file(str(self._tokenizer_path))
            self._tokenizer.enable_truncation(max_length=self._max_length)
            self._tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")

            logger.info(f"Loaded tokenizer from {self._tokenizer_path}")

        except ImportError:
            raise ImportError(
                "tokenizers is required for ONNXScorer. "
                "Install with: pip install tokenizers"
            )

    def compute_scores(
        self,
        query: str,
        documents: list[str],
    ) -> np.ndarray:
        """Compute relevance scores for query-document pairs.

        Args:
            query: The search query.
            documents: List of document texts to score.

        Returns:
            NumPy array of scores in [0, 1], higher is more relevant.
        """
        if not documents:
            return np.array([])

        self._ensure_initialized()

        all_scores = []

        # Process in batches
        for i in range(0, len(documents), self._batch_size):
            batch_docs = documents[i : i + self._batch_size]
            batch_scores = self._score_batch(query, batch_docs)
            all_scores.extend(batch_scores)

        return np.array(all_scores)

    def _score_batch(self, query: str, documents: list[str]) -> list[float]:
        """Score a batch of documents."""
        # Build query-document pairs
        pairs = [[query, doc] for doc in documents]

        # Tokenize
        encoded = self._tokenizer.encode_batch(pairs)
        input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)

        # Prepare ONNX inputs
        onnx_inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }

        # Check if token_type_ids is needed
        token_type_ids = np.array([e.type_ids for e in encoded], dtype=np.int64)
        if not np.all(token_type_ids == 0):
            onnx_inputs["token_type_ids"] = token_type_ids

        # Run inference
        outputs = self._session.run(None, onnx_inputs)
        logits = outputs[0]

        # Convert to scores
        scores = self._logits_to_scores(logits)

        return scores.tolist()

    def _logits_to_scores(self, logits: np.ndarray) -> np.ndarray:
        """Convert model logits to relevance scores.

        Handles two output formats:
        - Single output: Apply sigmoid
        - Two outputs: Apply softmax, take positive class probability
        """
        if logits.shape[1] == 1:
            # Sigmoid for single output
            return 1 / (1 + np.exp(-logits.flatten()))
        else:
            # Softmax for multi-class, take positive class
            exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
            probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
            return probs[:, 1]

    @staticmethod
    def _logits_to_scores_static(logits: np.ndarray) -> np.ndarray:
        """Static version for testing."""
        if logits.shape[1] == 1:
            return 1 / (1 + np.exp(-logits.flatten()))
        else:
            exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
            probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
            return probs[:, 1]

    def get_config(self) -> dict[str, Any]:
        """Get scorer configuration."""
        return {
            "name": self.name,
            "supports_batch": self.supports_batch,
            "model_path": str(self._model_path),
            "tokenizer_path": str(self._tokenizer_path),
            "max_length": self._max_length,
            "batch_size": self._batch_size,
            "providers": self._providers,
        }