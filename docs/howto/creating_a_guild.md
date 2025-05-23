# Creating a Guild with Multiple Agents

This guide will walk you through creating a guild with multiple agents that interact with each other using RusticAI. In RusticAI, a Guild serves as a container and coordination mechanism for a collection of agents.

## Prerequisites

Before you begin, make sure you have:
- Installed RusticAI and its dependencies
- Basic understanding of agents (see [Creating Your First Agent](creating_your_first_agent.md))
- Familiarity with RusticAI [core concepts](../core/index.md)

## Understanding Guilds

A Guild in RusticAI:
- Serves as a container for multiple agents
- Manages communication between agents
- Handles message routing
- Provides shared resources and dependencies
- Manages the lifecycle of agents

## Step 1: Design Your Agent System

Before coding, it's helpful to plan your multi-agent system:

1. **Identify the agents** needed and their responsibilities
2. **Define message models** for communication between agents
3. **Plan message flows** and routing between agents

For this example, we'll create a simple system with:
- A `GreeterAgent` that responds to greeting requests
- A `ProcessorAgent` that processes data
- A `ProbeAgent` for monitoring message traffic

## Step 2: Define Message Models

Let's define our message models:

```python
from pydantic import BaseModel
from typing import Dict, Any, List

class GreetRequest(BaseModel):
    """A request for a greeting."""
    name: str

class GreetResponse(BaseModel):
    """A response with a greeting."""
    greeting: str

class ProcessRequest(BaseModel):
    """A request to process some data."""
    data: Dict[str, Any]
    operation: str

class ProcessResponse(BaseModel):
    """A response with processed data."""
    result: Dict[str, Any]
    processing_time: float
```

## Step 3: Implement Your Agents

Now, let's implement our agents:

### Greeter Agent

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.dsl import AgentSpec, BaseAgentProps
import time

class GreeterAgent(Agent[BaseAgentProps]):
    """An agent that responds to greeting requests."""

    def __init__(self, agent_spec: AgentSpec[BaseAgentProps]):
        super().__init__(agent_spec)
        print(f"GreeterAgent initialized with ID: {self.id}")

    @agent.processor(clz=GreetRequest)
    def greet(self, ctx: agent.ProcessContext[GreetRequest]):
        """Process a greeting request and respond with a greeting."""
        name = ctx.payload.name
        print(f"[{self.name}] Received greeting request for: {name}")
        
        # Create and send a response
        response = GreetResponse(greeting=f"Hello, {name}!")
        ctx.send(response)
        print(f"[{self.name}] Sent response: {response.greeting}")
```

### Processor Agent

```python
class ProcessorAgent(Agent[BaseAgentProps]):
    """An agent that processes data requests."""

    def __init__(self, agent_spec: AgentSpec[BaseAgentProps]):
        super().__init__(agent_spec)
        print(f"ProcessorAgent initialized with ID: {self.id}")

    @agent.processor(clz=ProcessRequest)
    def process_data(self, ctx: agent.ProcessContext[ProcessRequest]):
        """Process a data processing request."""
        data = ctx.payload.data
        operation = ctx.payload.operation
        
        print(f"[{self.name}] Processing {operation} on data: {data}")
        
        # Simulate processing
        start_time = time.time()
        result = self._perform_operation(data, operation)
        processing_time = time.time() - start_time
        
        # Send the response
        ctx.send(ProcessResponse(
            result=result,
            processing_time=processing_time
        ))
        print(f"[{self.name}] Sent processing result. Time: {processing_time:.4f}s")
    
    def _perform_operation(self, data: Dict[str, Any], operation: str) -> Dict[str, Any]:
        """Perform an operation on the data."""
        if operation == "count":
            return {"count": len(data)}
        elif operation == "sum":
            return {"sum": sum(data.values() if isinstance(data.values(), list) else data.values())}
        elif operation == "uppercase":
            return {k: v.upper() if isinstance(v, str) else v for k, v in data.items()}
        else:
            return {"error": f"Unknown operation: {operation}"}
```

## Step 4: Create and Configure a Guild

Now, let's create a guild and add our agents to it:

```python
import asyncio
from rustic_ai.core.guild.builders import AgentBuilder, GuildBuilder
from rustic_ai.core.agents.testutils.probe_agent import ProbeAgent

async def main():
    # Create and launch a guild
    guild = GuildBuilder("demo_guild", "Demo Guild", "A demonstration guild with multiple agents") \
        .launch(add_probe=True)  # The add_probe=True adds a ProbeAgent for monitoring
    
    # Get the probe agent for monitoring messages
    probe_agent = guild.get_agent_of_type(ProbeAgent)
    print(f"Created guild with ID: {guild.id}")
    
    # Create agent specs
    greeter_agent_spec = AgentBuilder(GreeterAgent) \
        .set_name("Greeter") \
        .set_description("An agent that responds to greeting requests") \
        .build_spec()
    
    processor_agent_spec = AgentBuilder(ProcessorAgent) \
        .set_name("Processor") \
        .set_description("An agent that processes data requests") \
        .build_spec()
    
    # Launch the agents
    guild.launch_agent(greeter_agent_spec)
    guild.launch_agent(processor_agent_spec)
    
    print("\nAgents in the guild:")
    for agent_spec in guild.list_agents():
        print(f"- {agent_spec.name} (ID: {agent_spec.id}, Type: {agent_spec.class_name})")
    
    # Test the agents
    print("\nTesting the Greeter Agent...")
    probe_agent.publish("default_topic", GreetRequest(name="World"))
    
    print("\nTesting the Processor Agent...")
    probe_agent.publish("default_topic", ProcessRequest(
        data={"a": 1, "b": 2, "c": 3},
        operation="sum"
    ))
    
    # Wait for messages to be processed
    await asyncio.sleep(1)
    
    # Print all messages captured by the probe
    messages = probe_agent.get_messages()
    print(f"\nCaptured {len(messages)} messages:")
    for i, msg in enumerate(messages, 1):
        print(f"\nMessage {i} from {msg.sender.name}:")
        print(f"Format: {msg.format}")
        print(f"Payload: {msg.payload}")
    
    # Shutdown the guild
    guild.shutdown()
    print("\nGuild shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 5: Adding Custom Routing

You can customize message routing within your guild to create more complex interaction patterns:

```python
# Create a guild with custom routes
guild = GuildBuilder("demo_guild", "Demo Guild", "A demonstration guild with multiple agents")

# Define a route
route = RouteBuilder() \
    .add_recipients(AgentTag("greeter_agent")) \
    .build()

# Add a custom route for greeting messages
guild.add_route(route)
```

## Step 6: Using Guild Specifications

For more complex guilds, it's often easier to define them in a JSON specification file:

```json
{
  "guild_id": "demo_guild",
  "name": "Demo Guild",
  "description": "A demonstration guild with multiple agents",
  "agents": [
    {
      "id": "greeter_agent",
      "name": "Greeter Agent",
      "description": "An agent that handles greeting requests",
      "class_name": "path.to.GreeterAgent",
      "additional_topics": [],
      "properties": {},
      "listen_to_default_topic": true
    },
    {
      "id": "processor_agent",
      "name": "Processor Agent",
      "description": "An agent that processes data",
      "class_name": "path.to.ProcessorAgent",
      "additional_topics": [],
      "properties": {},
      "listen_to_default_topic": true
    }
  ],
  "default_topic": "default_topic",
  "routes": [
    {
      "route_id": "greeting_route",
      "match_expression": "$exists(payload.name)",
      "to_recipient": "greeter_agent",
      "mark_forwarded": true,
      "description": "Route greeting messages to the greeter agent"
    },
    {
      "route_id": "processing_route",
      "match_expression": "$exists(payload.operation)",
      "to_recipient": "processor_agent",
      "mark_forwarded": true,
      "description": "Route processing messages to the processor agent"
    }
  ]
}
```

You can load this specification using:

```python
from rustic_ai.core.guild.builders import load_guild_from_spec

# Load the guild specification from a file
with open("demo_guild_spec.json", "r") as f:
    guild_spec_json = f.read()

# Create and launch the guild
guild = load_guild_from_spec(guild_spec_json).launch()
```

## Advanced Guild Features

### Shared Dependencies

You can define dependencies at the guild level that are shared by all agents:

```python
from rustic_ai.core.guild.dsl import DependencySpec

# Create a guild with shared dependencies
guild = GuildBuilder("demo_guild", "Demo Guild", "A demonstration guild")

# Add a shared dependency
guild.add_dependency(
    key="database",
    dependency=DependencySpec(
        class_name="path.to.DatabaseResolver",
        properties={"connection_string": "sqlite:///guild.db"}
    )
)

# Launch the guild
guild = guild.launch()
```

### Custom Topics

You can create custom topics for message routing:

```python
# Create agents with custom topics
greeter_agent_spec = AgentBuilder(GreeterAgent) \
    .set_name("Greeter") \
    .set_description("An agent that responds to greeting requests") \
    .set_additional_topics(["greeting_topic"]) \
    .build_spec()

# Create a route to the custom topic
guild.add_route(
    route_id="greeting_route",
    match_expression="$exists(payload.name)",
    to_topic="greeting_topic",
    description="Route greeting messages to the greeting topic"
)
```

## Next Steps

Now that you've created a guild with multiple agents, you might want to:

- Learn about [state management](state_management.md) for sharing state between agents
- Explore [dependency injection](dependency_injection.md) for more complex agent configurations
- Understand how to [debug and test](testing_agents.md) multi-agent systems

For a complete example, see the **Hello World Guild** - `examples/hello_world/hello_world_guild.py` in the examples directory. 