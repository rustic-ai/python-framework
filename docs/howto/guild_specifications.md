# Guild Specifications

This guide explains how to create and work with Guild Specifications (GuildSpec) in RusticAI.

## What is a GuildSpec?

A `GuildSpec` is a declarative blueprint that defines the structure and behavior of a Guild. It specifies which agents are part of the guild, how they communicate, how they're executed, and what dependencies they have access to.

## Creating a GuildSpec

There are two main ways to create a `GuildSpec`:

### 1. Using the GuildBuilder API

The `GuildBuilder` provides a fluent interface for constructing guild specifications programmatically:

```python
from rustic_ai.core.guild.builders import GuildBuilder, AgentBuilder
from rustic_ai.agents.utils.user_proxy_agent import UserProxyAgent
from rustic_ai.agents.llm.litellm.litellm_agent import LiteLLMAgent

# Create a guild builder
guild_builder = GuildBuilder(guild_name="MyGuild") \
    .set_description("An example guild") \
    .set_execution_engine("rustic_ai.core.guild.execution.sync.sync_exec_engine.SyncExecutionEngine") \
    .set_messaging(
        backend_module="rustic_ai.core.messaging.backend",
        backend_class="InMemoryMessagingBackend",
        backend_config={}
    )

# Add agent specifications
user_agent_spec = AgentBuilder(UserProxyAgent) \
    .set_id("user_agent") \
    .set_name("User Interface") \
    .set_description("Handles user interactions") \
    .build_spec()

llm_agent_spec = AgentBuilder(LiteLLMAgent) \
    .set_id("llm_agent") \
    .set_name("Language Model") \
    .set_description("Processes language tasks") \
    .set_properties({
        "model": "gpt-3.5-turbo",
        "temperature": 0.7
    }) \
    .build_spec()

# Add the agents to the guild
guild_builder.add_agent_spec(user_agent_spec)
guild_builder.add_agent_spec(llm_agent_spec)

# Build the GuildSpec
guild_spec = guild_builder.build_spec()
```

### 2. Using YAML or JSON Configuration

You can also define your guild specification in a YAML or JSON file:

```yaml
id: "my_guild_01"
name: "MyGuild"
description: "An example guild"
properties:
  execution_engine: "rustic_ai.core.guild.execution.sync.sync_exec_engine.SyncExecutionEngine"
  messaging:
    backend_module: "rustic_ai.core.messaging.backend"
    backend_class: "InMemoryMessagingBackend"
    backend_config: {}
agents:
  - id: "user_agent"
    name: "User Interface"
    description: "Handles user interactions"
    class_name: "rustic_ai.agents.utils.user_proxy_agent.UserProxyAgent"
    properties: {}
  - id: "llm_agent"
    name: "Language Model"
    description: "Processes language tasks"
    class_name: "rustic_ai.agents.llm.litellm.litellm_agent.LiteLLMAgent"
    properties:
      model: "gpt-3.5-turbo"
      temperature: 0.7
```

Then load it in your code:

```python
from rustic_ai.core.guild.dsl import GuildSpec
import yaml

# Load from YAML file
with open("my_guild.yaml", "r") as f:
    guild_data = yaml.safe_load(f)

# Parse into a GuildSpec
guild_spec = GuildSpec.parse_obj(guild_data)
```

## Key Components of a GuildSpec

A complete `GuildSpec` includes:

- **Basic Information**: `id`, `name`, `description`
- **Properties**: Configures execution engines, messaging systems, etc.
- **Agents**: List of `AgentSpec` objects defining the member agents
- **Dependencies**: Resources available to agents via dependency injection
- **Routes**: Message routing rules for agent communication

## Instantiating a Guild from a GuildSpec

Once you have a `GuildSpec`, you can instantiate and launch a guild:

```python
# For development and testing
guild = guild_builder.launch()

# For production (with persistence)
guild = guild_builder.bootstrap(metastore_database_url="sqlite:///guild_store.db")
```

## Persisting and Loading GuildSpecs

You can save and load guild specifications:

```python
# Save to JSON
guild_spec_json = guild_spec.json(indent=2)
with open("guild_spec.json", "w") as f:
    f.write(guild_spec_json)

# Load from JSON
from rustic_ai.core.guild.dsl import GuildSpec
import json

with open("guild_spec.json", "r") as f:
    loaded_spec_data = json.load(f)

loaded_guild_spec = GuildSpec.parse_obj(loaded_spec_data)
```

## Best Practices

1. **Modular Design**: Break complex guilds into logical groups of agents
2. **Clear Naming**: Use descriptive names for guilds and agents
3. **Version Control**: Store guild specifications in version control
4. **Environment Variables**: Use environment variables for sensitive configuration
5. **Documentation**: Include clear descriptions for guilds and agents

For more detailed information about guilds, see the [Guilds](../core/guilds.md) core documentation. 