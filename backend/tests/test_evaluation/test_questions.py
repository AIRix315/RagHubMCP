"""RAG Evaluation test questions.

This module provides a collection of test questions for evaluating
RAG pipeline quality.

Reference:
- Docs/12-V2-Blueprint.md (Section 3.1)
- RULE.md (Section 7: 测试验收标准)
"""

from typing import Any


# Test questions for evaluation
# Format: (question, category, expected_keywords)
TEST_QUESTIONS: list[dict[str, Any]] = [
    # Exact technical questions
    {
        "id": 1,
        "question": "How do I implement authentication in FastAPI?",
        "category": "exact",
        "keywords": ["auth", "login", "JWT", "token", "OAuth"],
    },
    {
        "id": 2,
        "question": "What is the best way to handle async database queries?",
        "category": "exact",
        "keywords": ["async", "database", "await", "connection"],
    },
    {
        "id": 3,
        "question": "How to set up CORS in FastAPI?",
        "category": "exact",
        "keywords": ["CORS", "middleware", "cross-origin"],
    },
    
    # Open-ended questions
    {
        "id": 4,
        "question": "What's the best practice for structuring a Python project?",
        "category": "open",
        "keywords": ["structure", "organization", "best practice"],
    },
    {
        "id": 5,
        "question": "How does RAG improve LLM responses?",
        "category": "open",
        "keywords": ["RAG", "retrieval", "LLM", "context"],
    },
    
    # Long-form questions requiring context
    {
        "id": 6,
        "question": "Explain how the HybridSearchService combines vector and BM25 search, including the RRF algorithm and score normalization.",
        "category": "long",
        "keywords": ["HybridSearch", "RRF", "BM25", "vector", "fusion"],
    },
    {
        "id": 7,
        "question": "What are the differences between Chroma and Qdrant vector databases, and when should I use each?",
        "category": "long",
        "keywords": ["Chroma", "Qdrant", "vector database", "comparison"],
    },
    
    # Implementation-specific questions
    {
        "id": 8,
        "question": "How do I add a custom MCP tool to the server?",
        "category": "exact",
        "keywords": ["MCP", "tool", "register", "FastMCP"],
    },
    {
        "id": 9,
        "question": "What's the difference between FlashRank and Cohere for reranking?",
        "category": "exact",
        "keywords": ["FlashRank", "Cohere", "rerank", "comparison"],
    },
    {
        "id": 10,
        "question": "How to configure chunking for code documentation?",
        "category": "exact",
        "keywords": ["chunk", "split", "code", "AST"],
    },
    
    # Edge cases
    {
        "id": 11,
        "question": "What happens when the vector database is empty?",
        "category": "edge",
        "keywords": ["empty", "no results", "fallback"],
    },
    {
        "id": 12,
        "question": "How to handle very long queries in RAG?",
        "category": "edge",
        "keywords": ["long query", "truncation", "limit"],
    },
    
    # Integration questions
    {
        "id": 13,
        "question": "How do I integrate RagHubMCP with Cursor IDE?",
        "category": "exact",
        "keywords": ["Cursor", "MCP", "config", "IDE"],
    },
    {
        "id": 14,
        "question": "What's the process for adding a new embedding provider?",
        "category": "exact",
        "keywords": ["embedding", "provider", "interface"],
    },
    
    # Performance questions
    {
        "id": 15,
        "question": "How does the rerank step impact query latency?",
        "category": "open",
        "keywords": ["performance", "latency", "rerank", "speed"],
    },
    
    # Debugging questions
    {
        "id": 16,
        "question": "How do I debug a failed indexing operation?",
        "category": "exact",
        "keywords": ["debug", "indexing", "error", "log"],
    },
    
    # Configuration questions
    {
        "id": 17,
        "question": "What profile should I use for maximum accuracy?",
        "category": "exact",
        "keywords": ["profile", "accurate", "configuration"],
    },
    {
        "id": 18,
        "question": "How to switch between Chroma and Qdrant?",
        "category": "exact",
        "keywords": ["Chroma", "Qdrant", "switch", "config"],
    },
    
    # Advanced questions
    {
        "id": 19,
        "question": "How does reciprocal rank fusion work mathematically?",
        "category": "long",
        "keywords": ["RRF", "fusion", "formula", "ranking"],
    },
    {
        "id": 20,
        "question": "What's the difference between context window and token limit?",
        "category": "open",
        "keywords": ["context", "token", "window", "limit"],
    },
]


def get_test_questions() -> list[dict[str, Any]]:
    """Get all test questions.
    
    Returns:
        List of test question dictionaries.
    """
    return TEST_QUESTIONS


def get_questions_by_category(category: str) -> list[dict[str, Any]]:
    """Get questions filtered by category.
    
    Args:
        category: Category name (exact, open, long, edge).
        
    Returns:
        Filtered list of questions.
    """
    return [q for q in TEST_QUESTIONS if q.get("category") == category]


def get_question_by_id(question_id: int) -> dict[str, Any] | None:
    """Get a specific question by ID.
    
    Args:
        question_id: Question ID.
        
    Returns:
        Question dictionary or None if not found.
    """
    for q in TEST_QUESTIONS:
        if q.get("id") == question_id:
            return q
    return None