# Dependencies

RusticAI Core provides a flexible dependency management system for agents and guilds. This enables modular, testable, and extensible agent design.

## Purpose
- Allow agents and guilds to declare required dependencies
- Support runtime resolution and injection of dependencies
- Enable sharing of resources and services

## Core Components

### DependencySpec
A Pydantic model that defines a dependency with:
- `class_name`: The fully qualified name of a `DependencyResolver` class (string)
- `properties`: Configuration parameters passed to the resolver's constructor (JSON dictionary)

### DependencyResolver
An abstract base class that all resolvers must implement:
- Defines an abstract `resolve(guild_id, agent_id)` method that creates/returns the actual dependency
- Provides built-in caching via `get_or_resolve()` (controlled by `memoize_resolution` flag)
- Enables hierarchical dependency resolution through `inject()`

## Declaring Dependencies
Agents and guilds declare dependencies using the `dependency_map` in their specs. Dependencies can be defined at the agent or guild level.

### In Guild Specifications
```python
from rustic_ai.core.guild.dsl import DependencySpec

# Using GuildBuilder
guild_builder = (
    GuildBuilder("my_guild", "My Guild", "Guild with dependencies")
    .set_dependency_map({
        "database": DependencySpec(
            class_name="my_package.resolvers.DatabaseResolver", 
            properties={"connection_string": "postgresql://user:pass@host/db"}
        )
    })
    .add_dependency_resolver(
        "api_client", 
        DependencySpec(
            class_name="my_package.resolvers.ApiClientResolver",
            properties={"api_key": "my-api-key"}
        )
    )
)
```

### In Agent Specifications
```python
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.guild.dsl import DependencySpec

# Agent-specific dependencies
agent_spec = (
    AgentBuilder(MyAgent)
    .set_name("AgentWithDeps")
    .set_description("Agent with dependencies")
    .set_dependency_map({
        "logger": DependencySpec(
            class_name="my_package.resolvers.LoggerResolver",
            properties={"log_level": "DEBUG"}
        )
    })
    .build_spec()
)
```

## Dependency Resolution
- Dependencies are resolved at runtime by the execution engine or agent wrapper
- Dependency resolvers instantiate and inject the required resources
- Guild-level dependencies are available to all agents within the guild
- Agent-level dependencies can override guild-level dependencies with the same key

### Resolver Lifecycle
1. **Lookup** – At agent boot, the DI system reads the `dependency_map` and locates the specified resolver class
2. **Instantiate** – The resolver is instantiated with the provided properties from the DependencySpec
3. **Resolve** – Resolver's `resolve()` method is called to create or retrieve the concrete resource
4. **Cache** – Results are cached based on guild_id and agent_id for efficient reuse
5. **Shared Access** – Guild-level dependencies are shared by all agents requesting them

```python
class MyDatabaseResolver(DependencyResolver):
    def __init__(self, url: str):
        super().__init__()  # Important!
        self._url = url
        self._engine = None

    def resolve(self, guild_id: str, agent_id: str = None):
        if not self._engine:
            self._engine = create_database_engine(self._url)
        return self._engine
```

### Caching and Memoization
By default, dependency resolvers cache their resolved dependencies:
- The cache is a two-level dictionary keyed by `guild_id` and `agent_id`
- Guild-level dependencies use the special `GUILD_GLOBAL` constant as the agent_id
- The `memoize_resolution` class attribute can be set to `False` to disable caching

### Overriding Dependencies in Tests
Testing often requires replacing real services with fakes:

```python
from rustic_ai.core.guild.dsl import DependencySpec
from rustic_ai.testing.helpers import wrap_agent_for_testing

# Create mock dependencies for testing
mock_deps = {
    "database": DependencySpec(
        class_name="tests.mocks.MockDatabaseResolver",
        properties={"connection_string": "mock://in-memory"}
    )
}

# Wrap agent for testing with mock dependencies
test_agent, results = wrap_agent_for_testing(
    my_agent,
    gemstone_generator,
    dependencies=mock_deps
)
```

### Dependency Scopes
| Scope | Visibility | Example |
|-------|------------|---------|
| **Agent** | Only injected into a single agent | Personal API keys |
| **Guild** | Shared by all agents in a guild | Persistent DB connection pool |
| **Global** | Application-wide singletons | Metrics exporter |

## Injecting Dependencies into Handlers

Dependencies are injected into message handler methods using the `depends_on` parameter:

```python
from rustic_ai.core.guild import Agent, agent

class MyAgent(Agent):
    @agent.processor(clz=MyMessageType, depends_on=["database", "api_client"])
    def handle_message(self, ctx, database, api_client):
        # database and api_client are automatically injected
        result = database.query(...)
        api_client.send(result)
```

## Advanced Topics
- **Custom Resolvers**: Implement custom logic for dependency instantiation
- **Dependency Hierarchies**: Resolvers can inject other dependencies using the `inject()` method
- **Testing**: Inject mock dependencies for testing agents in isolation

> See the [Agents](agents.md) and [Guilds](guilds.md) sections for how dependencies are used in practice, and [Dependency Injection](../howto/dependency_injection.md) for a detailed guide. 