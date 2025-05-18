# LiteLLMAgent

The `LiteLLMAgent` provides a unified interface to various Large Language Models (LLMs) through integration with the [LiteLLM](https://github.com/BerriAI/litellm) library, enabling consistent interaction with different LLM providers.

## Purpose

This agent acts as a gateway to language models from providers like OpenAI, Anthropic, Google, and others. It provides a consistent message format and response handling, regardless of the underlying LLM being used.

## When to Use

Use the `LiteLLMAgent` when your application needs to:

- Interact with various LLMs through a unified interface
- Switch between different LLM providers without changing application code
- Maintain conversation history with LLMs
- Use system prompts and conversation context
- Leverage LLM tools and function calling capabilities

## Configuration

The `LiteLLMAgent` is configured through the `LiteLLMConf` class, which allows setting:

- The LLM model to use
- Default system messages
- Tools/function definitions
- Conversation memory size

The agent requires appropriate API keys for the selected model, which must be set as environment variables (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`).

## Message Types

### Input Messages

#### ChatCompletionRequest

A request for the LLM to process.

```python
class ChatCompletionRequest(BaseModel):
    messages: List[Union[SystemMessage, UserMessage, AssistantMessage, ToolMessage, FunctionMessage]]
    model: Optional[str] = None  # Overrides the default model if specified
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: Optional[List[ChatCompletionTool]] = None
    tool_choice: Optional[Union[str, ToolChoice]] = None
    mock_response: Optional[str] = None  # Used for testing
    # Other LLM parameters...
```

The message types include:
- `SystemMessage`: Instructions to the model about how to behave
- `UserMessage`: Input from the user
- `AssistantMessage`: Previous responses from the assistant
- `ToolMessage`/`FunctionMessage`: Tool call results

### Output Messages

#### ChatCompletionResponse

Sent when the LLM has generated a response:

```python
class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: Optional[ChatCompletionUsage] = None
```

The `choices` field contains the generated responses, potentially including tool calls.

#### ChatCompletionError

Sent when an error occurs during LLM processing:

```python
class ChatCompletionError(BaseModel):
    status_code: ResponseCodes
    message: str
    response: Optional[str] = None
    model: Optional[str] = None
    request_messages: Optional[List[Any]] = None
```

## Behavior

1. The agent receives a chat completion request with messages
2. It prepends any configured system messages from its initialization
3. If conversation memory is enabled, it includes previous exchanges
4. The request is sent to the LLM provider via LiteLLM
5. The response is formatted and returned in a standardized format
6. The conversation is updated in memory for subsequent requests

## Properties

The `LiteLLMConf` class supports the following properties:

| Property | Type | Description |
|----------|------|-------------|
| model | str | The LLM model to use (e.g., "gpt-4", "claude-3-opus") |
| messages | List[Message] | Default messages to prepend to all requests |
| tools | List[ChatCompletionTool] | Tools/functions the model can call |
| message_memory | Optional[int] | Number of message exchanges to remember |
| temperature | Optional[float] | Sampling temperature for generation |
| max_tokens | Optional[int] | Maximum tokens to generate |
| *Additional LLM parameters* | Various | Any parameter supported by the LLM provider |

## Sample Usage

```python
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.guild.agent_ext.depends.llm.models import SystemMessage
from rustic_ai.litellm.agent import LiteLLMAgent, LiteLLMConf
from rustic_ai.core.guild.agent_ext.depends.llm.models import Models

# Create the agent spec
llm_agent_spec = (
    AgentBuilder(LiteLLMAgent)
    .set_id("llm_agent")
    .set_name("Language Model")
    .set_description("Interacts with various LLMs via LiteLLM")
    .set_properties(
        LiteLLMConf(
            model=Models.gpt_4o,  # Use GPT-4o model
            messages=[
                SystemMessage(content="You are a helpful assistant in the RusticAI framework."),
            ],
            message_memory=10,  # Remember 10 message exchanges
            temperature=0.7,
        )
    )
    .build_spec()
)

# Add to guild
guild_builder.add_agent_spec(llm_agent_spec)
```

## Example Request

```python
from rustic_ai.core.guild.agent_ext.depends.llm.models import (
    ChatCompletionRequest,
    UserMessage
)

# Create a chat completion request
request = ChatCompletionRequest(
    messages=[
        UserMessage(content="What can RusticAI be used for?")
    ]
)

# Send to the agent
client.publish("default_topic", request)
```

## Example Response

The agent responds with a `ChatCompletionResponse` containing the LLM's response:

```python
ChatCompletionResponse(
    id="response-12345",
    object="chat.completion",
    created=1685960528,
    model="gpt-4o",
    choices=[
        ChatCompletionResponseChoice(
            index=0,
            message=AssistantMessage(
                content="RusticAI is a multi-agent framework that can be used to build..."
            ),
            finish_reason="stop"
        )
    ],
    usage=ChatCompletionUsage(
        prompt_tokens=25,
        completion_tokens=114,
        total_tokens=139
    )
)
```

## Testing with Mock Responses

For testing purposes, the `ChatCompletionRequest` accepts a `mock_response` parameter that bypasses the actual LLM call:

```python
request = ChatCompletionRequest(
    messages=[UserMessage(content="Test question")],
    mock_response="This is a mocked response for testing."
)
```

## Notes and Limitations

- Requires appropriate API keys for the chosen model provider
- Cost considerations apply based on the model and token usage
- Different models have different capabilities (e.g., context length, tool calling)
- Rate limits apply based on your subscription with the LLM provider 