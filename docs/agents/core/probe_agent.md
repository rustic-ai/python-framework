# ProbeAgent

The `ProbeAgent` is a specialized utility agent used for testing and debugging agent interactions within a RusticAI guild. It captures messages, allows sending test messages, and provides inspection capabilities.

## Purpose

This agent serves as a powerful testing tool that can:
- Record all messages it receives
- Send messages to other agents
- Inspect message flow within a guild
- Simulate interactions for integration testing
- Aid in debugging complex multi-agent systems

## When to Use

Use the `ProbeAgent` when you need to:

- Write tests for agent interactions
- Debug message flow in a guild
- Monitor communication between agents
- Simulate external inputs to the guild
- Validate agent responses

## Properties

The `ProbeAgent` does not require any special configuration properties.

## Capabilities

The `ProbeAgent` provides several key capabilities:

### 1. Message Capturing

All messages sent to the probe agent are stored and can be retrieved for inspection:

```python
# Get all messages received by the probe
messages = probe_agent.get_messages()

# Get messages of a specific format
chat_messages = probe_agent.get_messages_of_format(SimpleChatMessage)
```

### 2. Message Publishing

The probe can send messages to other agents:

```python
# Publish a message to a topic
probe_agent.publish("default_topic", some_message)

# Publish a dictionary as a message with a specific format
probe_agent.publish_dict(
    "default_topic",
    {"content": "Hello, world!"},
    format=SimpleChatMessage
)
```

### 3. Message Clearing

The message history can be cleared:

```python
# Clear all captured messages
probe_agent.clear_messages()
```

## Sample Usage in Tests

```python
import pytest
import time

from rustic_ai.core.guild.builders import GuildBuilder, AgentBuilder
from rustic_ai.core.agents.testutils.probe_agent import ProbeAgent
from rustic_ai.core.agents.llm.simple_llm_agent import SimpleLLMAgent, SimpleChatMessage

@pytest.fixture
def test_guild():
    # Create a guild for testing with a probe agent
    guild = GuildBuilder("test_guild", "Test Guild", "Guild for testing").launch(add_probe=True)
    
    # Add test agent
    agent_spec = AgentBuilder(SimpleLLMAgent).set_name("ChatAgent").build_spec()
    guild.launch_agent(agent_spec)
    
    # Get the probe agent for testing
    probe_agent = guild.get_agent_of_type(ProbeAgent)
    
    # Return guild and probe for test use
    try:
        yield guild, probe_agent
    finally:
        # Clean up
        guild.shutdown()

def test_chat_agent_response(test_guild):
    guild, probe_agent = test_guild
    
    # Send a test message through the probe
    probe_agent.publish_dict(
        guild.DEFAULT_TOPIC,
        {"content": "Hello, how are you?"},
        format=SimpleChatMessage
    )
    
    # Wait for processing
    time.sleep(1)
    
    # Get all messages captured by the probe
    messages = probe_agent.get_messages()
    
    # Verify a response was received
    assert len(messages) >= 1
    
    # Check the response content
    response = messages[0]
    assert "I'm doing well" in response.payload["content"]
```

## Probe Agent Variants

### EssentialProbeAgent

The `EssentialProbeAgent` is a variant that automatically subscribes to the essential topics in the guild, making it useful for monitoring system-level messages.

## Integration with Guild Builder

The `GuildBuilder` class provides a convenient method to add a probe agent when launching a guild:

```python
# Create a guild with a probe agent
guild = GuildBuilder("my_guild", "My Guild", "Description").launch(add_probe=True)

# Access the probe agent
probe_agent = guild.get_agent_of_type(ProbeAgent)
```

## Best Practices

1. **Use in Test Fixtures**: Create a fixture that sets up a guild with a probe agent and tears it down after tests.

2. **Wait for Asynchronous Processing**: Use `time.sleep()` or better asynchronous waiting patterns to allow time for messages to be processed.

3. **Clear Messages Between Tests**: Use `probe_agent.clear_messages()` between test cases to ensure clean testing state.

4. **Test Message Patterns**: Don't just test for response existence, but verify the correct content and message patterns.

5. **Use for Debugging**: During development, add a probe agent to inspect message flow and diagnose issues.

## Notes and Limitations

- The probe agent stores messages in memory, so be cautious with large message volumes
- Message history isn't persisted beyond the lifetime of the guild
- Not intended for production use, only for testing and debugging 