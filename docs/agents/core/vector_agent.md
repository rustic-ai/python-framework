# VectorAgent

The `VectorAgent` provides document indexing and vector search capabilities within a RusticAI guild, enabling semantic retrieval of information from text documents.

## Purpose

This agent serves as a bridge between your application and vector databases. It handles document processing, indexing, and vector similarity search, making it a core component for knowledge retrieval systems.

## When to Use

Use the `VectorAgent` when your application needs to:

- Store and retrieve documents based on semantic similarity
- Create a knowledge base for LLM context augmentation
- Implement retrieval-augmented generation (RAG) patterns
- Build search functionality based on meaning rather than keywords
- Process and index documents from various sources

## Dependencies

The `VectorAgent` requires:

- **vectorstore**: A vector database implementation for storing embeddings
- **textsplitter**: A text splitting implementation for breaking documents into chunks
- **embeddings**: An embeddings provider for converting text to vectors

## Message Types

### Input Messages

#### IngestDocuments

A request to index documents for later retrieval:

```python
class IngestDocuments(BaseModel):
    links: List[MediaLink]  # List of documents to ingest
    namespace: Optional[str] = None  # Optional namespace for organizing documents
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata for all documents
    chunk_metadata: Optional[Dict[str, Any]] = None  # Metadata for individual chunks
```

#### VectorSearchQuery

A request to search for documents by similarity:

```python
class VectorSearchQuery(BaseModel):
    query: str  # The search query text
    namespace: Optional[str] = None  # Namespace to search within
    limit: int = 5  # Maximum number of results to return
    filter: Optional[Dict[str, Any]] = None  # Filter criteria for search
```

### Output Messages

#### VectorSearchResults

The results of a vector search:

```python
class VectorSearchResults(BaseModel):
    query: str  # The original query
    results: List[Document]  # The matching documents
    namespace: Optional[str] = None  # The namespace that was searched
```

Each `Document` includes:
- content: The text content
- metadata: Document metadata
- score: Similarity score to the query

#### IngestCompleted

Sent when document ingestion is completed:

```python
class IngestCompleted(BaseModel):
    namespace: Optional[str] = None  # The namespace documents were added to
    count: int  # Number of documents ingested
    chunk_count: int  # Number of chunks created from documents
```

## Behavior

### Document Ingestion

1. The agent receives an `IngestDocuments` message with document links
2. For each document:
   - The content is loaded from the file or URL
   - The text is split into chunks using the text splitter dependency
   - Each chunk is converted to embeddings using the embeddings dependency
   - The embeddings are stored in the vector store with associated metadata
3. The agent emits an `IngestCompleted` message with statistics

### Vector Search

1. The agent receives a `VectorSearchQuery` message
2. The query text is converted to embeddings
3. A similarity search is performed in the vector store
4. The most similar documents are returned in a `VectorSearchResults` message

## Sample Usage

```python
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.guild.agent_ext.depends.dependency_resolver import DependencySpec
from rustic_ai.core.agents.indexing.vector_agent import VectorAgent

# Set up dependencies
vectorstore = DependencySpec(
    class_name="rustic_ai.chroma.agent_ext.vectorstore.ChromaResolver",
    properties={}
)

embeddings = DependencySpec(
    class_name="rustic_ai.langchain.agent_ext.embeddings.openai.OpenAIEmbeddingsResolver",
    properties={}
)

textsplitter = DependencySpec(
    class_name="rustic_ai.langchain.agent_ext.text_splitter.recursive_splitter.RecursiveSplitterResolver",
    properties={
        "conf": {
            "chunk_size": 1000,
            "chunk_overlap": 200
        }
    }
)

# Create the agent spec
vector_agent_spec = (
    AgentBuilder(VectorAgent)
    .set_id("vector_agent")
    .set_name("Vector Agent")
    .set_description("Agent for document indexing and semantic search")
    .build_spec()
)

# Add dependencies and agent to guild
guild_builder.add_dependency("vectorstore", vectorstore)
guild_builder.add_dependency("embeddings", embeddings)
guild_builder.add_dependency("textsplitter", textsplitter)
guild_builder.add_agent_spec(vector_agent_spec)
```

## Example Document Ingestion

```python
from rustic_ai.core.agents.commons.media import MediaLink
from rustic_ai.core.agents.indexing.vector_agent import IngestDocuments

# Create document links
documents = [
    MediaLink(
        url="docs/introduction.md",
        name="Introduction",
        on_filesystem=True,
        mimetype="text/markdown"
    ),
    MediaLink(
        url="docs/api_reference.md",
        name="API Reference",
        on_filesystem=True,
        mimetype="text/markdown"
    )
]

# Create ingestion request
ingest_request = IngestDocuments(
    links=documents,
    namespace="documentation",
    metadata={"source": "official_docs", "version": "1.0"}
)

# Send to the agent
client.publish("default_topic", ingest_request)
```

## Example Vector Search

```python
from rustic_ai.core.agents.indexing.vector_agent import VectorSearchQuery

# Create search query
search_query = VectorSearchQuery(
    query="How do I create a custom agent?",
    namespace="documentation",
    limit=3
)

# Send to the agent
client.publish("default_topic", search_query)
```

## Integration with RAG Pattern

The VectorAgent is commonly used as part of a Retrieval-Augmented Generation (RAG) pattern:

1. Documents are ingested and indexed using the VectorAgent
2. User queries are sent to a coordinator agent
3. The coordinator agent:
   - Sends a vector search query to find relevant context
   - Combines the retrieved context with the user query
   - Sends the augmented query to an LLM agent
4. The LLM agent generates a response using the retrieved context

This pattern significantly improves the quality and factuality of LLM responses for domain-specific applications.

## Notes and Limitations

- The quality of vector search depends on the embeddings model used
- Performance depends on the vector store implementation
- Document chunking strategies significantly impact search quality
- Large document collections require more storage and compute resources
- Consider metadata filtering to improve search efficiency in large collections 