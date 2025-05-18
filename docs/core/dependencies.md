# Dependencies

RusticAI Core provides a flexible dependency management system for agents and guilds. This enables modular, testable, and extensible agent design.

## Purpose
- Allow agents and guilds to declare required dependencies
- Support runtime resolution and injection of dependencies
- Enable sharing of resources and services

## Declaring Dependencies
Agents declare dependencies using the `dependency_map` in their `AgentSpec`. Dependencies can be at the agent or guild level.

## Dependency Resolution
- Dependencies are resolved at runtime by the execution engine or agent wrapper.
- Dependency resolvers instantiate and inject the required resources.
- Supports custom dependency types and resolvers.

### Resolver Lifecycle
1. **Lookup** – At agent boot, the DI container reads the `dependency_map` and locates a matching resolver class.
2. **Instantiate** – The resolver receives the YAML/JSON config block and the guild context.
3. **Provide** – Resolver's `provide()` method returns the concrete resource (DB connection, HTTP client, etc.).
4. **Cache** – Guild-level dependencies are memoised so that all agents share the same instance.
5. **Dispose** – On guild shutdown, `dispose()` is called to close connections gracefully.

```python
class MyDatabaseResolver(BaseResolver):
    def __init__(self, url: str):
        self._url = url
        self._engine: sa.Engine | None = None

    def provide(self):
        if not self._engine:
            self._engine = sa.create_engine(self._url)
        return self._engine

    def dispose(self):
        if self._engine:
            self._engine.dispose()
```

### Overriding Dependencies in Tests
Testing often requires replacing real services with fakes:

```python
fake_dep = {
    "database": DependencySpec(resolver_class=FakeDbResolver)
}

agent_spec = AgentBuilder(MyAgent).set_dependency_map(fake_dep).build_spec()
```

### Dependency Scopes
| Scope | Visibility | Example |
|-------|------------|---------|
| **Agent** | Only injected into a single agent | Personal API keys |
| **Guild** | Shared by all agents in a guild | Persistent DB connection pool |
| **Global** | Application-wide singletons | Metrics exporter |

## Example: Declaring and Using a Dependency
```python
from rustic_ai.core.guild.dsl import DependencySpec

# Define a dependency spec
dep_map = {
    "database": DependencySpec(
        resolver_class="MyDatabaseResolver",
        config={"url": "sqlite:///mydb.sqlite"},
    )
}

# Add to agent spec
agent_spec = (
    AgentBuilder(...)
    .set_name("AgentWithDB")
    .set_description("Agent with database dependency.")
    .set_dependency_map(dep_map)
    .build_spec()
)
```

## Advanced Topics
- **Custom Resolvers**: Implement custom logic for dependency instantiation.
- **Guild-Level Dependencies**: Share dependencies across all agents in a guild.
- **Testing**: Inject mock dependencies for testing agents in isolation.

> See the [Agents](agents.md) and [Guilds](guilds.md) sections for how dependencies are used in practice. 