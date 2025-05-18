# SimpleLLMAgent

The `SimpleLLMAgent` is a basic implementation of a Large Language Model agent within the RusticAI framework. It provides an easy-to-use interface for conversational interactions with language models.

## Purpose

This agent serves as a straightforward way to interact with language models in a conversational manner. It maintains a chat history and handles the formatting of messages for LLM interactions via a dependency injection pattern.

## When to Use

Use the `SimpleLLMAgent` when your application needs:

- A simple conversational interface with a language model
- Basic chat memory functionality
- A minimal implementation that can be easily extended
- A reference implementation for creating custom LLM agents

## Dependencies

The `SimpleLLMAgent` requires:

- **llm**: An LLM dependency that implements the LLM interface

## Configuration

The `SimpleLLMAgent` is configured through the `SimpleLLMAgentConf` class, which allows setting:

```python
class SimpleLLMAgentConf(BaseAgentProps):
    chat_memory: int = 10  # Number of messages to keep in memory
    system_messages: List[str] = ["You are a helpful assistant."]  # System instructions
```

## Message Types

### Input Messages

#### SimpleChatMessage

A simple chat message from a user.

```python
class SimpleChatMessage(BaseModel):
    content: str  # The user's message
```

### Output Messages

#### SimpleChatResponse

The agent's response to a chat message.

```python
class SimpleChatResponse(BaseModel):
    content: str  # The LLM's response
```

#### ChatCompletionError

Sent when an error occurs during LLM processing:

```python
class ChatCompletionError(BaseModel):
    status_code: ResponseCodes
    message: str
    model: str
    request_messages: List[Any]
```

## Behavior

1. The agent receives a chat message
2. It formats the message into a prompt, including:
   - System messages (from configuration)
   - Chat history (up to the configured limit)
   - The new user message
3. The formatted prompt is sent to the LLM dependency
4. The response from the LLM is captured and returned
5. Both the user message and the LLM response are added to the chat history

## Sample Usage

```python
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.guild.agent_ext.depends.dependency_resolver import DependencySpec
from rustic_ai.core.agents.llm.simple_llm_agent import SimpleLLMAgent, SimpleLLMAgentConf

# Create an LLM dependency
llm_dependency = DependencySpec(
    class_name="rustic_ai.litellm.agent_ext.llm.LiteLLMResolver",
    properties={
        "model": "gpt-4",
    },
)

# Create the agent spec
simple_llm_agent_spec = (
    AgentBuilder(SimpleLLMAgent)
    .set_id("chat_agent")
    .set_name("Chat Agent")
    .set_description("Simple conversational agent using an LLM")
    .set_properties(
        SimpleLLMAgentConf(
            chat_memory=15,  # Remember 15 messages
            system_messages=[
                "You are a helpful assistant in the RusticAI framework.",
                "You provide concise and accurate information."
            ]
        )
    )
    .build_spec()
)

# Add dependency to guild when launching
guild_builder.add_dependency("llm", llm_dependency)
guild_builder.add_agent_spec(simple_llm_agent_spec)
```

## Example Request

```python
from rustic_ai.core.agents.llm.simple_llm_agent import SimpleChatMessage

# Create a chat message
message = SimpleChatMessage(
    content="What is a multi-agent system?"
)

# Send to the agent
client.publish("default_topic", message)
```

## Example Response

The agent responds with a `SimpleChatResponse`:

```python
SimpleChatResponse(
    content="A multi-agent system (MAS) is a computerized system composed of multiple interacting intelligent agents within an environment. Multi-agent systems can solve problems that are difficult or impossible for an individual agent to solve. In RusticAI, these agents can communicate, coordinate, and collaborate to accomplish complex tasks."
)
```

## Extending the Agent

The `SimpleLLMAgent` is designed to be a minimal implementation that can be extended for more specialized use cases. You can extend it to add:

- Custom message preprocessing
- Additional message types
- More sophisticated memory management
- Integration with other agent capabilities

## Notes and Limitations

- Provides only basic conversational capabilities
- Memory is stored in-memory and not persisted
- Does not implement advanced features like tool calling
- Relies on the underlying LLM dependency for most functionality 