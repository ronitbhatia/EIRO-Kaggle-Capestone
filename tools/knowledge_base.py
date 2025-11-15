"""
Knowledge Base Tool - Custom tool for searching internal documentation.

This tool demonstrates how agents can access organizational knowledge
to help resolve incidents.
"""

from typing import Dict, Any, List
import re


# Simulated knowledge base articles
KNOWLEDGE_BASE = [
    {
        "id": "KB-001",
        "title": "Database Connection Timeout Resolution",
        "category": "database",
        "content": "If experiencing database connection timeouts, check: 1) Connection pool size, 2) Network latency, 3) Database server load. Solution: Increase pool size or add read replicas.",
        "tags": ["database", "timeout", "connection", "performance"]
    },
    {
        "id": "KB-002",
        "title": "API Rate Limiting Issues",
        "category": "api",
        "content": "API rate limiting can cause 429 errors. Check API key quotas, implement exponential backoff, or request quota increase from provider.",
        "tags": ["api", "rate-limit", "429", "quota"]
    },
    {
        "id": "KB-003",
        "title": "Cache Invalidation Best Practices",
        "category": "cache",
        "content": "When cache becomes stale, invalidate using TTL or manual invalidation. For distributed caches, use cache tags or pub/sub invalidation.",
        "tags": ["cache", "invalidation", "stale-data"]
    },
    {
        "id": "KB-004",
        "title": "Message Queue Backlog Resolution",
        "category": "messaging",
        "content": "If message queue has backlog, scale consumers, check consumer health, or increase processing capacity. Monitor queue depth metrics.",
        "tags": ["queue", "backlog", "scaling", "messaging"]
    },
    {
        "id": "KB-005",
        "title": "File Storage Access Denied",
        "category": "storage",
        "content": "Access denied errors usually indicate permission issues. Check IAM roles, file permissions, or service account credentials.",
        "tags": ["storage", "permissions", "access-denied", "iam"]
    }
]


def search_knowledge_base(query: str, category: str = None) -> List[Dict[str, Any]]:
    """
    Search knowledge base articles by query string.
    
    Args:
        query: Search query
        category: Optional category filter
        
    Returns:
        List of matching knowledge base articles
    """
    query_lower = query.lower()
    results = []
    
    for article in KNOWLEDGE_BASE:
        if category and article["category"] != category:
            continue
        
        # Simple keyword matching
        score = 0
        query_words = query_lower.split()
        
        # Check title match
        if any(word in article["title"].lower() for word in query_words):
            score += 3
        
        # Check content match
        if any(word in article["content"].lower() for word in query_words):
            score += 2
        
        # Check tag match
        if any(word in " ".join(article["tags"]).lower() for word in query_words):
            score += 1
        
        if score > 0:
            results.append({
                **article,
                "relevance_score": score
            })
    
    # Sort by relevance
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results[:5]  # Return top 5


def get_article(article_id: str) -> Dict[str, Any]:
    """
    Get a specific knowledge base article by ID.
    
    Args:
        article_id: Article ID (e.g., "KB-001")
        
    Returns:
        Article details or None if not found
    """
    for article in KNOWLEDGE_BASE:
        if article["id"] == article_id:
            return article
    return None


def get_articles_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Get all articles in a category.
    
    Args:
        category: Category name
        
    Returns:
        List of articles in that category
    """
    return [article for article in KNOWLEDGE_BASE if article["category"] == category]

