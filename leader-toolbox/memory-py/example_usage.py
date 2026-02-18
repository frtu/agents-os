"""
Example usage of the Memory System.

This script demonstrates how to use the memory system programmatically.
"""

import asyncio
import logging
from pathlib import Path
from memory import MemoryManager, load_memory_config
from memory.models import SearchOptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main example function."""
    logger.info("Memory System Example")
    logger.info("=" * 50)

    # Load configuration
    config = load_memory_config()
    logger.info(f"Loaded config with backend: {config.backend}")

    # Initialize memory manager
    manager = MemoryManager(config)
    await manager.initialize()
    logger.info("Memory system initialized")

    try:
        # Example 1: Ingest text content
        logger.info("\n1. Ingesting text content...")

        documents = [
            {
                "text": "Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
                "metadata": {"title": "Python Introduction", "category": "programming"}
            },
            {
                "text": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions without being explicitly programmed. Common algorithms include linear regression, decision trees, and neural networks.",
                "metadata": {"title": "Machine Learning Basics", "category": "ai"}
            },
            {
                "text": "FastAPI is a modern, fast web framework for building APIs with Python. It provides automatic validation, serialization, and documentation generation. It's built on top of Starlette and Pydantic.",
                "metadata": {"title": "FastAPI Overview", "category": "web"}
            }
        ]

        file_ids = []
        for doc in documents:
            file_id = await manager.ingest_text(doc["text"], doc["metadata"])
            file_ids.append(file_id)
            logger.info(f"  Ingested: {doc['metadata']['title']} (ID: {file_id[:8]}...)")

        # Example 2: Search for content
        logger.info("\n2. Searching memory...")

        search_queries = [
            "Python programming language",
            "machine learning algorithms",
            "web framework API",
            "artificial intelligence"
        ]

        for query in search_queries:
            logger.info(f"\n  Query: '{query}'")

            # Try different search modes
            for mode in ["vector", "keyword", "hybrid"]:
                options = SearchOptions(
                    mode=mode,
                    max_results=3,
                    min_score=0.2
                )

                results = await manager.search(query, options)
                logger.info(f"    {mode.capitalize()} search: {len(results)} results")

                if results:
                    best_result = results[0]
                    logger.info(f"      Best: {best_result.metadata.get('title', 'Untitled')} "
                              f"(score: {best_result.score:.3f})")

        # Example 3: File ingestion (if example files exist)
        logger.info("\n3. File ingestion example...")

        # Create example files
        example_dir = Path("./example_docs")
        example_dir.mkdir(exist_ok=True)

        example_files = {
            "python_guide.md": """# Python Programming Guide

## Introduction
Python is an interpreted, high-level programming language with dynamic semantics.
Its high-level built-in data structures, combined with dynamic typing and binding,
make it attractive for Rapid Application Development.

## Key Features
- Simple, easy-to-learn syntax
- Object-oriented programming support
- Large standard library
- Cross-platform compatibility

## Applications
Python is used in web development, data science, automation, and more.
""",
            "ml_concepts.md": """# Machine Learning Concepts

## Supervised Learning
Algorithms learn from labeled training data to make predictions on new data.
Examples: Linear Regression, Support Vector Machines, Random Forest.

## Unsupervised Learning
Algorithms find patterns in data without labeled examples.
Examples: K-Means Clustering, Principal Component Analysis.

## Deep Learning
Neural networks with multiple layers that can learn complex patterns.
Used in image recognition, natural language processing, and more.
""",
            "fastapi_tutorial.md": """# FastAPI Tutorial

## Getting Started
FastAPI is a modern web framework for building APIs with Python 3.7+.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

## Features
- Automatic API documentation
- Data validation with Pydantic
- High performance (comparable to NodeJS and Go)
- Easy to learn and use

## Advanced Features
- Dependency injection
- Background tasks
- WebSocket support
- Authentication and authorization
"""
        }

        # Write example files
        for filename, content in example_files.items():
            file_path = example_dir / filename
            file_path.write_text(content)

            # Ingest the file
            file_id = await manager.ingest_file(file_path, {"source": "example"})
            logger.info(f"  Ingested file: {filename} (ID: {file_id[:8]}...)")

        # Example 4: Advanced search with filtering
        logger.info("\n4. Advanced search examples...")

        # Search within specific categories
        for category in ["programming", "ai", "web"]:
            results = await manager.search(
                f"concepts and features",
                SearchOptions(
                    mode="hybrid",
                    max_results=5,
                    min_score=0.1
                )
            )

            # Filter results by category (manual filtering as example)
            category_results = [
                r for r in results
                if r.metadata.get('category') == category or category in r.text.lower()
            ]

            if category_results:
                logger.info(f"  {category.capitalize()} category: {len(category_results)} results")
                for result in category_results[:2]:
                    title = result.metadata.get('title', result.file_path)
                    logger.info(f"    - {title} (score: {result.score:.3f})")

        # Example 5: System status
        logger.info("\n5. System status...")
        status = await manager.get_status()

        logger.info(f"  Backend: {status.backend}")
        logger.info(f"  Files: {status.total_files}")
        logger.info(f"  Chunks: {status.total_chunks}")
        logger.info(f"  Embeddings: {status.total_embeddings}")
        logger.info(f"  Storage: {status.storage_size_mb:.1f} MB")
        logger.info(f"  Healthy: {status.is_healthy}")

        logger.info("  Embedding providers:")
        for provider in status.embedding_providers:
            status_icon = "✓" if provider.available else "✗"
            logger.info(f"    {status_icon} {provider.name} ({provider.model})")

        # Example 6: Retrieve file content
        logger.info("\n6. File content retrieval...")
        if file_ids:
            file_id = file_ids[0]
            content = await manager.get_file(file_id)
            logger.info(f"  Retrieved file content ({len(content)} characters)")
            logger.info(f"  Preview: {content[:100]}...")

        # Example 7: File synchronization
        logger.info("\n7. File synchronization...")
        if example_dir.exists():
            stats = await manager.sync_files([str(example_dir)])
            logger.info(f"  Sync stats: {stats.files_processed} processed, "
                       f"{stats.files_added} added, {stats.files_updated} updated")

    finally:
        # Clean up
        await manager.close()
        logger.info("\nMemory system closed")

        # Optional: Clean up example files
        import shutil
        if Path("./example_docs").exists():
            shutil.rmtree("./example_docs")
            logger.info("Cleaned up example files")

if __name__ == "__main__":
    asyncio.run(main())