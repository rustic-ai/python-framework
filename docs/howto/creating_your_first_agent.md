# Creating Your First Agent

This guide will walk you through creating your first agent using the RusticAI framework. Agents are the fundamental building blocks in RusticAI that encapsulate logic, maintain state, and communicate with other agents.

## Prerequisites

Before you begin, make sure you have:
- Installed RusticAI and its dependencies
- Basic understanding of Python
- Familiarity with RusticAI [core concepts](../core/index.md)

## Step 1: Define Message Models

First, let's define the message models our agent will process. We'll create a simple greeting agent that responds to name-based greeting requests.

```python
from pydantic import BaseModel

class GreetRequest(BaseModel):
    """A simple model for greeting requests."""
    name: str

class GreetResponse(BaseModel):
    """A model for greeting responses."""
    greeting: str
```

## Step 2: Create Your Agent Class

Next, create a class that inherits from `Agent` and implements the message handling logic:

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.dsl import AgentSpec, BaseAgentProps

class MyGreeterAgent(Agent[BaseAgentProps]):
    """A simple agent that responds to greeting requests."""

    def __init__(self, agent_spec: AgentSpec):
        super().__init__(agent_spec)
        print(f"Greeter Agent initialized with ID: {self.id}")

    @agent.processor(clz=GreetRequest)
    def greet(self, ctx: agent.ProcessContext[GreetRequest]):
        """Process a greeting request and respond with a greeting."""
        # Extract the name from the request
        name = ctx.payload.name
        print(f"Received greeting request for: {name}")
        
        # Create and send a response
        response = GreetResponse(greeting=f"Hello, {name}!")
        ctx.send(response)
        print(f"Sent response: {response.greeting}")
```

Let's break down what's happening here:

1. Our agent inherits from `Agent[BaseAgentProps]` - this uses the most basic agent properties.
2. The `__init__` method initializes the agent with the provided `AgentSpec`.
3. The `@agent.processor(clz=GreetRequest)` decorator registers our `greet` method as a handler for `GreetRequest` messages.
4. Inside the handler, we:
   - Extract the name from the request payload
   - Create a `GreetResponse` object
   - Send the response using `ctx.send()`

## Step 3: Creating an Agent Specification

To use your agent, you need to create an `AgentSpec` that defines its configuration:

```python
from rustic_ai.core.guild.builders import AgentBuilder

# Create the agent specification
greeter_spec = AgentBuilder(MyGreeterAgent) \
    .set_name("MyGreeter") \
    .set_description("A friendly greeter agent.") \
    .build_spec()
```

## Step 4: Testing Your Agent

You can test your agent directly without launching a full guild:

```python
from rustic_ai.core.messaging.core.message import Message, AgentTag
from rustic_ai.core.utils.priority import Priority
from rustic_ai.core.utils.gemstone_id import GemstoneGenerator

# Create a generator for message IDs
gemstone_gen = GemstoneGenerator(machine_id=1)

# Create the agent instance
greeter_agent = MyGreeterAgent(greeter_spec)

# Create a test message
message = Message(
    id_obj=gemstone_gen.get_id(Priority.NORMAL),
    topics=["test_topic"],
    sender=AgentTag(id="test_sender", name="Test Sender"),
    payload=GreetRequest(name="World").model_dump(),
    format=GreetRequest.model_json_schema()["$id"],
)

# Process the message
greeter_agent._on_message(message)
```

## Step 5: Using Your Agent in a Guild

In a real application, you would typically launch your agent as part of a guild:

```python
from rustic_ai.core.guild.builders import GuildBuilder

# Create and launch a guild
guild = GuildBuilder("greeting_guild", "Greeting Guild", "A guild with a greeter agent") \
    .launch()

# Launch the agent in the guild
guild.launch_agent(greeter_spec)

# Later, you can shut down the guild
guild.shutdown()
```

## Customizing Your Agent

### Custom Properties

You can define custom properties for your agent by creating a subclass of `BaseAgentProps`:

```python
class GreeterAgentProps(BaseAgentProps):
    """Custom properties for our greeter agent."""
    default_greeting: str = "Hello"
    include_emoji: bool = True

class MyGreeterAgent(Agent[GreeterAgentProps]):
    def __init__(self, agent_spec: AgentSpec[GreeterAgentProps]):
        super().__init__(agent_spec)
        # Access props through agent_spec
        self.default_greeting = agent_spec.props.default_greeting
        self.include_emoji = agent_spec.props.include_emoji

    @agent.processor(clz=GreetRequest)
    def greet(self, ctx: agent.ProcessContext[GreetRequest]):
        name = ctx.payload.name
        emoji = " 👋" if self.include_emoji else ""
        greeting = f"{self.default_greeting}, {name}!{emoji}"
        ctx.send(GreetResponse(greeting=greeting))
```

When creating the agent specification, provide the custom properties:

```python
greeter_spec = AgentBuilder(MyGreeterAgent) \
    .set_name("MyGreeter") \
    .set_description("A friendly greeter agent.") \
    .set_properties(GreeterAgentProps(
        default_greeting="Greetings",
        include_emoji=True
    )) \
    .build_spec()
```

## Next Steps

Now that you've created your first agent, you might want to:

- Learn how to [create a guild with multiple agents](creating_a_guild.md)
- Understand [state management in agents](state_management.md)
- Explore [dependency injection](dependency_injection.md)

For a complete example, see the **Hello World Agent** - `examples/hello_world/hello_world_agent.py` in the examples directory. 