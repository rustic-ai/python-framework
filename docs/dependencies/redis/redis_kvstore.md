# RedisKVStoreResolver

The `RedisKVStoreResolver` provides a persistent, shared key-value store backed by Redis. It offers a scalable solution for storing data that needs to be accessible across multiple agents, processes, or servers.

## Overview

- **Type**: `DependencyResolver[RedisKVStore]`
- **Provided Dependency**: `RedisKVStore`
- **Package**: `rustic_ai.redis.agent_ext.kvstore`

## Features

- **Persistence**: Data survives application restarts
- **Distributed Access**: Multiple processes can share the same data
- **Namespacing**: Organize keys with prefixes
- **Expiration**: Set TTL (Time-To-Live) for keys
- **Transactions**: Atomic operations for data consistency
- **Serialization**: Automatic JSON serialization/deserialization

## Configuration

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `host` | `str` | Redis server hostname | `"localhost"` |
| `port` | `int` | Redis server port | `6379` |
| `db` | `int` | Redis database number | `0` |
| `password` | `str` | Redis password | `None` |
| `prefix` | `str` | Prefix for all keys | `""` (empty string) |
| `socket_timeout` | `float` | Socket timeout in seconds | `5.0` |
| `socket_connect_timeout` | `float` | Socket connection timeout in seconds | `5.0` |
| `connection_pool` | `Dict[str, Any]` | Additional Redis connection pool options | `{}` |

## Usage

### Guild Configuration

```python
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.guild.dsl import DependencySpec

guild_builder = (
    GuildBuilder("redis_guild", "Redis Guild", "Guild with Redis-backed key-value store")
    .add_dependency_resolver(
        "kvstore",
        DependencySpec(
            class_name="rustic_ai.redis.agent_ext.kvstore.RedisKVStoreResolver",
            properties={
                "host": "redis.example.com",
                "port": 6379,
                "password": "redis_password",  # Or use an environment variable
                "prefix": "my_app:"
            }
        )
    )
)
```

### Agent Usage

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.redis.agent_ext.kvstore import RedisKVStore

class PersistentDataAgent(Agent):
    @agent.processor(clz=DataRequest, depends_on=["kvstore"])
    def handle_data(self, ctx: agent.ProcessContext, kvstore: RedisKVStore):
        # Basic operations
        kvstore.set("user:profile", {"name": "Alice", "email": "alice@example.com"})
        profile = kvstore.get("user:profile")
        
        # Set with expiration (TTL in seconds)
        kvstore.set("session:token", "abc123", ttl=3600)  # Expires in 1 hour
        
        # Get multiple keys
        users = kvstore.get_many(["user:1", "user:2", "user:3"])
        
        # Delete keys
        kvstore.delete("old_data")
        
        # Check if key exists
        if kvstore.exists("cache:results"):
            results = kvstore.get("cache:results")
        else:
            results = self._compute_results()
            kvstore.set("cache:results", results, ttl=300)  # Cache for 5 minutes
            
        ctx.send_dict({"results": results})
```

## API Reference

The `RedisKVStore` class provides these primary methods:

| Method | Description |
|--------|-------------|
| `get(key: str) -> Any` | Get a value by its key |
| `get_many(keys: List[str]) -> Dict[str, Any]` | Get multiple values by their keys |
| `set(key: str, value: Any, ttl: Optional[int] = None) -> None` | Set a value for a key with optional TTL in seconds |
| `set_many(data: Dict[str, Any], ttl: Optional[int] = None) -> None` | Set multiple key-value pairs with optional TTL |
| `delete(key: str) -> bool` | Delete a key |
| `delete_many(keys: List[str]) -> int` | Delete multiple keys, returns count of deleted keys |
| `exists(key: str) -> bool` | Check if a key exists |
| `get_by_prefix(prefix: str) -> Dict[str, Any]` | Get all key-value pairs with keys starting with the prefix |
| `clear() -> None` | Clear all keys (use with caution) |

## Example: Implementing a Rate Limiter

```python
@agent.processor(clz=ApiRequest, depends_on=["kvstore"])
def process_api_request(self, ctx: agent.ProcessContext, kvstore: RedisKVStore):
    user_id = ctx.payload.user_id
    rate_limit_key = f"rate_limit:{user_id}:{datetime.now().strftime('%Y-%m-%d:%H')}"
    
    # Get current count or 0 if not exists
    current_count = kvstore.get(rate_limit_key) or 0
    
    # Check if user exceeded rate limit (100 requests per hour)
    if current_count >= 100:
        ctx.send_dict({
            "status": "error",
            "message": "Rate limit exceeded. Try again later."
        })
        return
    
    # Increment count and set TTL for auto-cleanup (1 hour + small buffer)
    kvstore.set(rate_limit_key, current_count + 1, ttl=3700)
    
    # Process the actual API request
    result = self._call_api(ctx.payload.request_data)
    
    ctx.send_dict({
        "status": "success",
        "result": result,
        "remaining_requests": 100 - (current_count + 1)
    })
```

## Clustering and High Availability

For production environments, consider:

- **Redis Sentinel**: For high availability and automatic failover
- **Redis Cluster**: For scalability across multiple Redis nodes
- **Redis Enterprise**: For commercial support and additional features

To use with Redis Sentinel:

```python
DependencySpec(
    class_name="rustic_ai.redis.agent_ext.kvstore.RedisKVStoreResolver",
    properties={
        "sentinel_hosts": [
            {"host": "sentinel1.example.com", "port": 26379},
            {"host": "sentinel2.example.com", "port": 26379},
            {"host": "sentinel3.example.com", "port": 26379}
        ],
        "master_name": "mymaster",
        "sentinel_password": "sentinel_password"
    }
)
```

## Performance Considerations

- **Key Design**: Use meaningful key names with hierarchical structure (e.g., `"user:123:profile"`)
- **Data Size**: Keep values reasonably sized; consider external storage for large objects
- **TTL**: Use TTL for temporary data to prevent memory leaks
- **Connection Pooling**: The resolver automatically uses connection pooling for efficiency

## Comparison with InMemoryKVStore

| Feature | RedisKVStore | InMemoryKVStore |
|---------|-------------|------------------|
| Persistence | Yes | No |
| Multi-process | Yes | No |
| Distributed | Yes | No |
| TTL Support | Yes | No |
| Performance | Fast | Extremely Fast |
| Setup Complexity | Requires Redis server | No external dependencies |

## Related Resolvers

- [InMemoryKVStoreResolver](../core/in_memory_kvstore.md) - Non-persistent in-memory alternative 