# State Management

State is the backbone that allows agents and guilds to remember the past, reason about the present, and influence the future. RusticAI offers a unified **State Management** layer that is both *simple for trivial use-cases* and *powerful enough for distributed deployments*.

## Why a Dedicated State Layer?
1. **Consistency** – Shared state establishes a single source of truth across agents.
2. **Resilience** – Persisting critical data protects conversations and workflows from process crashes.
3. **Observability** – A well-structured state store enables auditing, monitoring and replay-debugging.

## Scopes and Lifetimes
| Scope | Owner | Lifetime | Typical Use-Case |
|-------|-------|----------|------------------|
| **Agent State** | Individual agent | Until the agent is removed | Conversation context, local counters |
| **Guild State** | Guild | While the guild is running | Shared knowledge base, collaborative draft |
| **Global State** | Application | Unlimited | Cross-guild configuration, global indexes |

> All scopes share the same API surface but may be backed by different persistence drivers.

## The `StateManager` Interface
```python
class BaseStateManager(Protocol):
    def get(self, scope: Scope, key: str) -> Any: ...
    def set(self, scope: Scope, key: str, value: Any) -> None: ...
    def delete(self, scope: Scope, key: str) -> None: ...
    def list(self, scope: Scope, prefix: str | None = None) -> dict[str, Any]: ...
```
Key characteristics:
- **Transactional** – Changes can be committed or rolled back atomically.
- **Pluggable** – Swap implementations without touching agent code.
- **Thread-Safe** – Guarantees correctness under concurrent access.

## Built-In Back-Ends
| Driver | Description | When to Use |
|--------|-------------|------------|
| `InMemoryStateManager` | Fast, non-persistent `dict`-based store | Unit tests, ephemeral prototypes |
| `SQLiteStateManager` | Lightweight, file-based SQL store | Desktop apps, single-node deployments |
| `RedisStateManager`  | Networked, in-memory store with persistence | Multi-process / Docker compose |
| `PostgresStateManager` | Full ACID guarantees & rich querying | Production workloads, analytics |

You can add your own driver by implementing `BaseStateManager` and registering it with the DI container.

## Working with Agent State
```python
from rustic_ai.core.state import Scope

@processor(MyRequest)
def handle(self, ctx):
    visits = ctx.state.get(Scope.AGENT, "visits") or 0
    ctx.state.set(Scope.AGENT, "visits", visits + 1)
```

## Concurrency & Consistency Strategies
Depending on your chosen back-end, you may need to handle concurrent modifications.

- **Optimistic Locking** – Each record carries a version; conflicting writes raise an error.
- **Pessimistic Locking** – A write lock is held for the duration of the transaction.
- **Event Sourcing** – Model state transitions as an append-only event log (advanced).

## Snapshotting & Replay
The state layer can periodically snapshot agent state and (optionally) persist message history. This allows you to:
1. Pause and resume long-running guilds.
2. Replay a conversation for debugging.
3. Fork a guild into an *alternate timeline* for what-if analysis.

## Best Practices
1. Store *only what you need* – large payloads belong in object storage.
2. Use **typed Pydantic models** for complex values to ensure schema evolution.
3. Version state explicitly when doing breaking changes.
4. Tightly scope writes to prevent accidental cross-agent leakage.

## Example: Pluggable Driver via Dependency Injection
```python
from rustic_ai.core.state import RedisStateManager
from rustic_ai.core.guild.dsl import DependencySpec

state_dep = {
    "state_manager": DependencySpec(
        resolver_class=RedisStateManager,
        config={"redis_url": "redis://localhost:6379/0"},
    )
}

guild_spec = GuildSpec(..., dependency_map=state_dep)
```

## Further Reading
- [Execution](execution.md) – how state persists across agent restarts
- [Agents](agents.md) – accessing state inside message handlers
- [Architecture](architecture.md) – where state fits in the big picture 