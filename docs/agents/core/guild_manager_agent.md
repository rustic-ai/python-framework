# GuildManagerAgent

The `GuildManagerAgent` is a system agent responsible for managing guild-level operations, agent lifecycle management, and guild state coordination.

## Purpose

This agent acts as a central coordinator for a RusticAI guild, providing administrative functionality for managing agents, monitoring guild health, and handling system-level operations.

## When to Use

The `GuildManagerAgent` is automatically added to every guild by default and should not typically be manually added. It's used internally by the guild system to:

- Manage agent lifecycle (creation, deletion)
- Maintain guild-level state
- Respond to system events
- Monitor guild health
- Provide guild introspection capabilities

## Configuration

The `GuildManagerAgent` is configured through the `GuildManagerAgentProps` class, which has these properties:

```python
class GuildManagerAgentProps(BaseAgentProps):
    guild_id: str  # ID of the guild this agent manages
    enable_agent_management: bool = True  # Whether agent lifecycle management is enabled
    auto_restart_agents: bool = False  # Whether to auto-restart failed agents
    health_check_interval: Optional[int] = None  # Seconds between health checks
```

## Message Types

### Input Messages

#### UserAgentCreationRequest

A request to create a new user agent:

```python
class UserAgentCreationRequest(BaseModel):
    user_id: str  # ID of the user to create an agent for
    default_target: Optional[str] = None  # Default target agent for user messages
```

#### GuildStateRequest

A request for the current state of the guild:

```python
class GuildStateRequest(BaseModel):
    include_agents: bool = True  # Whether to include agent information
    include_topics: bool = True  # Whether to include topic information
```

#### AgentLifecycleRequest

A request to manage agent lifecycle:

```python
class AgentLifecycleRequest(BaseModel):
    operation: AgentLifecycleOperation  # Operation to perform (CREATE, DELETE, RESTART)
    agent_spec: Optional[AgentSpec] = None  # Agent specification for creation
    agent_id: Optional[str] = None  # Agent ID for operations on existing agents
```

### Output Messages

#### UserAgentCreationResponse

Response to a user agent creation request:

```python
class UserAgentCreationResponse(BaseModel):
    status: ResponseStatus  # Status of the operation
    user_id: str  # ID of the user
    agent_id: Optional[str] = None  # ID of the created agent
    message: Optional[str] = None  # Additional information
```

#### GuildStateResponse

Response with guild state information:

```python
class GuildStateResponse(BaseModel):
    guild_id: str  # ID of the guild
    agents: Optional[List[AgentInfo]] = None  # Information about guild agents
    topics: Optional[List[str]] = None  # Topics in the guild
```

#### AgentLifecycleResponse

Response to an agent lifecycle request:

```python
class AgentLifecycleResponse(BaseModel):
    operation: AgentLifecycleOperation  # The operation that was performed
    status: ResponseStatus  # Status of the operation
    agent_id: Optional[str] = None  # ID of the affected agent
    message: Optional[str] = None  # Additional information
```

## Behavior

### Agent Management

1. The agent receives agent lifecycle requests (create, delete, restart)
2. It validates the request against guild policies
3. It performs the requested operation
4. It returns a response indicating success or failure

### User Agent Creation

1. The agent receives a request to create a user proxy agent
2. It generates a unique ID for the new agent
3. It creates and launches a UserProxyAgent with the specified parameters
4. It returns the ID of the created agent

### Guild State Reporting

1. The agent receives a guild state request
2. It collects information about the guild's agents and topics
3. It returns the compiled information in a structured format

### Health Monitoring

1. Periodically (if configured), the agent performs health checks on all agents
2. Agents that fail health checks may be restarted (if auto_restart is enabled)
3. Health status is published to the guild

## Sample Usage

Since the `GuildManagerAgent` is automatically included in guilds, you typically interact with it through messages:

```python
from rustic_ai.core.agents.system.models import UserAgentCreationRequest

# Create a request to create a user proxy agent
request = UserAgentCreationRequest(
    user_id="user-123",
    default_target="llm_agent"
)

# Send to the guild manager agent
client.publish(
    "default_topic", 
    request, 
    recipient=GuildTopics.GUILD_MANAGER
)
```

## Customizing the Guild Manager

If you need to customize the GuildManagerAgent, you can replace the default instance when creating a guild:

```python
from rustic_ai.core.guild.builders import AgentBuilder, GuildBuilder
from rustic_ai.core.agents.system.guild_manager_agent import GuildManagerAgent, GuildManagerAgentProps

# Create a custom guild manager specification
custom_manager_spec = (
    AgentBuilder(GuildManagerAgent)
    .set_id(GuildTopics.GUILD_MANAGER)
    .set_name("Custom Guild Manager")
    .set_description("Guild manager with custom configuration")
    .set_properties(
        GuildManagerAgentProps(
            guild_id="my_guild",
            enable_agent_management=True,
            auto_restart_agents=True,
            health_check_interval=60  # Check health every minute
        )
    )
    .build_spec()
)

# Create a guild with the custom manager
guild = (
    GuildBuilder("my_guild", "My Guild", "A guild with custom manager")
    .set_guild_manager_spec(custom_manager_spec)
    .launch()
)
```

## Security Considerations

The `GuildManagerAgent` has privileged access to guild operations. In production environments:

1. Ensure that access to the guild manager is properly authenticated
2. Restrict which agents can send lifecycle management requests
3. Consider disabling agent management if not needed
4. Monitor guild manager activity for security events

## Notes and Limitations

- The GuildManagerAgent is essential for guild operation and should not be removed
- Direct agent manipulation outside the guild manager may cause inconsistencies
- For production systems, consider how agent lifecycles intersect with your application's security model
- The default GuildManagerAgent does not persist agent configurations across restarts 