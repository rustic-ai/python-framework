# Agents

Agents are the fundamental, autonomous, and message-driven entities in RusticAI. They encapsulate specific logic, maintain their own state, communicate with other agents via asynchronous messages, and collaborate within a [Guild](guilds.md) to achieve complex tasks. Agents can represent automated processes (bots) or act as proxies for human users.

**Prerequisites**: Familiarity with [Guilds](guilds.md), [Messaging](messaging.md), [State Management](state_management.md), and [Dependencies](dependencies.md) is recommended.

## Table of Contents
- [Core Concepts](#core-concepts)
- [Defining an Agent Class](#defining-an-agent-class)
- [Agent Specification (AgentSpec)](#agent-specification-agentspec)
- [The AgentMetaclass and its Magic](#the-agentmetaclass-and-its-magic)
- [Message Handling](#message-handling)
- [Agent Fixtures and Modifiers](#agent-fixtures-and-modifiers-agentfixtures)
- [Dependency Injection in Handlers](#dependency-injection-in-handlers)
- [Agent State Management](#agent-state-management)
- [Error Handling Strategies](#error-handling-strategies)
- [Testing Agents in Isolation](#testing-agents-in-isolation)
- [Agent Mixins: Behind-the-Scenes Support](#agent-mixins-behind-the-scenes-support)
- [Advanced Topics](#advanced-topics)

## Core Concepts
- **Encapsulation**: Agents bundle their own logic, configuration, and state.
- **Message-Driven**: Agents react to incoming messages, process them, and can send new messages.
- **Stateful**: Agents can maintain internal state across message interactions. See [State Management](state_management.md).
- **Collaborative**: Agents operate within Guilds, allowing for coordinated multi-agent workflows.
- **Configurable**: Agent behavior is defined by their Python class and configured via an `AgentSpec`.

## Agent Types and Modes

RusticAI provides two enumerations that define fundamental characteristics of agents:

### AgentType

`AgentType` specifies the nature of the agent:

```python
from rustic_ai.core.guild import AgentType

# Usage:
class MyAgent(Agent[BaseAgentProps]):
    def __init__(self, agent_spec: AgentSpec[BaseAgentProps]):
        super().__init__(agent_spec, agent_type=AgentType.BOT)  # Default is BOT
```

| Value | Description |
|-------|-------------|
| `AgentType.BOT` | A fully automated agent that operates without human intervention (default) |
| `AgentType.HUMAN` | Represents a human user or requires human participation |

### AgentMode

`AgentMode` defines how the agent is executed by the execution engine:

```python
from rustic_ai.core.guild import AgentMode

# Usage:
class MyAgent(Agent[BaseAgentProps]):
    def __init__(self, agent_spec: AgentSpec[BaseAgentProps]):
        super().__init__(agent_spec, agent_mode=AgentMode.LOCAL)  # Default is LOCAL
```

| Value | Description |
|-------|-------------|
| `AgentMode.LOCAL` | Runs in the same process as the Guild (default) |
| `AgentMode.REMOTE` | Runs in a separate process (potentially distributed) |

These values are used by the execution engine to determine how to instantiate and run the agent, especially in distributed or multi-process environments.

## Defining an Agent Class

To create a custom agent, you define a Python class that inherits from `rustic_ai.core.guild.Agent`. This base class, along with the powerful `AgentMetaclass`, provides the core machinery for message handling, dependency injection, and lifecycle management.

### Agent Properties (`BaseAgentProps`)
Each agent can have its own set of configurable properties. These are defined in a Pydantic model that inherits from `rustic_ai.core.guild.dsl.BaseAgentProps`.

```python
from rustic_ai.core.guild import Agent, agent  # agent provides the @agent.processor decorator
from rustic_ai.core.guild.dsl import BaseAgentProps, AgentSpec

# 1. Define messages models
class GreetRequest(BaseModel):
    name: Optional[str]

class GreetResponse(BaseModel):
    greeting: str
    count: int

# 1. Define Properties Model (Optional but Recommended)
class MyGreeterAgentProps(BaseAgentProps):
    greeting_prefix: str = "Hello"
    default_name: str = "World"

# 2. Define the Agent Class
class GreeterAgent(Agent[MyGreeterAgentProps]): # Generic type specifies the props model
    def __init__(self, agent_spec: AgentSpec[MyGreeterAgentProps]):
        super().__init__(agent_spec)
        # Access configured properties:
        self.greeting_prefix = self.get_spec().props.greeting_prefix
        self.default_name = self.get_spec().props.default_name
        self.greet_count = 0

    @agent.processor(clz=GreetRequest) # Handles raw string payloads
    def handle_name(self, ctx: agent.ProcessContext[GreetRequest]):
        name_to_greet = ctx.payload.name if ctx.payload.name else self.default_name
        response = f"{self.greeting_prefix}, {name_to_greet}!"
        self.greet_count += 1
        
        # Update agent's own state (illustrative, actual state updates are more structured)
        # self._state["greet_count"] = self.greet_count 
        
        ctx.send_dict(GreetResponse(greeting = response, count=count))

# To use this agent, you'd create an AgentSpec for it, often via AgentBuilder.
# from rustic_ai.core.guild.builders import AgentBuilder
# greeter_spec = AgentBuilder(GreeterAgent) \\
#     .set_name("MyGreeter") \\
#     .set_description("A friendly greeter agent.") \\
#     .set_properties(MyGreeterAgentProps(greeting_prefix="Greetings")) \\
#     .build_spec()
```
- The agent class is generic: `Agent[MyAgentPropsType]`. This tells the system about the expected structure of its `properties`.
- The `__init__` method must call `super().__init__(agent_spec)`.
- The `agent_spec` (an instance of `AgentSpec[MyAgentPropsType]`) provides access to configured properties via `self.get_spec().props`.

## Agent Specification (`AgentSpec`)

As introduced in [Guilds](guilds.md), an `AgentSpec` is a data structure (typically created via `AgentBuilder` or loaded from YAML/JSON) that defines an agent's configuration. Key fields relevant from an agent's perspective:

-   `id` (str): Unique identifier.
-   `name` (str): Human-readable name.
-   `description` (str): Purpose of the agent.
-   `class_name` (str): The fully qualified Python class name of the agent (e.g., `"my_project.agents.GreeterAgent"`).
-   `properties` (Pydantic Model | Dict): An instance of the agent's properties model (e.g., `MyGreeterAgentProps`) or a dictionary that can be validated into it. This is how you customize an agent instance.
-   `additional_topics` (List[str]): Specific message topics the agent subscribes to, beyond the default guild topic.
-   `listen_to_default_topic` (bool): If `True` (default), the agent listens to messages on the guild's default topic.
-   `dependency_map` (Dict[str, DependencySpec]): Agent-specific [dependencies](dependencies.md). These can override or supplement guild-level dependencies.
-   `act_only_when_tagged` (bool): If `True`, the agent will only process messages where its `AgentTag` (ID or name) is explicitly included in the message's `recipient_list`. This is useful for targeted communication in busy topics.
-   `predicates` (Dict[str, SimpleRuntimePredicate]): A dictionary mapping method names (of `@processor` decorated methods) to `SimpleRuntimePredicate` objects. A predicate contains a JSONata expression that is evaluated against the incoming message, agent state, and guild state. The handler method is only invoked if the predicate evaluates to true.

    ```json
    // Example predicate in AgentSpec (conceptual)
    "predicates": {
        "handle_urgent_task": {
            "expression": "message.priority > 7 and agent_state.is_available"
        }
    }
    ```

## The `AgentMetaclass` and its Magic

The `Agent` base class uses `AgentMetaclass`. This metaclass works behind the scenes during agent class definition to automate several setup tasks:

-   **Handler Registration**: It inspects the agent class for methods decorated with `@agent.processor(...)` and registers them as message handlers.
-   **Fixture Registration**: It finds methods decorated with `@AgentFixtures.*` and registers them as lifecycle hooks or message modifiers.
-   **Properties Type Inference**: It determines the agent's specific properties type (e.g., `MyGreeterAgentProps`) from the generic type hint (`Agent[MyGreeterAgentProps]`).
-   **Dependency Analysis**: It can analyze `@processor` methods for `depends_on` arguments to understand their dependencies.
-   **Mixin Injection**: It automatically includes default mixins (e.g., `StateRefresherMixin`, `HealthMixin`, `TelemetryMixin`) that provide common cross-cutting concerns.

This automation reduces boilerplate and allows developers to focus on the agent's core logic.

## Message Handling

Agents are fundamentally message-driven. The process of an agent receiving and handling a message involves several steps, orchestrated by the `AgentMetaclass` and the `Agent` base class.

### The `@agent.processor` Decorator

Methods that handle incoming messages are decorated with `@agent.processor`.

```python
from pydantic import BaseModel
from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.agent import ProcessContext
from rustic_ai.core.messaging.core import JsonDict # For raw JSON

class MyData(BaseModel):
    value: str
    count: int

class MyOtherAgent(Agent[BaseAgentProps]):
    # Handles messages where payload is MyData
    @agent.processor(clz=MyData)
    def handle_my_data(self, ctx: ProcessContext[MyData]):
        data_object = ctx.payload # data_object is an instance of MyData
        # ... process data_object ...
        ctx.send(AnotherMessage(...))

    # Handles messages where payload is a raw JSON dictionary
    @agent.processor(clz=JsonDict)
    def handle_any_json(self, ctx: ProcessContext[JsonDict]):
        raw_payload = ctx.payload # raw_payload is a dict
        # ... process raw_payload ...
        ctx.send_dict({"status": "processed raw json"})

    # Handles messages of MyData type only on "essential" topics,
    # and also injects a 'db_connection' dependency.
    @agent.processor(clz=MyData, handle_essential=True, depends_on=["db_connection"])
    def handle_essential_data(self, ctx: ProcessContext[MyData], db_connection: Any):
        # This handler will run for MyData messages on system/status topics
        # even if the agent doesn't explicitly subscribe to them.
        # db_connection is resolved and injected.
        pass
```

-   **`clz`**: Specifies the expected Pydantic model for the message payload. If the incoming message's `format` matches the qualified name of this model, the payload is automatically parsed and validated into an instance of this model. Use `JsonDict` to receive the payload as a raw dictionary without parsing.
-   **`handle_essential`** (bool, default `False`): If `True`, this handler can process messages on essential guild topics (like status or system topics), even if the agent isn't explicitly subscribed to them or if the message isn't directly addressed to it.
-   **`depends_on`** (List[str | AgentDependency], optional): A list of dependency keys. These dependencies are resolved at runtime and injected as arguments into the handler method. See [Dependency Injection in Handlers](#dependency-injection-in-handlers).
-   **`predicate`** (Callable[[Agent, Message], bool], optional, less common): An older style of predicate, a callable that takes the agent instance and the raw message and returns `True` if the handler should run. Prefer `AgentSpec.predicates` for declarative JSONata-based predicates.

### Asynchronous Handlers


```python
from aiohttp import ClientSession

class AsyncAgent(Agent[BaseAgentProps]):
    @agent.processor(clz=SearchQuery)
    async def search_web(self, ctx: ProcessContext[SearchQuery]):
        query = ctx.payload.query
        
        # Perform asynchronous operations
        async with ClientSession() as session:
            async with session.get(f"https://api.example.com/search?q={query}") as response:
                result = await response.json()
                
        # Process results and respond
        ctx.send(SearchResult(results=result["items"]))
```

When an async handler is invoked:
1. The framework detects it's an async function via `inspect.iscoroutinefunction()`
2. The `ProcessorHelper.run_coroutine()` method handles scheduling:
   - If in an already running event loop, it creates a new task
   - Otherwise, it calls `asyncio.run()` to run the coroutine to completion

This allows your agent to perform non-blocking I/O operations like network requests or database queries without blocking the entire agent/guild.

### Incoming Message Flow

1.  **Delivery**: A message is delivered to the agent's internal `_on_message(self, message: Message)` method by the messaging system.
2.  **Handler Discovery**:
    *   The `Agent` base class, using handler maps prepared by `AgentMetaclass`, identifies applicable `@processor` methods.
    *   This matching considers:
        *   The `format` string in the `Message` against the `clz` argument of `@processor`.
        *   If `agent_spec.act_only_when_tagged` is `True`, the message must explicitly tag the agent.
        *   The `handle_essential` flag of the processor if the message is on an essential topic.
3.  **Processing Each Applicable Handler**: For each matched handler method:
    *   **Runtime Predicate Check**: If a predicate is defined for this handler in `agent_spec.predicates`, it's evaluated. If it returns `False`, the handler is skipped.
    *   **Dependency Resolution**: Dependencies specified in `@processor(depends_on=[...])` are resolved.
    *   **`ProcessContext` Creation**: A `ProcessContext` instance (`ctx`) is created, providing access to the message, payload, agent state, and sending capabilities.
    *   **`before_process` Fixtures**: Any methods decorated with `@AgentFixtures.before_process` are executed.
    *   **Handler Invocation**: The handler method is called with `self` (the agent instance), `ctx` (the `ProcessContext`), and any resolved dependencies as arguments.
    *   **`after_process` Fixtures**: Any methods decorated with `@AgentFixtures.after_process` are executed.
    *   **Error Handling**: If the handler raises an unhandled exception, it's caught, wrapped in an `ErrorMessage`, and sent out (triggering `on_send_error` fixtures). The exception might also be bubbled to the execution engine.

### The `ProcessContext` (`ctx`)

The `ProcessContext` is passed as the second argument (after `self`) to every message handler and provides essential tools for message processing:

-   **`ctx.payload` -> `MDT` (MessageDataType)**:
    *   If the `@processor` specified a Pydantic model (e.g., `clz=MyData`), `ctx.payload` is an instance of that model, automatically parsed and validated from the message's payload.
    *   If `clz=JsonDict`, `ctx.payload` is the raw dictionary payload.
-   **`ctx.message` -> `Message`**: The full incoming `Message` object, including headers, sender/recipient info, topic, `routing_slip`, etc.
-   **`ctx.agent` -> `Agent`**: The instance of the agent processing the message.
-   **`ctx.method_name` -> `str`**: The name of the handler method currently being executed.
-   **`ctx.update_context(updates: JsonDict)`**: Updates a temporary, per-message-processing-flow, session-like state. This context is passed along if messages are sent via `ctx.send()` and the routing rules dictate context propagation.
-   **`ctx.get_context() -> JsonDict`**: Retrieves the current per-message-flow context.
-   **`ctx.add_routing_step(routing_entry: RoutingRule)`**: Adds a new `RoutingRule` to the `RoutingSlip` of the *original incoming message*. This can dynamically alter the message's future path if it's part of a multi-step workflow.
-   **Sending Methods**:
    *   **`ctx.send(payload: BaseModel, new_thread: bool = False, forwarding: bool = False) -> List[GemstoneID]`**:
        Sends a new message with a Pydantic `BaseModel` as its payload.
        -   `new_thread`: If `True`, starts a new message thread ID.
        -   `forwarding`: If `True`, indicates the message is being forwarded, which can affect routing rule application (e.g., `mark_forwarded`).
    *   **`ctx.send_dict(payload: JsonDict, format: str = MessageConstants.RAW_JSON_FORMAT, new_thread: bool = False, forwarding: bool = False) -> List[GemstoneID]`**:
        Sends a new message with a raw dictionary as its payload. The `format` string should indicate the type of the payload.
    *   **`ctx.send_error(payload: BaseModel) -> List[GemstoneID]`**:
        Sends a new message marked as an error, typically using an `ErrorMessage` or a custom error model.

    When `ctx.send*` is called:
    1.  Registered `@AgentFixtures.on_send` (or `@AgentFixtures.on_send_error` for `send_error`) fixtures are executed.
    2.  The routing logic (detailed in [Guilds](guilds.md) and [Messaging](messaging.md)) determines the next step(s) based on the incoming message's `RoutingSlip` or guild-level routes.
    3.  For each routing step, a new `Message` is constructed.
    4.  Registered `@AgentFixtures.outgoing_message_modifier` fixtures can alter the new message before it's published.
    5.  The message is published via the agent's messaging client.
    6.  IDs of the sent messages are returned.

### End-to-End Handler Example

```python
from pydantic import BaseModel
from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.agent import ProcessContext
from rustic_ai.core.guild.dsl import BaseAgentProps

class UserQuery(BaseModel):
    text: str
    user_id: str

class QueryResponse(BaseModel):
    answer: str
    source: str

class MyQnAAgent(Agent[BaseAgentProps]):
    @agent.processor(clz=UserQuery)
    def handle_query(self, ctx: ProcessContext[UserQuery]):
        query_text = ctx.payload.text # Accessing typed payload
        user = ctx.payload.user_id
        
        # Illustrative: update per-message context
        ctx.update_context({"current_user_id": user, "query_received_at": "timestamp"})
        
        print(f"Agent {self.name} received query: '{query_text}' from {user}")
        print(f"Original message ID: {ctx.message.id}, Topic: {ctx.message.topic_published_to}")

        # Simulate processing
        answer = f"Answer to '{query_text}'"
        
        response_payload = QueryResponse(answer=answer, source=self.name)
        
        # Send the response
        # Routing will be determined by incoming message's slip or guild routes
        sent_ids = ctx.send(response_payload) 
        print(f"Sent response message(s) with IDs: {sent_ids}")
```

## Agent Fixtures and Modifiers (`@AgentFixtures`)

Fixtures allow you to inject logic at various points in an agent's message processing lifecycle or when messages are sent. They are methods in your agent class decorated with specific decorators from `rustic_ai.core.guild.agent.AgentFixtures`.

-   **`@AgentFixtures.before_process`**:
    -   Signature: `def my_fixture(self, ctx: ProcessContext[MDT])`
    -   Called before each message handler (`@processor`) method is executed for a message that the handler matches. `MDT` is the type the handler expects.
-   **`@AgentFixtures.after_process`**:
    -   Signature: `def my_fixture(self, ctx: ProcessContext[MDT])`
    -   Called after each message handler method completes (normally or with an exception that was handled by the system).
-   **`@AgentFixtures.on_send`**:
    -   Signature: `def my_fixture(self, ctx: ProcessContext[Any])`
    -   Called when `ctx.send()` or `ctx.send_dict()` is invoked (but *not* `ctx.send_error()`), before the routing logic determines the final outgoing message(s). The `ctx` here is the context of the handler that *initiated* the send.
-   **`@AgentFixtures.on_send_error`**:
    -   Signature: `def my_fixture(self, ctx: ProcessContext[Any])`
    -   Called when `ctx.send_error()` is invoked, before the routing logic.
-   **`@AgentFixtures.outgoing_message_modifier`**:
    -   Signature: `def my_fixture(self, ctx: ProcessContext[Any], message_to_be_sent: Message)`
    -   Called for each message that is about to be published via the agent's client (resulting from `ctx.send*` calls). Allows direct modification of the `message_to_be_sent` object (e.g., adding custom headers) before it goes out.

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.agent import AgentFixtures, ProcessContext, Message
from rustic_ai.core.guild.dsl import BaseAgentProps
from pydantic import BaseModel

class LoggableEvent(BaseModel):
    event_data: str

class FixtureDemoAgent(Agent[BaseAgentProps]):
    def __init__(self, agent_spec):
        super().__init__(agent_spec)
        self.processed_count = 0
        self.sent_count = 0

    @agent.processor(LoggableEvent)
    def log_event(self, ctx: ProcessContext[LoggableEvent]):
        print(f"HANDLER: Processing event: {ctx.payload.event_data}")
        ctx.send(LoggableEvent(event_data="Response to " + ctx.payload.event_data))

    @AgentFixtures.before_process
    def count_incoming(self, ctx: ProcessContext[LoggableEvent]):
        self.processed_count +=1
        print(f"BEFORE_PROCESS: Message #{self.processed_count} for {ctx.method_name}. Payload: {ctx.payload}")

    @AgentFixtures.after_process
    def confirm_processed(self, ctx: ProcessContext[LoggableEvent]):
        print(f"AFTER_PROCESS: Finished processing for {ctx.method_name}.")

    @AgentFixtures.on_send
    def count_outgoing(self, ctx: ProcessContext[LoggableEvent]): # Context of the calling handler
        self.sent_count += 1
        print(f"ON_SEND: Agent {self.name} is sending message #{self.sent_count} (initiated by {ctx.method_name}).")

    @AgentFixtures.outgoing_message_modifier
    def add_custom_header(self, ctx: ProcessContext[LoggableEvent], message_to_be_sent: Message):
        print(f"OUTGOING_MODIFIER: Modifying message ID {message_to_be_sent.id}")
        if message_to_be_sent.payload: # Ensure payload exists
             message_to_be_sent.payload["modified_by"] = self.name # Example modification
```

## Dependency Injection in Handlers

Message handlers can declare dependencies that are automatically resolved and injected by the framework when the handler is called. This is done using the `depends_on` argument of the `@agent.processor` decorator.

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.agent import ProcessContext
from rustic_ai.core.guild.dsl import BaseAgentProps, AgentSpec, DependencySpec
# Assume MyDatabaseService and MyApiClient are defined elsewhere

# Example Dependency Resolvers (simplified, see dependencies.md for full structure)
class MyDatabaseResolver: # Implements rustic_ai.core.guild.agent_ext.depends.DependencyResolver
    def __init__(self, connection_string: str): 
        super().__init__()
        self.conn_str = connection_string
    def resolve(self, guild_id, agent_id=None): return f"DBConnection({self.conn_str})" # Returns actual service

class MyApiClientResolver:
    def __init__(self, api_key: str): 
        super().__init__()
        self.api_key = api_key
    def resolve(self, guild_id, agent_id=None): return f"ApiClient(key={self.api_key})"

class OrderRequest(BaseModel):
    item_id: str
    quantity: int

class OrderProcessorAgent(Agent[BaseAgentProps]):
    @agent.processor(clz=OrderRequest, depends_on=["db", "api_client"])
    def process_order(self, ctx: ProcessContext[OrderRequest], db: str, api_client: str):
        # 'db' will be an instance of MyDatabaseService (or whatever the resolver returns)
        # 'api_client' will be an instance of MyApiClient
        print(f"Processing order for item {ctx.payload.item_id} using DB: {db} and API: {api_client}")
        # ... use db and api_client ...
        ctx.send_dict({"status": "order processed"})

# In AgentSpec for OrderProcessorAgent:
# "dependency_map": {
#   "db": { 
#       "class_name": "my_project.resolvers.MyDatabaseResolver", 
#       "properties": {"connection_string": "prod_db_uri"} 
#   },
#   "api_client": { 
#       "class_name": "my_project.resolvers.MyApiClientResolver", 
#       "properties": {"api_key": "secret_key"}
#   }
# }
# Or these could be defined at the Guild level and inherited/overridden.
```

-   The `depends_on` list contains string keys.
-   These keys must match entries in the agent's own `dependency_map` or the `dependency_map` of its [Guild](guilds.md).
-   The corresponding `DependencySpec` defines a resolver class and its configuration.
-   The resolver's `resolve()` method is called to provide the dependency instance.
-   The names of the parameters in the handler method must match the keys in `depends_on`.

Refer to the [Dependencies documentation](dependencies.md) for a full explanation of dependency resolvers.

## Agent State Management

Agents are often stateful. RusticAI provides mechanisms for managing agent state persistently.

-   **Internal State Access**: Within an agent, `self._state` holds a dictionary representing the agent's current state. `self._guild_state` holds the guild's state. **Direct modification of these is generally discouraged for persistence.**
-   **`StateRefresherMixin`**: This default mixin, added by `AgentMetaclass`, handles messages like `StateFetchResponse` and `StateUpdateResponse` to keep `self._state` and `self._guild_state` synchronized with the authoritative `StateManager`.
-   **Requesting State Changes**: To persist state changes, an agent typically sends a `StateUpdateRequest` message (often to a system topic like `GuildTopics.GUILD_STATUS_TOPIC`). The `StateManager` (via a system agent like `GuildManagerAgent` or a dedicated state agent) processes this request.
-   **`ProcessContext` and State**: While `ctx.update_context()` modifies a per-message-flow temporary context, it does *not* directly persist to the agent's long-term state.

```python
# Conceptual example of an agent requesting a state update
# (Actual implementation details may vary based on system setup)
from rustic_ai.core.state.models import StateOwner, StateUpdateRequest

# Inside a handler:
# new_state_values = {"last_processed_id": ctx.message.id, "item_count": self.item_count + 1}
# update_request = StateUpdateRequest(
#     state_owner=StateOwner.AGENT,
#     guild_id=self.guild_id,
#     agent_id=self.id,
#     update_format="MERGE_DICT", # or "REPLACE_DICT", "JMESPATH_UPDATE"
#     state_update=new_state_values 
# )
# # Send this request, typically to a system topic
# ctx.send_dict(payload=update_request.model_dump(), format=StateUpdateRequest.get_qualified_class_name(), ...)
```

For detailed information, see the [State Management documentation](state_management.md).

## Error Handling Strategies

Robust agents need to handle errors gracefully.

1.  **Standard Exceptions in Handlers**:
    *   If a `@processor` method raises an unhandled Python exception:
        1.  The system catches the exception.
        2.  It wraps the error details into an `ErrorMessage` (or similar).
        3.  `ctx.send_error()` is implicitly called with this `ErrorMessage`.
        4.  This triggers any `@AgentFixtures.on_send_error` hooks.
        5.  The `ErrorMessage` is then published, often to a designated error topic or back to the sender based on routing.
        6.  The original exception might also be logged and potentially bubbled up to the `ExecutionEngine`, which could have policies for restarting the agent.

2.  **Custom Typed Errors (`AgentError`)**:
    *   For business logic errors or expected fault conditions, it's good practice to define custom exception classes inheriting from `rustic_ai.core.guild.AgentError` (or a more specific base error if available).
    *   Raise these custom errors from your handlers.
    *   Other agents can then have `@processor` methods specifically for these custom error types, allowing for targeted error handling workflows.

```python
# Create your own error class to support domain-specific error handling
from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.agent import ProcessContext
from pydantic import BaseModel

# Define a custom error class based on exception or a framework base
class AgentError(Exception):
    """Base class for agent-specific exceptions"""
    pass

class InsufficientStockError(AgentError):
    item_id: str
    requested_qty: int
    available_qty: int

    def __init__(self, item_id: str, requested_qty: int, available_qty: int, message: str = "Insufficient stock"):
        super().__init__(message)
        self.item_id = item_id
        self.requested_qty = requested_qty
        self.available_qty = available_qty

class OrderRequest(BaseModel):
    item_id: str
    quantity: int
    
class StockCheckerAgent(Agent[BaseAgentProps]):
    @agent.processor(OrderRequest)
    def check_stock(self, ctx: ProcessContext[OrderRequest]):
        # ... logic to check stock ...
        available = 5 # simplified
        if ctx.payload.quantity > available:
            raise InsufficientStockError(
                item_id=ctx.payload.item_id, 
                requested_qty=ctx.payload.quantity, 
                available_qty=available
            )
        # ... proceed with order ...
        ctx.send_dict({"status": "stock_ok"})

class ErrorHandlerAgent(Agent[BaseAgentProps]):
    @agent.processor(InsufficientStockError) # Handles the specific typed error
    def handle_stock_error(self, ctx: ProcessContext[InsufficientStockError]):
        error_data = ctx.payload # error_data is an InsufficientStockError instance
        print(f"Stock error: Item {error_data.item_id}, wanted {error_data.requested_qty}, have {error_data.available_qty}")
        # ... notify user, log, etc. ...
```

## Testing Agents in Isolation

RusticAI promotes robust unit and integration testing of agents. The framework provides utilities, most notably `wrap_agent_for_testing` from `rustic_ai.testing.helpers`, to simplify the setup and execution of agent tests.

The `wrap_agent_for_testing` helper typically handles:
-   **Agent Instantiation**: Taking an agent instance (usually created via `AgentBuilder(...).build()`).
-   **Dependency Setup**: Allowing you to provide `DependencySpec`s for the agent's dependencies, enabling the use of mock resolvers or test-specific configurations.
-   **Message ID Generation**: Often takes a `generator` (e.g., a `GemstoneGenerator` instance) for creating unique message IDs during the test.
-   **Outgoing Message Capture**: It returns the configured agent instance and a `results` list, which automatically collects all messages sent by the agent under test.

### Unit Testing with `wrap_agent_for_testing`

Here's how you typically test an agent:

```python
import pytest
import asyncio # For testing async handlers
from pydantic import BaseModel # For defining message payloads
from typing import Any, Callable # For type hinting mock callables

from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.guild.dsl import AgentSpec, BaseAgentProps, DependencySpec
from rustic_ai.core.guild.agent import ProcessContext # For type hinting if needed
from rustic_ai.core.messaging.core.message import Message, AgentTag, MessageConstants
from rustic_ai.core.utils.basic_class_utils import get_qualified_class_name
from rustic_ai.core.utils.priority import Priority
from rustic_ai.core.utils.gemstone_id import GemstoneGenerator, GemstoneID # For ID generation in tests
from rustic_ai.testing.helpers import wrap_agent_for_testing # The real helper for testing agents
```

#### Example Test Setup

```python
# Agent under test 
class GreeterAgentProps(BaseAgentProps):
    greeting: str = "Hello"

class GreetingResponse(BaseModel):
    message: str

class GreeterAgent(Agent[GreeterAgentProps]):
    def __init__(self, agent_spec: AgentSpec[GreeterAgentProps]):
        super().__init__(agent_spec)
        
    @agent.processor(clz=str)
    def greet(self, ctx: ProcessContext[str]):
        name = ctx.payload or "World"
        ctx.send(GreetingResponse(message=f"{self.get_spec().props.greeting}, {name}!"))

# Test fixture
@pytest.fixture
def greeter_test_setup():
    # Create agent instance
    agent_instance = AgentBuilder(GreeterAgent)\
        .set_name("TestGreeter")\
        .set_properties(GreeterAgentProps(greeting="Greetings"))\
        .build()
    
    # Set up for testing
    id_generator = GemstoneGenerator(machine_id=1)
    test_agent, results = wrap_agent_for_testing(agent_instance, id_generator)
    
    return test_agent, results, id_generator

# Actual test
def test_greeter(greeter_test_setup):
    agent, results, id_generator = greeter_test_setup
    
    # Create test message
    msg = Message(
        id_obj=id_generator.get_id(Priority.NORMAL),
        topics=["test_topic"],
        sender=AgentTag(id="test_sender", name="Tester"),
        payload="Friend",
        format="str"  # Matches @agent.processor(clz=str)
    )
    
    # Deliver message
    agent._on_message(msg)
    
         # Verify response
     assert len(results) == 1
     response = GreetingResponse.model_validate(results[0].payload)
     assert response.message == "Greetings, Friend!"
```

### Key Aspects of Testing with `wrap_agent_for_testing`

- **Agent Instantiation**: Pass an *instance* of your agent (usually from `AgentBuilder(...).build()`) to `wrap_agent_for_testing`.
- **Dependency Management**:
  - Provide a `dependencies` dictionary to `wrap_agent_for_testing`. The keys are dependency names (as used in `@agent.processor(depends_on=[...])`) and values are `DependencySpec` objects.
  - Your `DependencySpec` in the test should point to a mock resolver or a real resolver configured for a test environment. The mock resolver's `resolve()` method should return the mock object/function your agent expects.
- **Simulating Input**: Craft `Message` objects with appropriate `payload`, `format`, `sender`, `id_obj` (using the provided `id_generator`), etc., to correctly trigger your target handler.
- **Invoking Handler**: Call `agent_instance._on_message(input_message)` to simulate message arrival. The `AgentMetaclass` and base `Agent` logic will then find and invoke the correct `@processor`.
- **Capturing & Asserting Output**: The `results` list returned by `wrap_agent_for_testing` collects all `Message` objects sent by the agent. Assert their `payload`, `format`, `recipient_list`, `in_response_to` field, etc.

### Mocking External Calls with `unittest.mock.patch`

If an agent makes direct external calls that are not managed via the `dependency_map` (e.g., using a globally imported library or a method on an unmanaged object), you can use Python's standard `unittest.mock.patch`:

```python
from unittest.mock import patch

# Inside your test function or class:
# @patch('my_agent_module.some_external_library.some_function')
# def test_agent_with_patched_call(mock_some_function, my_agent_test_setup):
#     agent_uut, captured_messages, id_generator = my_agent_test_setup
#     mock_some_function.return_value = "mocked_external_data"
#     
#     # ... create input message and call agent_uut._on_message(...) ...
#     
#     mock_some_function.assert_called_once_with(...)
#     # ... assert on captured_messages ...
```

### Testing Asynchronous Handlers

If your agent's `@processor` methods are `async def`:
-   The test function itself might need to be `async` (e.g., using `pytest-asyncio` and decorating the test with `@pytest.mark.asyncio`).
-   The `Agent`'s `_on_message` method and the `@agent.processor` decorator handle the execution of the async handler correctly.
-   If your assertions depend on the completion of asynchronous tasks that the handler might have initiated (e.g., messages sent after an `await` within the handler, or background tasks), you may need to use `await asyncio.sleep()` in your test to allow these operations time to complete before making assertions on the `captured_messages` list or other side effects. The Playwright agent tests demonstrate this pattern by looping with `await asyncio.sleep()` while checking the `results` list.

```python
# Conceptual snippet for testing an async handler
# @pytest.mark.asyncio
# async def test_async_agent_handler(my_async_agent_test_setup):
#     agent_uut, captured_messages, id_generator = my_async_agent_test_setup
#     # ... prepare incoming_message ...
#     agent_uut._on_message(incoming_message) # This will schedule the async handler

#     # Allow time for async operations within the handler to complete
#     await asyncio.sleep(0.1) 

#     # ... assertions on captured_messages ...
```

### General Testing Guidelines:
-   **Focus**: Test the specific logic within your agent's handlers and fixtures.
-   **Isolation**: Use dependency injection (via `wrap_agent_for_testing` and `DependencySpec`) and standard mocking techniques (like `unittest.mock.patch`) to isolate your agent from external systems for unit tests.
-   **Variety**: Test with different valid and invalid input message payloads and formats to ensure robustness.
-   **Error Conditions**: Simulate errors from dependencies (e.g., make mock services raise exceptions or return error indicators) and verify your agent's error handling logic.
-   **State Changes**: If your agent is stateful, assert that its internal state is updated correctly after message processing. For persistent state, you might need more integrated tests involving a test `StateManager`.
-   **Agent-to-Agent Interactions**: For testing how multiple agents interact within a workflow, consider setting up a minimal test `Guild` (e.g., using `GuildBuilder().launch(add_probe=True)` or by manually adding a `ProbeAgent`) to capture messages on relevant topics or observe interactions.

## Agent Mixins: Behind-the-Scenes Support

When you define an agent class, the `AgentMetaclass` automatically incorporates several default "mixin" classes into its structure. These mixins operate largely behind the scenes, providing your agent with essential cross-cutting functionalities without requiring explicit code in your agent logic.

The primary default mixins include:

-   **`StateRefresherMixin`**: This is crucial for stateful agents. It listens for system messages (like `StateFetchResponse` and `StateUpdateResponse`) from the `StateManager` and ensures that the agent's local cached copies of its own state (`self._state`) and the guild's state (`self._guild_state`) are kept synchronized with the authoritative state. This allows you to access reasonably up-to-date state within your agent without manually fetching it on every message.

    This mixin provides helpful methods for state management that you can safely use in your handlers:
    ```python
    # Get state from the state manager
    self.request_state(ctx)  # Request agent's own state 
    self.request_guild_state(ctx)  # Request guild state
    
    # Update state persistently
    self.update_state(
        ctx,
        update_format=StateUpdateFormat.MERGE_DICT,  # or REPLACE_DICT, JMESPATH_UPDATE
        update={"counter": self.counter}  # New state values
    )
    
    self.update_guild_state(
        ctx,
        update_format=StateUpdateFormat.MERGE_DICT,
        update={"last_active_agent": self.id}
    )
    ```

-   **`HealthMixin`**: This mixin provides a basic health check capability. It defines a handler for a system "ping" message (`Heartbeat`), allowing the execution environment or guild management services to verify that the agent is alive and responsive. The default implementation responds with `HeartbeatResponse` and status "OK".

-   **`TelemetryMixin`**: This mixin integrates the agent with the broader observability infrastructure. It helps in propagating tracing contexts across messages and emitting standard metrics, which are invaluable for monitoring and debugging distributed multi-agent interactions. It automatically adds tracing information to outgoing messages and captures spans for message processing.

**Interaction and Customization:**

For most agent development, you don't need to interact directly with these mixins or even be explicitly aware of their detailed implementation. They are designed to provide foundational capabilities transparently.

However, if you are an advanced user looking to deeply customize these core behaviors (e.g., changing how state is refreshed or implementing a very custom health check), you would then need to understand the specific mixin's interface and potentially override its methods or provide alternative implementations. For such advanced scenarios, referring to the source code of these mixins (typically found in `rustic_ai.core.guild.agent_ext.mixins.*`) would be necessary.

## Advanced Topics

In this section, we cover more advanced topics related to agent development and usage.

### Custom Mixins

You can create your own mixins and let the AgentMetaclass auto-inject them. To do this:

1. Define your mixin class with functionality you want to add to agents
2. Add your mixin to the `DEFAULT_MIXINS` list in a custom metaclass extending `AgentMetaclass`
3. Use your custom metaclass when defining agent classes

### Dynamic Agent Deployment

The `GuildManagerAgent` provides capabilities for dynamic agent deployment:

- Hot-reloading agents with updated implementation or configuration
- Blue-green deployment strategies for zero-downtime updates
- Dynamic scaling by adding/removing agent instances

### Performance Considerations

For high-performance agent systems:

- Message priority control using the `Priority` enum
- Message batching for reducing overhead
- Efficient state management strategies for agents with large state
- Gemstone ID sharding for distributed systems

The `@agent.processor` decorator also supports asynchronous functions with `async def`. The framework will automatically detect and properly schedule these handlers:

```python
from aiohttp import ClientSession

class AsyncAgent(Agent[BaseAgentProps]):
    @agent.processor(clz=SearchQuery)
    async def search_web(self, ctx: ProcessContext[SearchQuery]):
        query = ctx.payload.query
        
        # Perform asynchronous operations
        async with ClientSession() as session:
            async with session.get(f"https://api.example.com/search?q={query}") as response:
                result = await response.json()
                
        # Process results and respond
        ctx.send(SearchResult(results=result["items"]))
```

When an async handler is invoked:
1. The framework detects it's an async function via `inspect.iscoroutinefunction()`
2. The `ProcessorHelper.run_coroutine()` method handles scheduling:
   - If in an already running event loop, it creates a new task
   - Otherwise, it calls `asyncio.run()` to run the coroutine to completion

This allows your agent to perform non-blocking I/O operations like network requests or database queries without blocking the entire agent/guild.

### Asynchronous Handlers

The `@agent.processor` decorator also supports asynchronous functions with `async def`. The framework will automatically detect and properly schedule these handlers:

```python
from aiohttp import ClientSession

class AsyncAgent(Agent[BaseAgentProps]):
    @agent.processor(clz=SearchQuery)
    async def search_web(self, ctx: ProcessContext[SearchQuery]):
        query = ctx.payload.query
        
        # Perform asynchronous operations
        async with ClientSession() as session:
            async with session.get(f"https://api.example.com/search?q={query}") as response:
                result = await response.json()
                
        # Process results and respond
        ctx.send(SearchResult(results=result["items"]))
```

When an async handler is invoked:
1. The framework detects it's an async function via `inspect.iscoroutinefunction()`
2. The `ProcessorHelper.run_coroutine()` method handles scheduling:
   - If in an already running event loop, it creates a new task
   - Otherwise, it calls `asyncio.run()` to run the coroutine to completion

This allows your agent to perform non-blocking I/O operations like network requests or database queries without blocking the entire agent/guild.

-   **`clz`**: Specifies the expected Pydantic model for the message payload. If the incoming message's `format` matches the qualified name of this model, the payload is automatically parsed and validated into an instance of this model. Use `JsonDict` to receive the payload as a raw dictionary without parsing.