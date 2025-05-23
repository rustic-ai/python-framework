# Dependency Resolvers

Dependency resolvers are a key component of RusticAI's dependency injection system. They provide agents with access to external services, resources, and capabilities in a modular, configurable way.

## Overview

RusticAI's dependency resolver system allows agents to:

- Access external services (databases, APIs, LLMs, etc.)
- Share resources efficiently
- Swap implementations without changing agent code
- Configure services in a consistent way
- Test with mock dependencies

## Available Resolvers by Package

RusticAI provides dependency resolvers across multiple packages:

### [Core](core/index.md)
Core dependencies for essential functionality:
- [FileSystemResolver](core/filesystem.md) - File system access
- [InMemoryKVStoreResolver](core/in_memory_kvstore.md) - In-memory key-value store
- [PythonExecExecutorResolver](core/python_exec_executor.md) - Python code execution
- [InProcessCodeInterpreterResolver](core/in_process_interpreter.md) - In-process code interpretation
- [EnvSecretProviderResolver](core/env_secret_provider.md) - Environment-based secret management

### [Redis](redis/index.md)
Redis-based dependencies:
- [RedisKVStoreResolver](redis/redis_kvstore.md) - Persistent key-value store backed by Redis

### [LiteLLM](litellm/index.md)
Large language model integration:
- [LiteLLMResolver](litellm/litellm_resolver.md) - Unified LLM access across multiple providers

### [Chroma](chroma/index.md)
Vector database integration:
- [ChromaResolver](chroma/chroma_resolver.md) - Vector database for embeddings

### [LangChain](langchain/index.md)
LangChain framework integration:
- [OpenAIEmbeddingsResolver](langchain/openai_embeddings.md) - OpenAI embeddings
- [CharacterSplitterResolver](langchain/character_splitter.md) - Character-based text splitting
- [RecursiveSplitterResolver](langchain/recursive_splitter.md) - Recursive text splitting

## Using Dependency Resolvers

Dependency resolvers are configured in guild or agent specifications and then injected into agent handlers:

```python
# In guild configuration
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.guild.dsl import DependencySpec

guild_builder = (
    GuildBuilder("my_guild", "My Guild", "Guild with dependencies")
    .add_dependency_resolver(
        "filesystem",
        DependencySpec(
            class_name="rustic_ai.core.guild.agent_ext.depends.filesystem.filesystem.FileSystemResolver", 
            properties={"path_base": "/tmp/rusticai/files", "protocol": "file", "storage_options": {}}
        )
    )
)

# In agent code
from rustic_ai.core.guild import Agent, agent

class FileAgent(Agent):
    @agent.processor(clz=FileRequest, depends_on=["filesystem"])
    def handle_file_request(self, ctx: agent.ProcessContext, filesystem):
        # Use the filesystem dependency
        with filesystem.open("data.txt", "w") as f:
            f.write("Hello, World!")
```

## Dependency Resolution Process

When an agent handler with dependencies is invoked:

1. The system identifies dependencies listed in `depends_on`
2. For each dependency:
   - First checks agent-level `dependency_map`
   - Then checks guild-level `dependency_map`
3. For each dependency specification:
   - The resolver class is instantiated with the provided properties
   - The resolver's `resolve()` method is called to create the dependency
   - The result is injected as an argument to the handler

## Creating Custom Resolvers

To create a custom resolver:

1. Extend the `DependencyResolver` base class
2. Implement the `resolve(guild_id, agent_id)` method
3. Configure the resolver in your guild or agent specification

For detailed information on the dependency system, see [Dependencies Core Documentation](../core/dependencies.md) and [Dependency Injection Guide](../howto/dependency_injection.md). 