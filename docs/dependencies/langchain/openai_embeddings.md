# OpenAIEmbeddingsResolver

The `OpenAIEmbeddingsResolver` provides access to OpenAI's embedding models for generating vector representations of text. These embeddings capture semantic meaning, allowing agents to perform operations like semantic search, clustering, and similarity matching.

## Overview

- **Type**: `DependencyResolver[Embeddings]`
- **Provided Dependency**: `OpenAIEmbeddings`
- **Package**: `rustic_ai.langchain.agent_ext.embeddings.openai`

## Features

- **High-Quality Embeddings**: Generate state-of-the-art text embeddings using OpenAI models
- **Batch Processing**: Efficiently embed multiple texts in a single API call
- **Dimensionality Control**: Specify the number of dimensions for embeddings
- **Dynamic Sizing**: Automatically handle texts of different lengths
- **API Key Management**: Flexible API key configuration

## Configuration

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `model` | `str` | Embedding model name | `"text-embedding-ada-002"` |
| `dimensions` | `int` | Number of dimensions for the embeddings | Model-dependent |
| `api_key` | `str` | OpenAI API key | `None` (uses environment variables) |
| `organization` | `str` | OpenAI organization ID | `None` |
| `timeout` | `int` | Request timeout in seconds | `60` |
| `max_retries` | `int` | Maximum number of retries for failed requests | `6` |
| `batch_size` | `int` | Maximum number of texts to embed in one API call | `100` |
| `chunk_size` | `int` | Maximum chunk size when dealing with very long texts | `1000` |

## Usage

### Guild Configuration

```python
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.guild.dsl import DependencySpec

guild_builder = (
    GuildBuilder("embedding_guild", "Embedding Guild", "Guild with text embedding capabilities")
    .add_dependency_resolver(
        "embeddings",
        DependencySpec(
            class_name="rustic_ai.langchain.agent_ext.embeddings.openai.OpenAIEmbeddingsResolver",
            properties={
                "model": "text-embedding-ada-002",
                "dimensions": 1536,
                "api_key": "sk-..."  # or use environment variable OPENAI_API_KEY
            }
        )
    )
)
```

### Agent Usage

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.langchain.agent_ext.embeddings.openai import OpenAIEmbeddings

class EmbeddingAgent(Agent):
    @agent.processor(clz=EmbeddingRequest, depends_on=["embeddings"])
    def generate_embeddings(self, ctx: agent.ProcessContext, embeddings: OpenAIEmbeddings):
        texts = ctx.payload.texts
        
        # Generate embeddings for all texts
        embedding_vectors = embeddings.embed_documents(texts)
        
        # Generate embedding for a single text
        query_vector = embeddings.embed_query(ctx.payload.query)
        
        # Calculate similarities
        similarities = []
        for text, vector in zip(texts, embedding_vectors):
            # Simple dot product similarity
            similarity = sum(v1 * v2 for v1, v2 in zip(query_vector, vector))
            similarities.append({
                "text": text,
                "similarity": similarity
            })
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        ctx.send_dict({
            "query": ctx.payload.query,
            "results": similarities
        })
```

## API Reference

The `OpenAIEmbeddings` class provides these primary methods:

| Method | Description |
|--------|-------------|
| `embed_documents(texts: List[str]) -> List[List[float]]` | Generate embeddings for multiple texts |
| `embed_query(text: str) -> List[float]` | Generate an embedding for a single text |

## Supported Models

OpenAI offers several embedding models, each with different characteristics:

| Model | Dimensions | Context Length | Description |
|-------|------------|----------------|-------------|
| `text-embedding-ada-002` | 1536 | 8191 | General purpose embeddings |
| `text-embedding-3-small` | 1536 | 8191 | Newer model with improved performance |
| `text-embedding-3-large` | 3072 | 8191 | High-performance, larger dimensional model |

## Cost Considerations

- Embedding models are charged per token
- The cost is significantly lower than completion models
- Batch processing is more cost-effective than single requests
- Consider caching embeddings for frequently used texts

## Example: Semantic Search

```python
@agent.processor(clz=SearchRequest, depends_on=["embeddings"])
def semantic_search(self, ctx: agent.ProcessContext, embeddings: OpenAIEmbeddings):
    query = ctx.payload.query
    documents = self._get_documents()  # Method to retrieve documents
    
    # Embed the query
    query_embedding = embeddings.embed_query(query)
    
    # Embed all documents (in a real implementation, you'd likely cache these)
    document_embeddings = embeddings.embed_documents([doc["text"] for doc in documents])
    
    # Calculate similarity scores
    search_results = []
    for doc, doc_embedding in zip(documents, document_embeddings):
        # Cosine similarity calculation
        dot_product = sum(q * d for q, d in zip(query_embedding, doc_embedding))
        magnitude1 = sum(q * q for q in query_embedding) ** 0.5
        magnitude2 = sum(d * d for d in doc_embedding) ** 0.5
        similarity = dot_product / (magnitude1 * magnitude2)
        
        search_results.append({
            "text": doc["text"],
            "metadata": doc["metadata"],
            "similarity": similarity
        })
    
    # Sort by similarity (highest first)
    search_results.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Return top 5 results
    ctx.send_dict({
        "query": query,
        "results": search_results[:5]
    })
```

## Integration with Vector Databases

OpenAIEmbeddings works seamlessly with vector databases:

```python
@agent.processor(clz=PopulateVectorDBRequest, depends_on=["embeddings", "vectorstore"])
def populate_vector_db(self, ctx: agent.ProcessContext, embeddings: OpenAIEmbeddings, vectorstore: VectorStore):
    documents = [
        Document(
            id=f"doc{i}",
            text=text,
            metadata={"source": "example"}
        )
        for i, text in enumerate(ctx.payload.documents)
    ]
    
    # The vector store will use the embeddings internally
    result = vectorstore.upsert(documents)
    
    ctx.send_dict({
        "success_count": len(result.succeeded),
        "failed_count": len(result.failed)
    })
```

## Security and Authentication

To authenticate with OpenAI, you can:

1. Pass the API key directly in the resolver properties
2. Set the `OPENAI_API_KEY` environment variable
3. Use a secure secret manager via the `EnvSecretProviderDependencyResolver`

For security best practices, avoid hardcoding API keys and use environment variables or a secret management service.

## Related Resolvers

- [ChromaResolver](../chroma/chroma_resolver.md) - Vector database for storing and searching embeddings
- [CharacterSplitterResolver](character_splitter.md) - Text splitter for breaking documents into chunks
- [RecursiveSplitterResolver](recursive_splitter.md) - Advanced text splitting for document processing 