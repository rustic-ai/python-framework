# Managing State in Agents

This guide explains how to manage state in RusticAI agents, allowing them to maintain data between message processing and share state across the guild.

## Prerequisites

Before you begin, make sure you have:
- Installed RusticAI and its dependencies
- Basic understanding of agents (see [Creating Your First Agent](creating_your_first_agent.md))
- Familiarity with RusticAI [core concepts](../core/index.md)

## Understanding State in RusticAI

RusticAI provides a robust state management system that allows agents to:
- Maintain their own state across message processing
- Access the shared guild state
- Persist state using state backends
- Update state safely with concurrency control

## Types of State

There are two primary types of state in a RusticAI guild:

1. **Agent State**: Private to each agent instance
2. **Guild State**: Shared across all agents in the guild

## Accessing State

By default, every agent has access to:

- `self._state`: A dictionary containing the agent's current state
- `self._guild_state`: A dictionary containing the guild's shared state

However, you should not modify these dictionaries directly. Instead, use the state management APIs described below.

## Basic State Management Using `StateRefresherMixin`

The `StateRefresherMixin` is automatically included in all agents via the `AgentMetaclass`. It provides methods for state management:

```python
from rustic_ai.core.state.models import StateUpdateFormat

class MyStatefulAgent(Agent[BaseAgentProps]):
    def __init__(self, agent_spec: AgentSpec[BaseAgentProps]):
        super().__init__(agent_spec)
        self.counter = 0  # Local instance variable (not persisted)
        
    @agent.processor(clz=IncrementRequest)
    def increment_counter(self, ctx: agent.ProcessContext[IncrementRequest]):
        # Read from state
        current_count = self._state.get("count", 0)
        
        # Update local variable
        self.counter += 1
        
        # Calculate new state
        new_count = current_count + ctx.payload.amount
        
        # Update state using StateRefresherMixin methods
        self.update_state(
            ctx=ctx,
            update_format=StateUpdateFormat.MERGE_DICT,
            update={"count": new_count, "last_updated": time.time()}
        )
        
        # Similarly, you can update guild state
        self.update_guild_state(
            ctx=ctx,
            update_format=StateUpdateFormat.MERGE_DICT,
            update={"last_action": f"Increment by {ctx.payload.amount}"}
        )
        
        # Respond with the new state
        ctx.send(CountResponse(count=new_count))
```

## State Update Formats

RusticAI supports several formats for updating state:

1. **`MERGE_DICT`**: Merges the update dictionary with the existing state
2. **`REPLACE_DICT`**: Completely replaces the state with the new dictionary
3. **`JMESPATH_UPDATE`**: Uses JMESPath expressions for more targeted updates

Example of JMESPATH_UPDATE:

```python
# Update a nested value
self.update_state(
    ctx=ctx,
    update_format=StateUpdateFormat.JMESPATH_UPDATE,
    update={"users[0].visits": self._state["users"][0]["visits"] + 1}
)
```

## Requesting State Explicitly

You can request the latest state explicitly:

```python
@agent.processor(clz=StateRequest)
def handle_state_request(self, ctx: agent.ProcessContext[StateRequest]):
    # Request my own state
    self.request_state(ctx)
    
    # Request guild state
    self.request_guild_state(ctx)
    
    # The StateRefresherMixin will automatically update self._state and self._guild_state
    # when the responses arrive
```

## State Lifecycle and Persistence

States in RusticAI are managed by a `StateManager` which handles:

1. **Persistence**: Storing state in a chosen backend
2. **Versioning**: Maintaining version history of state changes
3. **Concurrency**: Handling concurrent updates to the same state
4. **Distribution**: Managing state across distributed agents

The state lifecycle flows as follows:

1. Agent requests state using `request_state()`
2. State manager responds with current state
3. Agent's `self._state` is updated via `StateRefresherMixin`
4. Agent performs operations using state data
5. Agent requests state update using `update_state()`
6. State manager applies the update and returns the new state
7. Agent's `self._state` is updated again

## Example: Implementing a Counter Agent

Here's a complete example of a counter agent that maintains its count in state:

```python
from pydantic import BaseModel
from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.dsl import AgentSpec, BaseAgentProps
from rustic_ai.core.state.models import StateUpdateFormat

class CounterRequest(BaseModel):
    """Request to manipulate the counter."""
    action: str  # "increment", "decrement", "reset", "get"
    amount: int = 1

class CounterResponse(BaseModel):
    """Response with the current counter value."""
    count: int
    operation: str

class CounterAgent(Agent[BaseAgentProps]):
    """An agent that maintains a counter in its state."""

    def __init__(self, agent_spec: AgentSpec[BaseAgentProps]):
        super().__init__(agent_spec)
        print(f"CounterAgent initialized with ID: {self.id}")

    @agent.processor(clz=CounterRequest)
    def process_counter_request(self, ctx: agent.ProcessContext[CounterRequest]):
        """Process a counter request."""
        # Get current count from state or default to 0
        current_count = self._state.get("count", 0)
        action = ctx.payload.action
        amount = ctx.payload.amount
        
        # Determine the new count based on the action
        if action == "increment":
            new_count = current_count + amount
            operation = f"Incremented by {amount}"
        elif action == "decrement":
            new_count = current_count - amount
            operation = f"Decremented by {amount}"
        elif action == "reset":
            new_count = 0
            operation = "Reset to 0"
        elif action == "get":
            new_count = current_count
            operation = "Retrieved current value"
        else:
            ctx.send(CounterResponse(count=current_count, operation="Unknown operation"))
            return
        
        # Update the state
        self.update_state(
            ctx=ctx,
            update_format=StateUpdateFormat.MERGE_DICT,
            update={"count": new_count}
        )
        
        # Also update guild state to track the last operation
        self.update_guild_state(
            ctx=ctx,
            update_format=StateUpdateFormat.MERGE_DICT,
            update={"last_counter_operation": operation}
        )
        
        # Send the response
        ctx.send(CounterResponse(count=new_count, operation=operation))
```

## Using This Agent in a Guild

```python
import asyncio
from rustic_ai.core.guild.builders import AgentBuilder, GuildBuilder
from rustic_ai.core.agents.testutils.probe_agent import ProbeAgent

async def main():
    # Create and launch a guild
    guild = GuildBuilder("counter_guild", "Counter Guild", "A guild with a stateful counter agent") \
        .launch(add_probe=True)
    
    # Get the probe agent
    probe_agent = guild.get_agent_of_type(ProbeAgent)
    
    # Create and launch the counter agent
    counter_agent_spec = AgentBuilder(CounterAgent) \
        .set_name("Counter") \
        .set_description("A stateful counter agent") \
        .build_spec()
    
    guild.launch_agent(counter_agent_spec)
    
    # Test the counter operations
    operations = [
        CounterRequest(action="increment", amount=5),
        CounterRequest(action="increment", amount=3),
        CounterRequest(action="decrement", amount=2),
        CounterRequest(action="get")
    ]
    
    for op in operations:
        print(f"\nSending {op.action} request...")
        probe_agent.publish("default_topic", op)
        await asyncio.sleep(0.5)  # Allow time for processing
        
        # Get and clear messages
        messages = probe_agent.get_messages()
        for msg in messages:
            if hasattr(msg.payload, "count"):
                print(f"Count: {msg.payload.count}, Operation: {msg.payload.operation}")
        probe_agent.clear_messages()
    
    # Shutdown the guild
    guild.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Best Practices for State Management

1. **Use Helper Methods**: Always use `update_state()` and `update_guild_state()` instead of directly modifying `self._state` or `self._guild_state`.

2. **Keep State Clean**: Store only serializable data in state. Complex objects, file handles, or connection objects should not be stored in state.

3. **Minimize State Size**: Keep state reasonably sized. Large states can impact performance, especially with distributed backends.

4. **Handle State Carefully**: Consider potential race conditions when updating state based on its current value.

5. **Structure Your State**: Use a consistent schema for your state to make it easier to reason about.

6. **Version Your State**: Consider including a version field in your state to handle schema migrations.

## Advanced State Management

### Custom State Backends

RusticAI supports various state backends such as:
- In-memory (default)
- Redis
- SQLite
- Custom backends

To configure a custom state backend, you would typically do this at the guild level:

```python
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.state.manager import SQLiteStateManager

# Create a guild with a custom state manager
guild = GuildBuilder("my_guild", "My Guild", "A guild with custom state management") \
    .set_state_manager(SQLiteStateManager(db_path="my_guild_state.db")) \
    .launch()
```

### State Snapshots and Version Control

You can manage state versions:

```python
# Get a specific version of state
self.request_state(ctx, version=5)

# Get state at a specific timestamp
self.request_state(ctx, timestamp=1610000000000)
```

## Next Steps

Now that you understand state management, you might want to:
- Learn about [dependency injection](dependency_injection.md) for more complex agent configurations
- Explore [creating custom guild specifications](guild_specifications.md)
- Understand [testing and debugging](testing_agents.md) stateful agents

For a complete example, see the **Stateful Counter Agent** - `examples/basic_agents/stateful_counter_agent.py` in the examples directory. 