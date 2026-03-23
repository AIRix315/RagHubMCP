"""RAG Pipeline Evaluation Module.

This module provides utilities for evaluating RAG pipeline quality,
including metrics calculation and test question datasets.

Reference:
- Docs/12-V2-Blueprint.md (Section 3: 验证体系)
- RULE.md (Section 7: 测试验收标准)
"""

from .metrics import (
    EvaluationResult,
    calculate_noise_ratio,
    calculate_relevance_score,
    calculate_top_k_hit_rate,
    evaluate_pipeline,
)
from .questions import (
    TEST_QUESTIONS,
    get_question_by_id,
    get_questions_by_category,
    get_test_questions,
)

__all__ = [
    "EvaluationResult",
    "calculate_noise_ratio",
    "calculate_relevance_score",
    "calculate_top_k_hit_rate",
    "evaluate_pipeline",
    "get_test_questions",
    "get_questions_by_category",
    "get_question_by_id",
    "TEST_QUESTIONS",
]
