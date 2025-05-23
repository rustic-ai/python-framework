# CharacterSplitterResolver

The `CharacterSplitterResolver` provides a text splitting service that divides text into smaller chunks based on character separators. This is particularly useful for processing large documents before embedding or generating summaries.

## Overview

- **Type**: `DependencyResolver[TextSplitter]`
- **Provided Dependency**: `CharacterTextSplitter`
- **Package**: `rustic_ai.langchain.agent_ext.text_splitter.character_splitter`

## Features

- **Character-Based Splitting**: Split text at specified separator characters
- **Configurable Chunk Size**: Control the approximate size of each text chunk
- **Chunk Overlap**: Define overlap between chunks to maintain context
- **Multiple Separators**: Use different separators with priority ordering
- **Metadata Retention**: Preserve document metadata across splits

## Configuration

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `separator` | `str` | Character(s) to split on | `"\n\n"` (blank line) |
| `chunk_size` | `int` | Maximum chunk size in characters | `1000` |
| `chunk_overlap` | `int` | Number of characters to overlap between chunks | `200` |
| `add_start_index` | `bool` | Add chunk start index to metadata | `True` |
| `strip_whitespace` | `bool` | Strip whitespace from chunk beginnings/ends | `True` |

## Usage

### Guild Configuration

```python
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.guild.dsl import DependencySpec

guild_builder = (
    GuildBuilder("text_processing_guild", "Text Processing Guild", "Guild with text processing capabilities")
    .add_dependency_resolver(
        "text_splitter",
        DependencySpec(
            class_name="rustic_ai.langchain.agent_ext.text_splitter.character_splitter.CharacterSplitterResolver",
            properties={
                "separator": "\n\n",  # Split on blank lines
                "chunk_size": 1000,
                "chunk_overlap": 200
            }
        )
    )
)
```

### Agent Usage

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.langchain.agent_ext.text_splitter.character_splitter import CharacterTextSplitter
from rustic_ai.core.agents.commons.media import Document

class TextProcessingAgent(Agent):
    @agent.processor(clz=DocumentChunkRequest, depends_on=["text_splitter"])
    def split_document(self, ctx: agent.ProcessContext, text_splitter: CharacterTextSplitter):
        # Create a document
        document = Document(
            id="doc1",
            text=ctx.payload.text,
            metadata={"source": ctx.payload.source}
        )
        
        # Split the document into smaller chunks
        chunks = text_splitter.split_document(document)
        
        # Each chunk is a Document object with its own ID and metadata
        ctx.send_dict({
            "original_id": document.id,
            "chunk_count": len(chunks),
            "chunks": [
                {
                    "id": chunk.id,
                    "text": chunk.text,
                    "metadata": chunk.metadata
                }
                for chunk in chunks
            ]
        })
        
    @agent.processor(clz=TextChunkRequest, depends_on=["text_splitter"])
    def split_text(self, ctx: agent.ProcessContext, text_splitter: CharacterTextSplitter):
        # Split raw text (without creating a Document)
        text = ctx.payload.text
        chunks = text_splitter.split_text(text)
        
        ctx.send_dict({
            "chunk_count": len(chunks),
            "chunks": chunks
        })
```

## API Reference

The `CharacterTextSplitter` class provides these primary methods:

| Method | Description |
|--------|-------------|
| `split_text(text: str) -> List[str]` | Split a single text string into chunks |
| `split_documents(documents: List[Document]) -> List[Document]` | Split multiple Document objects |
| `split_document(document: Document) -> List[Document]` | Split a single Document object |
| `create_documents(texts: List[str], metadatas: List[Dict] = None) -> List[Document]` | Create Document objects from texts |

## Working with Document Objects

When splitting Document objects, important points to note:

1. The original document's metadata is preserved in each chunk
2. Each chunk gets a unique ID (based on the original ID with a suffix)
3. Additional metadata is added to track the chunk's position and content:
   - `chunk_index`: The position of the chunk in the sequence
   - `start_index`: The character position in the original text where the chunk starts

## Example: Processing Large Documents for RAG

```python
@agent.processor(clz=PrepareForRAGRequest, depends_on=["text_splitter", "vectorstore"])
def prepare_for_rag(self, ctx: agent.ProcessContext, text_splitter: CharacterTextSplitter, vectorstore: VectorStore):
    # Convert input text to a Document
    document = Document(
        id=f"doc-{uuid.uuid4()}",
        text=ctx.payload.text,
        metadata={
            "source": ctx.payload.source,
            "author": ctx.payload.author,
            "date": ctx.payload.date
        }
    )
    
    # Split into manageable chunks
    chunks = text_splitter.split_document(document)
    
    # Store chunks in vector database for later retrieval
    result = vectorstore.upsert(chunks)
    
    ctx.send_dict({
        "processed": True,
        "document_id": document.id,
        "chunk_count": len(chunks),
        "success_count": len(result.succeeded),
        "failed_count": len(result.failed)
    })
```

## Custom Separators

You can use different separators with varying priorities:

```python
DependencySpec(
    class_name="rustic_ai.langchain.agent_ext.text_splitter.character_splitter.CharacterSplitterResolver",
    properties={
        "separator": ["\n\n", "\n", ". ", ", "],  # Try these separators in order
        "chunk_size": 800,
        "chunk_overlap": 150
    }
)
```

With this configuration, the splitter will:
1. First try to split on blank lines (`"\n\n"`)
2. If chunks are still too large, split on newlines (`"\n"`)
3. If still too large, split on sentence endings (`. `)
4. If still too large, split on commas (`, `)

## When to Use Character Splitting

Character splitting works well when:

- Documents have natural separators (paragraphs, lines, etc.)
- You need simple, fast splitting without complex logic
- Text is relatively well-structured

For more complex splitting needs involving recursive separators or language-aware splitting, consider using [RecursiveSplitterResolver](recursive_splitter.md).

## Related Resolvers

- [RecursiveSplitterResolver](recursive_splitter.md) - More advanced text splitting with recursive separator logic
- [OpenAIEmbeddingsResolver](openai_embeddings.md) - For embedding the split chunks
- [ChromaResolver](../chroma/chroma_resolver.md) - For storing embedded chunks in a vector database 