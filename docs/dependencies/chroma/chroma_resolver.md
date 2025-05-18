# ChromaResolver

The `ChromaResolver` provides a vector database for storing, retrieving, and searching vector embeddings. It leverages the [Chroma](https://docs.trychroma.com/) vector database to enable semantic search and retrieval-augmented generation (RAG) capabilities for agents.

## Overview

- **Type**: `DependencyResolver[VectorStore]`
- **Provided Dependency**: `ChromaVectorStore`
- **Package**: `rustic_ai.chroma.agent_ext.vectorstore`

## Features

- **Vector Storage**: Store document embeddings in a persistent database
- **Semantic Search**: Find semantically similar documents based on vector similarity
- **Metadata Filtering**: Filter search results based on metadata
- **Document Management**: Add, update, delete, and retrieve documents
- **Multiple Distance Metrics**: Cosine similarity, dot product, and Euclidean distance

## Configuration

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `collection_name` | `str` | Name of the Chroma collection | Required |
| `embedding_function` | `str` | Fully qualified class name of the embedding function | Required |
| `persist_directory` | `str` | Directory for persisting the database | `None` (in-memory) |
| `client_settings` | `Dict[str, Any]` | Settings for the Chroma client | `{}` |
| `collection_metadata` | `Dict[str, Any]` | Metadata for the collection | `{}` |
| `distance_function` | `str` | Distance function for similarity (`"cosine"`, `"l2"`, `"ip"`) | `"cosine"` |

## Usage

### Guild Configuration

```python
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.guild.dsl import DependencySpec

guild_builder = (
    GuildBuilder("vector_guild", "Vector Search Guild", "Guild with vector search capabilities")
    .add_dependency_resolver(
        "vectorstore",
        DependencySpec(
            class_name="rustic_ai.chroma.agent_ext.vectorstore.ChromaResolver",
            properties={
                "collection_name": "my_documents",
                "embedding_function": "rustic_ai.langchain.agent_ext.embeddings.openai.OpenAIEmbeddings",
                "persist_directory": "/path/to/chroma_db",
                "distance_function": "cosine"
            }
        )
    )
    # Note: You also need to configure the embedding function dependency
    .add_dependency_resolver(
        "embeddings",
        DependencySpec(
            class_name="rustic_ai.langchain.agent_ext.embeddings.openai.OpenAIEmbeddingsResolver",
            properties={
                "model": "text-embedding-ada-002",
                "dimensions": 1536
            }
        )
    )
)
```

### Agent Usage

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.chroma.agent_ext.vectorstore import ChromaVectorStore
from rustic_ai.core.agents.commons.media import Document

class VectorSearchAgent(Agent):
    @agent.processor(clz=DocumentUpsertRequest, depends_on=["vectorstore"])
    def add_documents(self, ctx: agent.ProcessContext, vectorstore: ChromaVectorStore):
        # Create documents
        documents = [
            Document(
                id="doc1",
                text="Artificial intelligence is transforming industries worldwide.",
                metadata={"source": "article", "category": "technology"}
            ),
            Document(
                id="doc2",
                text="Machine learning models require large amounts of training data.",
                metadata={"source": "textbook", "category": "technology"}
            )
        ]
        
        # Add documents to vector store
        response = vectorstore.upsert(documents)
        
        ctx.send_dict({
            "success_count": len(response.succeeded),
            "failed_count": len(response.failed)
        })
    
    @agent.processor(clz=SearchRequest, depends_on=["vectorstore"])
    def search_documents(self, ctx: agent.ProcessContext, vectorstore: ChromaVectorStore):
        query = ctx.payload.query
        
        # Perform semantic search
        results = vectorstore.similarity_search(
            query=query,
            k=5,  # Number of results to return
            metadata_filter={"category": "technology"}  # Optional metadata filter
        )
        
        # Send back search results
        ctx.send_dict({
            "query": query,
            "results": [
                {
                    "text": doc.text,
                    "metadata": doc.metadata,
                    "score": score
                }
                for doc, score in zip(results.documents, results.scores)
            ]
        })
```

## Document Structure

Documents in the vector store have these components:

- **ID**: Unique identifier for the document
- **Text**: The document content
- **Metadata**: Key-value pairs of additional information about the document
- **Embedding**: Vector representation of the document (generated automatically)

## API Reference

The `ChromaVectorStore` class provides these primary methods:

| Method | Description |
|--------|-------------|
| `upsert(documents: List[Document]) -> UpsertResponse` | Add or update documents |
| `similarity_search(query: str, k: int = 4, metadata_filter: Optional[Dict[str, str]] = None) -> VectorSearchResults` | Search for similar documents |
| `delete(ids: Optional[List[str]] = None) -> Optional[bool]` | Delete documents by IDs (or all if None) |
| `get_by_ids(ids: List[str]) -> List[Document]` | Retrieve documents by IDs |

## Example: Retrieval-Augmented Generation (RAG)

```python
@agent.processor(clz=RAGRequest, depends_on=["vectorstore", "llm"])
def answer_with_rag(self, ctx: agent.ProcessContext, vectorstore: ChromaVectorStore, llm: LLM):
    query = ctx.payload.query
    
    # Step 1: Retrieve relevant documents
    search_results = vectorstore.similarity_search(query, k=3)
    
    # Step 2: Build context from retrieved documents
    context = "\n\n".join([doc.text for doc in search_results.documents])
    
    # Step 3: Generate answer using LLM with context
    request = ChatCompletionRequest(
        messages=[
            ChatMessage(
                role=ChatMessageRole.SYSTEM, 
                content=f"Answer the question based on the following context:\n\n{context}"
            ),
            ChatMessage(role=ChatMessageRole.USER, content=query)
        ]
    )
    
    response = llm.completion(request)
    
    # Step 4: Return the answer with sources
    ctx.send_dict({
        "answer": response.choices[0].message.content,
        "sources": [
            {"text": doc.text, "metadata": doc.metadata}
            for doc in search_results.documents
        ]
    })
```

## Persistence Modes

ChromaResolver supports two modes of operation:

1. **In-memory**: When `persist_directory` is `None`, data is kept only in memory
2. **Persistent**: When `persist_directory` is specified, data is saved to disk

For production use, always specify a `persist_directory` to ensure data is not lost on restart.

## Embedding Functions

The `embedding_function` parameter is crucial - it determines how text documents are converted to vector embeddings. You must provide the fully qualified class name of a compatible embedding function.

Common choices include:
- `rustic_ai.langchain.agent_ext.embeddings.openai.OpenAIEmbeddings`
- `rustic_ai.langchain.agent_ext.embeddings.huggingface.HuggingFaceEmbeddings`
- Other custom embedding functions that implement the required interface

## Performance Considerations

- **Document Size**: Keep documents reasonably sized (chunking large documents is recommended)
- **Collection Size**: Very large collections may require more resources
- **Query Frequency**: High-volume search may require scaling the Chroma backend
- **Persistence**: Disk-based persistence has lower performance than in-memory

## Related Resolvers

- [OpenAIEmbeddingsResolver](../langchain/openai_embeddings.md) - For generating embeddings with OpenAI models 