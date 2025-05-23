# InMemoryKVStoreResolver

The `InMemoryKVStoreResolver` provides a lightweight, in-memory key-value store for agents. It's ideal for development, testing, or situations where persistence isn't required.

## Overview

- **Type**: `DependencyResolver[InMemoryKVStore]`
- **Provided Dependency**: `InMemoryKVStore`
- **Package**: `rustic_ai.core.guild.agent_ext.depends.kvstore.in_memory_kvstore`

## Features

- Simple key-value storage with string keys and arbitrary JSON-serializable values
- Fast performance (RAM-based)
- Optional namespacing for organizing keys
- Supports basic CRUD operations

## Limitations

- Data is not persisted between application restarts
- Not suitable for sharing data across different processes
- Limited to memory capacity of the host machine

## Configuration

The resolver accepts no configuration parameters.

```python
from rustic_ai.core.guild.dsl import DependencySpec

spec = DependencySpec(
    class_name="rustic_ai.core.guild.agent_ext.depends.kvstore.in_memory_kvstore.InMemoryKVStoreResolver",
    properties={}
)
```

## Usage

### Guild Configuration

```python
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.guild.dsl import DependencySpec

guild_builder = (
    GuildBuilder("my_guild", "KV Guild", "Guild with in-memory key-value store")
    .add_dependency_resolver(
        "kvstore",
        DependencySpec(
            class_name="rustic_ai.core.guild.agent_ext.depends.kvstore.in_memory_kvstore.InMemoryKVStoreResolver",
            properties={}
        )
    )
)
```

### Agent Usage

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.agent_ext.depends.kvstore.in_memory_kvstore import InMemoryKVStore

class KVStoreAgent(Agent):
    @agent.processor(clz=StoreRequest, depends_on=["kvstore"])
    def handle_store_request(self, ctx: agent.ProcessContext, kvstore: InMemoryKVStore):
        # Basic operations
        kvstore.set("my_key", {"value": "Hello, World!"})
        value = kvstore.get("my_key")
        
        # Namespace operations
        kvstore.set("user:123:name", "Alice")
        kvstore.set("user:123:email", "alice@example.com")
        
        # Get all keys with a prefix
        user_data = kvstore.get_by_prefix("user:123:")
        
        # Delete a key
        kvstore.delete("my_key")
        
        ctx.send_dict({"result": user_data})
```

## API Reference

The `InMemoryKVStore` class provides these primary methods:

| Method | Description |
|--------|-------------|
| `get(key: str) -> Any` | Get a value by its key |
| `set(key: str, value: Any) -> None` | Set a value for a key |
| `delete(key: str) -> bool` | Delete a key; returns `True` if deleted, `False` if it didn't exist |
| `get_by_prefix(prefix: str) -> Dict[str, Any]` | Get all key-value pairs where the key starts with the given prefix |
| `exists(key: str) -> bool` | Check if a key exists |
| `clear() -> None` | Delete all stored key-value pairs |

## Use Cases

- **Stateful agents**: Store temporary state during agent execution
- **Caching**: Cache expensive computations or API responses
- **Testing**: Easily test agent logic without complex persistence setup
- **Prototyping**: Quick development of agents before implementing permanent storage

## Example: Session Management

```python
@agent.processor(clz=UserMessage, depends_on=["kvstore"])
def handle_message(self, ctx: agent.ProcessContext, kvstore: InMemoryKVStore):
    user_id = ctx.payload.user_id
    session_key = f"session:{user_id}"
    
    # Retrieve or initialize session
    session = kvstore.get(session_key) or {"message_count": 0, "last_seen": None}
    
    # Update session
    session["message_count"] += 1
    session["last_seen"] = datetime.now().isoformat()
    kvstore.set(session_key, session)
    
    # Use session information in response
    response = f"Welcome back! This is your {session['message_count']} message."
    ctx.send_dict({"response": response})
```

## Migration Path

When you need to migrate from `InMemoryKVStore` to a persistent solution:

1. Replace the resolver with `RedisKVStoreResolver` or another persistent implementation
2. Keep your agent code unchanged, as the KVStore interface remains the same
3. Test to ensure proper data serialization and persistence

See also: [RedisKVStoreResolver](../redis/redis_kvstore.md) for a persistent alternative. 