# RecursiveSplitterResolver

The `RecursiveSplitterResolver` provides an advanced text splitting service that recursively divides text using a hierarchy of separators. This enables more intelligent splitting that respects document structure, making it ideal for processing complex, structured documents.

## Overview

- **Type**: `DependencyResolver[TextSplitter]`
- **Provided Dependency**: `RecursiveCharacterTextSplitter`
- **Package**: `rustic_ai.langchain.agent_ext.text_splitter.recursive_splitter`

## Features

- **Hierarchical Splitting**: Uses a prioritized list of separators to recursively split text
- **Structure-Aware**: Respects document structure by trying larger semantic units first
- **Custom Separators**: Configurable separators for different document types
- **Chunk Control**: Configure size and overlap of text chunks
- **Language-Specific Presets**: Built-in separator configurations for common languages/formats

## Configuration

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `separators` | `List[str]` | Ordered list of separators to split on | See below |
| `chunk_size` | `int` | Maximum chunk size in characters | `1000` |
| `chunk_overlap` | `int` | Number of characters to overlap between chunks | `200` |
| `add_start_index` | `bool` | Add chunk start index to metadata | `True` |
| `strip_whitespace` | `bool` | Strip whitespace from chunk beginnings/ends | `True` |
| `language` | `str` | Predefined separator set for a language/format | `None` |

### Default Separators

If not specified, the default separators (in order) are:
1. `"\n\n"` (blank line)
2. `"\n"` (newline)
3. `" "` (space)
4. `""` (character-by-character)

### Predefined Language Separators

| Language | Description | Separators |
|----------|-------------|------------|
| `"python"` | Python code | Module, class, function, line breaks |
| `"markdown"` | Markdown files | Headers, paragraphs, lists |
| `"html"` | HTML documents | Elements, paragraphs, breaks |
| `"cpp"` | C++ code | Class, function, line separations |
| `"java"` | Java code | Class, method, line separations |

## Usage

### Guild Configuration

```python
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.guild.dsl import DependencySpec

guild_builder = (
    GuildBuilder("text_processing_guild", "Text Processing Guild", "Guild with advanced text processing")
    .add_dependency_resolver(
        "recursive_splitter",
        DependencySpec(
            class_name="rustic_ai.langchain.agent_ext.text_splitter.recursive_splitter.RecursiveSplitterResolver",
            properties={
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "separators": ["\n## ", "\n### ", "\n#### ", "\n", " ", ""]
            }
        )
    )
    # Or use a predefined language configuration
    .add_dependency_resolver(
        "markdown_splitter",
        DependencySpec(
            class_name="rustic_ai.langchain.agent_ext.text_splitter.recursive_splitter.RecursiveSplitterResolver",
            properties={
                "language": "markdown",
                "chunk_size": 1500,
                "chunk_overlap": 300
            }
        )
    )
)
```

### Agent Usage

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.langchain.agent_ext.text_splitter.recursive_splitter import RecursiveCharacterTextSplitter
from rustic_ai.core.agents.commons.media import Document

class DocumentProcessor(Agent):
    @agent.processor(clz=DocumentRequest, depends_on=["recursive_splitter"])
    def process_document(self, ctx: agent.ProcessContext, recursive_splitter: RecursiveCharacterTextSplitter):
        document = Document(
            id=ctx.payload.doc_id,
            text=ctx.payload.content,
            metadata=ctx.payload.metadata
        )
        
        # Split document using recursive logic
        chunks = recursive_splitter.split_document(document)
        
        # Process the chunks
        ctx.send_dict({
            "original_id": document.id,
            "chunk_count": len(chunks),
            "chunks": [
                {
                    "id": chunk.id,
                    "text": chunk.text[:100] + "..." if len(chunk.text) > 100 else chunk.text,
                    "size": len(chunk.text),
                    "metadata": chunk.metadata
                }
                for chunk in chunks
            ]
        })
```

## How Recursive Splitting Works

The recursive splitting process follows these steps:

1. Start with the first separator in the list
2. Split the text using this separator
3. For each resulting segment:
   - If the segment is smaller than `chunk_size`, keep it
   - Otherwise, recursively split it using the next separator in the list
4. Continue until all segments are within the specified size or no more separators are available
5. Apply overlaps between adjacent chunks as specified by `chunk_overlap`

This approach results in more natural splits that respect document structure.

## API Reference

The `RecursiveCharacterTextSplitter` class provides these primary methods:

| Method | Description |
|--------|-------------|
| `split_text(text: str) -> List[str]` | Split a single text string into chunks |
| `split_documents(documents: List[Document]) -> List[Document]` | Split multiple Document objects |
| `split_document(document: Document) -> List[Document]` | Split a single Document object |
| `create_documents(texts: List[str], metadatas: List[Dict] = None) -> List[Document]` | Create Document objects from texts |

## Example: Processing Code Files for Embedding

```python
@agent.processor(clz=CodeProcessingRequest, depends_on=["recursive_splitter", "vectorstore"])
def process_code(self, ctx: agent.ProcessContext, recursive_splitter: RecursiveCharacterTextSplitter, vectorstore: VectorStore):
    code_text = ctx.payload.code
    language = ctx.payload.language
    
    # Use language-specific splitter
    language_specific_splitter = RecursiveCharacterTextSplitter.from_language(
        language=language,
        chunk_size=1000,
        chunk_overlap=200
    )
    
    # Create document
    document = Document(
        id=f"code-{uuid.uuid4()}",
        text=code_text,
        metadata={
            "filename": ctx.payload.filename,
            "language": language,
            "repository": ctx.payload.repository
        }
    )
    
    # Split code into semantically meaningful chunks
    chunks = language_specific_splitter.split_document(document)
    
    # Store in vector database
    result = vectorstore.upsert(chunks)
    
    ctx.send_dict({
        "success": True,
        "chunk_count": len(chunks),
        "stored_chunks": len(result.succeeded)
    })
```

## Custom Separator Strategies

### For Legal Documents

```python
DependencySpec(
    class_name="rustic_ai.langchain.agent_ext.text_splitter.recursive_splitter.RecursiveSplitterResolver",
    properties={
        "separators": [
            "\nARTICLE ",      # Split on articles first
            "\nSection ",      # Then on sections
            "\nSubsection ",   # Then on subsections
            "\n\n",            # Then on paragraphs
            "\n",              # Then on lines
            ". ",              # Then on sentences
            " ",               # Then on words
            ""                 # Finally on characters
        ],
        "chunk_size": 1000,
        "chunk_overlap": 200
    }
)
```

### For Research Papers

```python
DependencySpec(
    class_name="rustic_ai.langchain.agent_ext.text_splitter.recursive_splitter.RecursiveSplitterResolver",
    properties={
        "separators": [
            "\n# ",            # Split on main headers
            "\n## ",           # Then on subheaders
            "\n### ",          # Then on sub-subheaders
            "\n\n",            # Then on paragraphs
            ". ",              # Then on sentences
            ", ",              # Then on clauses
            " ",               # Then on words
            ""                 # Finally on characters
        ],
        "chunk_size": 1500,
        "chunk_overlap": 300
    }
)
```

## When to Use Recursive Splitting

Recursive splitting is ideal for:

- Complex, structured documents (code, legal texts, etc.)
- Documents where the hierarchy of content is important
- Cases where you want to preserve semantic units as much as possible
- Documents with varying section sizes

For simpler documents or when performance is critical, consider [CharacterSplitterResolver](character_splitter.md) instead.

## Related Resolvers

- [CharacterSplitterResolver](character_splitter.md) - Simpler text splitting for less structured content
- [OpenAIEmbeddingsResolver](openai_embeddings.md) - For embedding the split chunks
- [ChromaResolver](../chroma/chroma_resolver.md) - For storing embedded chunks in a vector database 