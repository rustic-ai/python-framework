# Dependency Injection in Agents

This guide explains how to use dependency injection in RusticAI agents, which allows you to provide external services and resources to your agents in a clean, modular way.

## Prerequisites

Before you begin, make sure you have:
- Installed RusticAI and its dependencies
- Basic understanding of agents (see [Creating Your First Agent](creating_your_first_agent.md))
- Familiarity with RusticAI [core concepts](../core/index.md)

## Understanding Dependency Injection

Dependency injection in RusticAI allows you to:

1. **Separate concerns**: Keep agent logic separate from external service implementations
2. **Enhance testability**: Easily mock dependencies for testing
3. **Centralize configuration**: Configure services once at the guild level
4. **Share resources**: Reuse the same resources across multiple agents

## How Dependency Injection Works in RusticAI

The dependency injection system in RusticAI consists of these key components:

1. **Dependencies**: External services or resources (e.g., database connections, API clients)
2. **Dependency Resolvers**: Classes that know how to create and configure dependencies
3. **Dependency Specifications**: Configuration for dependency resolvers
4. **Injection Points**: Places in your agent code where dependencies are injected

## Step 1: Create a Dependency Resolver

A dependency resolver is a class that implements the `DependencyResolver` interface. Its job is to create and provide instances of the dependency.

```python
from rustic_ai.core.guild.agent_ext.depends.dependency_resolver import DependencyResolver

# First, define your service class
class DatabaseService:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connected = False
        print(f"DatabaseService created with connection: {connection_string}")
    
    def connect(self):
        print(f"Connecting to {self.connection_string}")
        self.connected = True
        
    def execute_query(self, query: str):
        if not self.connected:
            self.connect()
        print(f"Executing query: {query}")
        return {"result": "data from database"}

# Then, create a resolver for this service
class DatabaseResolver(DependencyResolver):
    def __init__(self, connection_string: str = "sqlite:///:memory:"):
        super().__init__()  # Important to call parent constructor
        self.connection_string = connection_string
        self._db_instance = None
    
    def resolve(self, guild_id: str, agent_id: str = None) -> DatabaseService:
        """Create or return the database service."""
        if self._db_instance is None:
            self._db_instance = DatabaseService(self.connection_string)
        return self._db_instance
```

## Step 2: Configure Dependencies in Your Guild or Agent

You can configure dependencies at the guild level (for all agents) or at the agent level (for specific agents).

### Guild-Level Dependencies

```python
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.guild.dsl import DependencySpec

# Create a guild with a shared database dependency
guild_builder = GuildBuilder("demo_guild", "Demo Guild", "A guild with shared dependencies")

# Set multiple dependencies at once
guild_builder.set_dependency_map({
    "database": DependencySpec(
        class_name="your_package.resolvers.DatabaseResolver",
        properties={"connection_string": "sqlite:///guild_db.sqlite"}
    )
})

# Or add a single dependency
guild_builder.add_dependency_resolver(
    "logger",
    DependencySpec(
        class_name="your_package.resolvers.LoggerResolver",
        properties={"log_level": "INFO"}
    )
)

# Launch the guild
guild = guild_builder.launch()
```

### Agent-Level Dependencies

```python
from rustic_ai.core.guild.builders import AgentBuilder

# Create an agent with its own database dependency
agent_spec = AgentBuilder(MyAgent) \
    .set_name("DataAgent") \
    .set_description("Agent with database access") \
    .set_dependency_map({
        "database": DependencySpec(
            class_name="your_package.resolvers.DatabaseResolver",
            properties={"connection_string": "sqlite:///agent_db.sqlite"}
        )
    }) \
    .build_spec()
```

## Step 3: Inject Dependencies into Handler Methods

Use the `depends_on` parameter in the `@agent.processor` decorator to inject dependencies into your handler methods:

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.dsl import AgentSpec, BaseAgentProps

class QueryRequest(BaseModel):
    """A request to query the database."""
    query: str

class QueryResponse(BaseModel):
    """A response with query results."""
    results: dict

class DatabaseAgent(Agent[BaseAgentProps]):
    """An agent that uses a database dependency."""
    
    def __init__(self, agent_spec: AgentSpec[BaseAgentProps]):
        super().__init__(agent_spec)
        print(f"DatabaseAgent initialized with ID: {self.id}")
    
    @agent.processor(clz=QueryRequest, depends_on=["database"])
    def execute_query(self, ctx: agent.ProcessContext[QueryRequest], database: DatabaseService):
        """Execute a database query using the injected database service."""
        query = ctx.payload.query
        print(f"[{self.name}] Executing query: {query}")
        
        # Use the injected database service
        results = database.execute_query(query)
        
        # Send the response
        ctx.send(QueryResponse(results=results))
```

The key points in this example:

1. The `depends_on=["database"]` parameter specifies the dependency key to inject
2. The handler method has a parameter `database: DatabaseService` that will receive the injected dependency
3. The parameter name must match the key in `depends_on`
4. The type hint is optional but recommended for IDE support

## Dependency Resolution Process

When an agent processes a message:

1. The agent framework identifies the handler method to invoke
2. It checks the `depends_on` list for the handler
3. For each dependency key, it looks for a matching resolver:
   - First in the agent's dependency map
   - Then in the guild's dependency map
4. It calls the resolver's `resolve()` method to get the dependency instance
5. It injects the instance into the handler method

## Dependency Lifetime Management

In RusticAI, dependencies are generally:

1. **Resolved once** per agent or guild (depending on where they're defined)
2. **Cached** by the resolver
3. **Shared** among all handlers in an agent that request the same dependency

This behavior can be customized by implementing different caching strategies in your resolvers:

```python
class NonCachingResolver(DependencyResolver):
    # Disable memoization to create a new instance each time
    memoize_resolution = False
    
    def resolve(self, guild_id: str, agent_id: str = None) -> SomeService:
        # Create a new instance every time
        return SomeService()
```

## Testing with Dependencies

One of the main benefits of dependency injection is easier testing. You can create mock dependencies for testing:

```python
from rustic_ai.testing.helpers import wrap_agent_for_testing
from rustic_ai.core.utils.gemstone_id import GemstoneGenerator

# Create a mock resolver for testing
class MockDatabaseResolver(DependencyResolver):
    def resolve(self, guild_id: str, agent_id: str = None) -> DatabaseService:
        """Return a mock database service for testing."""
        mock_db = DatabaseService("mock://in-memory")
        # Override the execute_query method for testing
        mock_db.execute_query = lambda query: {"result": "mocked data", "query": query}
        return mock_db

# Test setup
def test_database_agent():
    # Create the agent
    agent = AgentBuilder(DatabaseAgent) \
        .set_name("TestDBAgent") \
        .build()
    
    # Configure mock dependencies
    mock_dependencies = {
        "database": DependencySpec(
            class_name="__main__.MockDatabaseResolver",
            properties={}
        )
    }
    
    # Wrap the agent for testing with mock dependencies
    test_agent, results = wrap_agent_for_testing(
        agent,
        GemstoneGenerator(machine_id=1),
        dependencies=mock_dependencies
    )
    
    # Create a test message
    message = Message(
        id_obj=GemstoneGenerator(machine_id=1).get_id(Priority.NORMAL),
        topics=["test_topic"],
        sender=AgentTag(id="test_sender", name="Tester"),
        payload=QueryRequest(query="SELECT * FROM test").model_dump(),
        format=QueryRequest.model_json_schema()["$id"]
    )
    
    # Process the message
    test_agent._on_message(message)
    
    # Check results
    assert len(results) == 1
    assert "mocked data" in results[0].payload["results"]["result"]
```

## Advanced Dependency Injection Patterns

### Multiple Dependencies

You can inject multiple dependencies into a single handler:

```python
@agent.processor(clz=ComplexRequest, depends_on=["database", "api_client", "logger"])
def handle_complex_request(
    self, 
    ctx: agent.ProcessContext[ComplexRequest], 
    database: DatabaseService, 
    api_client: ApiClient,
    logger: Logger
):
    # Use all three dependencies
    logger.info("Processing complex request")
    db_data = database.execute_query("SELECT * FROM data")
    api_result = api_client.call_api("endpoint", db_data)
    ctx.send(ComplexResponse(result=api_result))
```

### Dependency Hierarchies

Dependencies can depend on other dependencies:

```python
class ApiClientResolver(DependencyResolver):
    def __init__(self, api_key: str, cache_service_key: str = "cache"):
        super().__init__()
        self.api_key = api_key
        self.cache_service_key = cache_service_key
        self._api_client = None
    
    def resolve(self, guild_id: str, agent_id: str = None) -> ApiClient:
        if self._api_client is None:
            # Inject another dependency using the inject method
            cache_service = self.inject(CacheService, self.cache_service_key, guild_id, agent_id)
            self._api_client = ApiClient(self.api_key, cache_service)
        return self._api_client
```

## Best Practices for Dependency Injection

1. **Keep Resolvers Simple**: Resolvers should focus on creating and configuring the service, not on business logic.

2. **Use Guild-Level Dependencies** for shared resources that should be the same for all agents.

3. **Use Agent-Level Dependencies** for resources that are specific to a single agent.

4. **Cache Appropriately**: Most resolvers should cache dependency instances, but be careful with resources that need explicit cleanup.

5. **Type Hint Your Dependencies**: Use type hints to make your code more readable and catch errors early.

6. **Design for Testability**: Make your dependencies easy to mock for testing.

7. **Document Dependencies**: Clearly document what dependencies your agents need and what they do.

## Example: A Complete Agent with Dependency Injection

Here's a complete example of an agent that uses dependency injection:

```python
from pydantic import BaseModel
from typing import Dict, Any, List
from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.dsl import AgentSpec, BaseAgentProps

# Message models
class ApiRequest(BaseModel):
    """A request to call an API."""
    endpoint: str
    data: Dict[str, Any]

class ApiResponse(BaseModel):
    """A response from an API call."""
    result: Dict[str, Any]

# External service
class ApiService:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        print(f"ApiService initialized with key '{api_key}' and URL '{base_url}'")
    
    def call_api(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call an API endpoint."""
        print(f"Calling API endpoint '{endpoint}' with data: {data}")
        # In a real implementation, this would make an HTTP request
        return {
            "endpoint": endpoint,
            "input": data,
            "result": "API response data",
            "timestamp": "2023-01-01T12:00:00Z"
        }

# Dependency resolver
class ApiServiceResolver(DependencyResolver):
    def __init__(self, api_key: str = "default_key", base_url: str = "https://api.example.com"):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url
        self._api_service = None
    
    def resolve(self, guild_id: str, agent_id: str = None) -> ApiService:
        """Create or return the API service."""
        if self._api_service is None:
            self._api_service = ApiService(self.api_key, self.base_url)
        return self._api_service

# Agent that uses the dependency
class ApiAgent(Agent[BaseAgentProps]):
    """An agent that makes API calls using an injected API service."""
    
    def __init__(self, agent_spec: AgentSpec[BaseAgentProps]):
        super().__init__(agent_spec)
        print(f"ApiAgent initialized with ID: {self.id}")
    
    @agent.processor(clz=ApiRequest, depends_on=["api_service"])
    def call_api(self, ctx: agent.ProcessContext[ApiRequest], api_service: ApiService):
        """Call an API using the injected API service."""
        request = ctx.payload
        
        print(f"[{self.name}] Calling API endpoint '{request.endpoint}'")
        
        # Use the injected API service
        result = api_service.call_api(request.endpoint, request.data)
        
        # Send the response
        ctx.send(ApiResponse(result=result))
```

## Next Steps

Now that you understand dependency injection, you might want to:

- Learn how to [manage state in agents](state_management.md)
- Explore [creating custom guild specifications](creating_a_guild.md)
- Understand [testing and debugging](testing_agents.md) agents with dependencies

For a complete example, see the [Dependency Injection Example](../../examples/basic_agents/dependency_injection_example.py) in the examples directory. 