# Guilds

A Guild is a logical grouping of agents in RusticAI. It acts as a collaborative environment, managing the lifecycle, execution, and coordination of its member agents. Guilds provide a shared context, including common dependencies, message routing infrastructure, and state management facilities.

## Purpose
- **Organize Agents**: Group agents into functional units for specific tasks or workflows.
- **Lifecycle Management**: Control the registration, launching, execution, and removal of agents.
- **Coordinated Execution**: Define how agents run, leveraging different [Execution Engines](execution.md).
- **Message Orchestration**: Define sophisticated [Messaging](messaging.md) flows between agents using routes.
- **Shared Resources**: Provide shared [Dependencies](dependencies.md) and [State](state_management.md) for member agents.

## Guild Specification (`GuildSpec`)

A `GuildSpec` is a declarative blueprint that defines the structure and behavior of a Guild. It's typically defined in a YAML or JSON file, or constructed programmatically using the `GuildBuilder`.

Key fields in a `GuildSpec`:

-   `id` (str): A unique identifier for the Guild. Defaults to a `shortuuid`.
-   `name` (str): A human-readable name for the Guild (1-64 characters).
-   `description` (str): A detailed description of the Guild's purpose.
-   `properties` (Dict[str, Any]): A dictionary for guild-specific configurations. This often includes:
    -   `execution_engine` (str): The fully qualified class name of the [Execution Engine](execution.md) to use (e.g., `"rustic_ai.core.guild.execution.sync.sync_exec_engine.SyncExecutionEngine"`).
    -   `messaging` (Dict): Configuration for the [Messaging](messaging.md) system, including `backend_module`, `backend_class`, and `backend_config`.
    -   `client_type` (str): The default `Client` class for agents.
    -   `client_properties` (Dict): Default properties for agent clients.
-   `agents` (List[AgentSpec]): A list of [Agent Specifications (`AgentSpec`)](agents.md) that define the agents belonging to this guild.
-   `dependency_map` (Dict[str, DependencySpec]): A mapping of dependency keys to [Dependency Specifications (`DependencySpec`)](dependencies.md) available to all agents in the guild. These can be overridden at the agent level.
-   `routes` (RoutingSlip): Defines the message routing rules within the guild. This is a powerful mechanism for orchestrating agent interactions.

### Example `GuildSpec` (Conceptual JSON)

```json
{
    "id": "research-guild-01",
    "name": "Research Guild",
    "description": "A guild to research topics using multiple agents.",
    "properties": {
        "execution_engine": "rustic_ai.core.guild.execution.sync.sync_exec_engine.SyncExecutionEngine",
        "messaging": {
            "backend_module": "rustic_ai.core.messaging.backend",
            "backend_class": "InMemoryMessagingBackend",
            "backend_config": {}
        }
    },
    "agents": [
        // ... AgentSpec definitions here ... (see Agents section below)
    ],
    "dependency_map": {
        // ... Guild-level dependency definitions here ...
    },
    "routes": {
        // ... RoutingSlip definition here ... (see Routes section below)
    }
}
```

## Agents within a Guild

The `agents` field in `GuildSpec` is a list of `AgentSpec` objects. Each `AgentSpec` defines an individual agent within the guild. Key `AgentSpec` fields include:

-   `id` (str): Unique ID for the agent.
-   `name` (str): Human-readable name.
-   `description` (str): Agent's purpose.
-   `class_name` (str): Fully qualified class name of the agent (e.g., `"rustic_ai.agents.llm.litellm.litellm_agent.LiteLLMAgent"`).
-   `additional_topics` (List[str]): Specific message topics the agent subscribes to.
-   `properties` (Dict[str, Any]): Agent-specific configuration (e.g., LLM model, API keys).
-   `listen_to_default_topic` (bool): Whether the agent listens to the guild's default topic.
-   `dependency_map` (Dict[str, DependencySpec]): Agent-specific dependencies, which can override guild-level ones.

Refer to the [Agents documentation](agents.md) for a complete overview of `AgentSpec`.

### Example Agent in a Guild:

```json
// Inside GuildSpec.agents list
{
    "id": "research_manager",
    "name": "Research Manager",
    "description": "A manager for the research process",
    "class_name": "rustic_ai.agents.laira.research_manager.ResearchManager",
    "properties": {
        "llm_model": "gpt-4o"
    },
    "listen_to_default_topic": true
}
```

## Guild-Level Dependencies (`dependency_map`)

The `dependency_map` in `GuildSpec` allows you to define dependencies that are available to all agents within the guild. This is useful for sharing resources like database connections, API clients, or configuration objects.

-   Each key in the map is a name by which agents can request the dependency.
-   The value is a `DependencySpec` that defines how to resolve and instantiate the dependency.
-   Agent-specific `dependency_map` entries can override guild-level ones with the same key.

See [Dependencies](dependencies.md) for more details on how dependency injection works.

## Message Routing (`routes`)

The `routes` field in `GuildSpec` defines a `RoutingSlip`. A RoutingSlip is a list of `RoutingRule` objects (often called "steps") that dictate how messages are processed and forwarded within the guild. This enables complex workflows and orchestrations.

### `RoutingSlip` Structure:

A `RoutingSlip` primarily contains a list of `steps`, where each step is a `RoutingRule`.

```json
// GuildSpec.routes
"routes": {
    "steps": [
        // ... RoutingRule definitions here ...
    ]
}
```

### `RoutingRule` (Step) Structure:

Each `RoutingRule` defines how a message, upon matching certain criteria, should be transformed and sent to a destination. Key fields include:

-   **`agent`** (AgentTag) or **`agent_type`** (str):
    -   `agent`: Specifies a particular agent instance by its `id` or `name` (e.g., `{"name": "echo_agent_1"}`). This rule applies to messages *produced by* this specific agent.
    -   `agent_type`: Specifies an agent class (e.g., `"rustic_ai.agents.utils.user_proxy_agent.UserProxyAgent"`). This rule applies to messages *produced by any agent of* this type.
-   **`method_name`** (str, optional): The name of the method on the source agent that produced the message. If specified, the rule only applies to messages from this method.
-   **`origin_filter`** (Dict, optional): Further filters messages based on their origin:
    -   `origin_sender` (AgentTag): The original sender of the message.
    -   `origin_topic` (str): The topic the original message was on.
    -   `origin_message_format` (str): The Pydantic model type of the original message.
-   **`message_format`** (str, optional): The Pydantic model type (fully qualified name) of the incoming message payload this rule should match (e.g., `"rustic_ai.ui_protocol.types.TextFormat"`).
-   **`transformer`** (Dict, optional): Defines how to transform the incoming message payload before sending it to the destination.
    -   `expression` (str): A JSONata expression or a custom transformation logic to apply to the incoming message payload.
    -   `output_format` (str): The Pydantic model type (fully qualified name) of the transformed payload (e.g., `"rustic_ai.agents.laira.research_manager.UserQuery"`).
    Example: `{"expression": "{\"query\": text}", "output_format": "rustic_ai.agents.laira.research_manager.UserQuery"}`
-   **`destination`** (Dict, optional): Specifies where the (transformed) message should be sent. If `null`, the message is typically sent back to the original sender or follows routing slip logic from the incoming message.
    -   `topics` (str | List[str]): The topic(s) to publish the message to (e.g., `"echo_topic"`, `"user_message_broadcast"`).
    -   `recipient_list` (List[AgentTag]): A list of specific agents to send the message to.
    -   `priority` (int, optional): Message priority.
-   **`route_times`** (int): How many times this rule can be applied. `1` means it applies once. `-1` means it can apply indefinitely for messages matching its criteria.
-   **`mark_forwarded`** (bool, default: `false`): If `true`, marks the message as forwarded, which can influence subsequent routing decisions.

### Example Route Step:

This rule takes a `TextFormat` message from a `UserProxyAgent`, transforms its `text` field into a `UserQuery`'s `query` field, and sends it to the `default_topic`.

```json
// Inside RoutingSlip.steps list
{
    "agent_type": "rustic_ai.agents.utils.user_proxy_agent.UserProxyAgent",
    "method_name": "unwrap_and_forward_message", // From UserProxyAgent
    "message_format": "rustic_ai.ui_protocol.types.TextFormat",
    "transformer": {
        "expression": "{\"query\": text}",
        "output_format": "rustic_ai.agents.laira.research_manager.UserQuery"
    },
    "destination": {
        "topics": "default_topic"
    },
    "route_times": 1
}
```

Routing slips enable powerful patterns:
-   **Sequential Processing**: Message passed from agent A -> B -> C.
-   **Fan-out/Fan-in**: One message triggers multiple agents, results are aggregated.
-   **Content-Based Routing**: Message content dictates the next recipient.
-   **Transformations**: Messages are reshaped between agents to match differing interfaces.

## Guild Lifecycle & Management

Managing the lifecycle of a Guild involves defining its structure, instantiating it, launching its agents, facilitating their interactions, and eventually shutting it down. RusticAI provides different mechanisms for bringing a Guild to life, suited for development versus production environments.

1. **Definition (`GuildSpec`)**: The blueprint for a Guild is its `GuildSpec`. This can be defined in a YAML/JSON file or constructed programmatically using `GuildBuilder` and `AgentBuilder`.

```python
    # Basic programmatic GuildSpec construction
    from rustic_ai.core.guild.builders import GuildBuilder, AgentBuilder, RouteBuilder
    from rustic_ai.core.guild.dsl import GuildSpec, AgentSpec, RoutingSlip, RoutingRule
    from rustic_ai.core.messaging.core.message import AgentTag
    # Assuming EchoAgent and UserProxyAgent are defined/imported
    # from rustic_ai.core.agents.testutils import EchoAgent
    # from rustic_ai.core.agents.utils import UserProxyAgent 

    # Define an AgentSpec
    echo_agent_spec = AgentBuilder(EchoAgent) \
        .set_name("echo_agent_1") \
        .set_description("Echoes input") \
        .add_additional_topic("echo_topic") \
        .listen_to_default_topic(False) \
        .build_spec()

    # Define a Route
    route1 = RouteBuilder(from_agent=UserProxyAgent) \
        .from_method("unwrap_and_forward_message") \
        .on_message_format("rustic_ai.ui_protocol.types.TextFormat") \
        .set_destination_topics("echo_topic") \
        .set_route_times(1) \
        .build()
    
    route2 = RouteBuilder(from_agent=AgentTag(name="echo_agent_1")) \
        .set_destination_topics("user_message_broadcast") \
        .set_route_times(1) \
        .build()

    routing_slip = RoutingSlip(steps=[route1, route2])

    # Build the GuildSpec
    guild_builder = GuildBuilder(guild_name="MyDevGuild", guild_description="For local testing.") \
        .set_execution_engine("rustic_ai.core.guild.execution.sync.sync_exec_engine.SyncExecutionEngine") \
        .set_messaging(
            backend_module="rustic_ai.core.messaging.backend",
            backend_class="InMemoryMessagingBackend",
            backend_config={}
        ) \
        .add_agent_spec(echo_agent_spec) \
        .set_routes(routing_slip)
    
    guild_spec = guild_builder.build_spec()
    ```

2. **Instantiation and Launching Agents**:

There are two main approaches to instantiate a `Guild` from a `GuildSpec` and launch its agents, provided by the `GuildBuilder`:

    *   **`guild_builder.launch()` - For Development & Testing:**
        *   **How it works:** This method is a convenient way to quickly bring up an entire Guild and its agents in the current environment. 
            1. It first creates a `Guild` instance from the `GuildSpec` (a "shallow" guild without agents running).
            2. Then, it iterates through all `AgentSpec`s defined within the `GuildSpec` and calls `guild.launch_agent(agent_spec)` for each. The `guild.launch_agent()` method handles registering the agent with the guild and then uses the Guild's configured `ExecutionEngine` to start the agent.
        *   **Outcome:** A fully operational `Guild` with all its agents running.
        *   **Use Case:** Best suited for local development, running examples, and automated tests where immediate, self-contained execution is desired.
        ```python
        # Assuming guild_builder is configured as above
        # development_guild = guild_builder.launch()
        # print(f"Guild '{development_guild.name}' launched with {development_guild.get_agent_count()} agent(s).")
        # # ... interact with the guild ...
        # development_guild.shutdown()
        ```

    *   **`guild_builder.bootstrap(metastore_database_url: str)` - For Production:**
        *   **How it works:** This method is designed for more robust, production-like deployments.
            1. It also starts by creating a "shallow" `Guild` instance from the `GuildSpec`.
            2. However, instead of directly launching the agents from the `GuildSpec`, it instantiates and launches a special system agent called `GuildManagerAgent`.
            3. This `GuildManagerAgent` is configured with the original `GuildSpec` and the `metastore_database_url`.
            4. The `GuildManagerAgent` then takes on the responsibility of persisting the `GuildSpec` to the metastore and managing the lifecycle (launching, monitoring, stopping) of the user-defined agents based on this persisted specification. 
        *   **Outcome:** A `Guild` instance where the primary user-defined agents are managed by the `GuildManagerAgent`, facilitating persistence, and potentially more advanced lifecycle operations suitable for production (like distributed execution, depending on the execution engine).
        *   **Use Case:** Recommended for production or staging environments where Guilds need to be persistent, managed centrally, and potentially operate in a distributed manner.
        ```python
        # Assuming guild_builder is configured as above
        # METASTORE_URL = "sqlite:///./rusticai_metastore.db" # Example
        # production_guild = guild_builder.bootstrap(metastore_database_url=METASTORE_URL)
        # print(f"Guild '{production_guild.name}' bootstrapped. GuildManagerAgent is running.")
        # # Agents defined in guild_spec will be launched by GuildManagerAgent
        # # ... (Guild operates, likely in a separate process or managed environment) ...
        # # Shutdown would typically be managed by the environment or the GuildManagerAgent's signals
        ```

    **Important Note on `guild.launch_agent()`:** While `guild.launch_agent(agent_spec)` is the underlying method that starts an individual agent, you typically **do not call it directly** when setting up a guild from a specification. Instead, rely on `guild_builder.launch()` for development or `guild_builder.bootstrap()` for production scenarios, as these methods handle the overall setup process correctly.

3. **Interaction**: Once launched, agents within the Guild communicate via messages, with their interactions orchestrated by the Guild's defined [routes](#message-routing-routes) and [messaging system](messaging.md).

4. **Agent Management (Runtime)**: After initial launch, you might interact with the guild or its agents:
    *   Via API endpoints if the Guild is managed by a service (see [Observability & Remote Management](#observability--remote-management)).
    *   Programmatically in some scenarios (less common for bootstrapped guilds directly):
        *   `guild.remove_agent(agent_id)`: Stops and removes an agent from the guild's tracking and execution engine.
        *   `guild.get_agent(agent_id)`: Retrieves an `AgentSpec` by its ID.
        *   `guild.list_agents()`: Lists all `AgentSpec`s currently registered with the guild instance.
        *   `guild.list_all_running_agents()`: Lists `AgentSpec`s of agents the execution engine reports as running for this guild.

5. **Shutdown**:
    *   For guilds started with `guild_builder.launch()`: Call `guild.shutdown()`. This will attempt to gracefully stop all agents and release resources associated with the guild and its execution engine.
    *   For guilds started with `guild_builder.bootstrap()`: Shutdown is typically managed by the environment hosting the `GuildManagerAgent` or through signals sent to it. The `GuildManagerAgent` would then handle the graceful shutdown of the agents it manages.

## Guild Object API

Once a `Guild` object is instantiated (e.g., via `GuildBuilder().launch()` or `GuildBuilder().load()`), it provides several methods for interaction and introspection:

-   `guild.id`, `guild.name`, `guild.description`: Access basic properties.
-   `guild.register_agent(agent_spec: AgentSpec)`: Registers an agent spec with the guild. Does not run the agent.
-   `guild.launch_agent(agent_spec: AgentSpec, execution_engine: Optional[ExecutionEngine] = None)`: (As noted, primarily for internal/system use) Registers and runs an agent using the specified or guild's default execution engine.
-   `guild.remove_agent(agent_id: str)`: Stops the agent in the execution engine and removes it from the guild's internal tracking.
-   `guild.get_agent(agent_id: str) -> Optional[AgentSpec]`: Retrieves a registered agent's specification by ID.
-   `guild.get_agent_by_name(name: str) -> Optional[AgentSpec]`: Retrieves a registered agent's specification by name.
-   `guild.list_agents() -> List[AgentSpec]`: Returns a list of all registered (not necessarily running) agent specifications.
-   `guild.list_all_running_agents() -> List[AgentSpec]`: Queries the execution engine for agents it considers currently running for this guild.
-   `guild.get_agent_count() -> int`: Returns the number of registered agents.
-   `guild.to_spec() -> GuildSpec`: Converts the current state of the guild instance (including its registered agents, routes, etc.) back into a `GuildSpec` object.
-   `guild.shutdown()`: Initiates the shutdown process for the guild and its associated execution engine(s), attempting to stop all managed agents.

## Execution Engines
Guilds use execution engines to manage how agents are run. Supported modes include synchronous, multithreaded, and more (see [Execution](execution.md)). The execution engine is typically specified in the `GuildSpec.properties`.

## Observability & Remote Management
Large deployments expose a **Guild Control Plane** (HTTP/REST or gRPC) that allows operators to:

| Endpoint     | Verb   | Description                       |
|--------------|--------|-----------------------------------|
| `/agents`    | GET    | List running agents               |
| `/agents`    | POST   | Register + launch a new agent     |
| `/agents/{id}` | DELETE | Stop and remove an agent          |
| `/state`     | GET    | Dump guild-level state snapshot   |
| `/metrics`   | GET    | Prometheus scrape endpoint        |

These endpoints are backed by the same APIs shown earlier (`register_agent`, `launch_agent`, etc.) and secured via JWT bearer tokens.

## Monitoring
Guilds emit the following metrics:
*   `guild_agents_running` – Gauge labelled by `guild_id` and `agent_type`.
*   `guild_messages_total` – Counter for messages processed.
*   `guild_errors_total` – Counter for processing errors.

Integrate with Grafana dashboards for a helicopter view of the system.

## Advanced Topics
-   **Dynamic Guilds**: Guilds can be created, modified, and managed at runtime, especially when using a `GuildManagerAgent`.
-   **State Propagation**: Guild-level state changes can be broadcast or made available to agents.
-   **Cross-Guild Communication**: While guilds provide encapsulation, advanced scenarios might involve routing messages between guilds.

> See the [Agents](agents.md), [Messaging](messaging.md), [Execution](execution.md), and [Dependencies](dependencies.md) sections for more details on related components. 