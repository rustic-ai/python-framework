# Chroma Integration

This section contains documentation for RusticAI's Chroma integration, which provides vector database capabilities for embedding-based retrieval and similarity search.

## Overview

Chroma is an open-source embedding database designed for AI applications. The RusticAI Chroma integration enables you to:

- Store and retrieve vector embeddings efficiently
- Implement semantic search capabilities
- Build retrieval-augmented generation (RAG) systems
- Create knowledge bases for your agents

## Features

- **Vector Storage** - Store embeddings generated from various content types
- **Similarity Search** - Find relevant information using vector similarity metrics
- **Metadata Filtering** - Filter results based on document metadata
- **Persistence** - Store embeddings locally or in a persistent database
- **Collection Management** - Organize embeddings into collections for different use cases

## Getting Started

To use the Chroma integration, you'll need:

1. Chroma DB installed in your environment
2. A compatible embedding model (e.g., OpenAI, Sentence Transformers)
3. RusticAI core framework configured properly

### Basic Example

```python
from rustic_ai.chroma.vector_store import ChromaVectorStore
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.guild.agent_ext.depends.dependency_resolver import DependencySpec

# Create a Chroma vector store dependency
chroma_store = DependencySpec(
    class_name="rustic_ai.chroma.vector_store.ChromaVectorStore",
    properties={
        "collection_name": "documentation",
        "embedding_function_name": "openai",
        "persist_directory": "./chroma_db"
    }
)

# Add to guild when building
guild_builder.add_dependency("vector_store", chroma_store)
```

## Documentation

Comprehensive documentation for all Chroma integration features is currently under development. Please check back for updates as we expand this section. 