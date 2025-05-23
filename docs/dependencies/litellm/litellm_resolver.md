# LiteLLMResolver

The `LiteLLMResolver` provides a unified interface for interacting with large language models (LLMs) from various providers like OpenAI, Anthropic, Google, and others. It leverages the [LiteLLM](https://github.com/BerriAI/litellm) library to standardize API calls across different LLM providers.

## Overview

- **Type**: `DependencyResolver[LLM]`
- **Provided Dependency**: `LLM`
- **Package**: `rustic_ai.litellm.agent_ext.llm`

## Features

- **Provider Agnostic**: Consistent interface across different LLM providers
- **Model Switching**: Easily switch between models without changing code
- **Fallback Models**: Configure backup models for reliability
- **Cost Tracking**: Optional tracking of token usage and costs
- **Streaming Support**: Stream responses for real-time interaction
- **Async API**: Support for both synchronous and asynchronous calls

## Configuration

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `model` | `str` | Model identifier (e.g., `"gpt-4"`, `"claude-3-opus"`) | Required |
| `api_key` | `str` | API key for the model provider | `None` (uses environment variables) |
| `organization_id` | `str` | Organization ID for API access | `None` |
| `base_url` | `str` | Custom base URL for API requests | Provider's default URL |
| `timeout` | `float` | Request timeout in seconds | `600.0` (10 minutes) |
| `max_retries` | `int` | Maximum number of retries on failure | `2` |
| `fallback_models` | `List[str]` | List of models to try if primary fails | `[]` |
| `temperature` | `float` | Model temperature (0.0-2.0) | `0.7` |
| `max_tokens` | `int` | Maximum tokens to generate | `None` (model default) |
| `top_p` | `float` | Nucleus sampling parameter | `1.0` |
| `frequency_penalty` | `float` | Penalty for token frequency | `0.0` |
| `presence_penalty` | `float` | Penalty for token presence | `0.0` |
| `extra_headers` | `Dict[str, str]` | Additional headers for API requests | `{}` |

## Usage

### Guild Configuration

```python
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.guild.dsl import DependencySpec

guild_builder = (
    GuildBuilder("llm_guild", "LLM Guild", "Guild with LLM capabilities")
    .add_dependency_resolver(
        "llm",
        DependencySpec(
            class_name="rustic_ai.litellm.agent_ext.llm.LiteLLMResolver",
            properties={
                "model": "gpt-4",
                "temperature": 0.5,
                "max_tokens": 1000,
                "fallback_models": ["gpt-3.5-turbo", "claude-instant-1"]
            }
        )
    )
)
```

### Agent Usage

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.litellm.agent_ext.llm import LLM
from rustic_ai.core.guild.agent_ext.depends.llm.models import ChatCompletionRequest, ChatMessage, ChatMessageRole

class LLMAgent(Agent):
    @agent.processor(clz=QueryRequest, depends_on=["llm"])
    def process_query(self, ctx: agent.ProcessContext, llm: LLM):
        query = ctx.payload.query
        
        # Create chat completion request
        request = ChatCompletionRequest(
            messages=[
                ChatMessage(role=ChatMessageRole.SYSTEM, content="You are a helpful assistant."),
                ChatMessage(role=ChatMessageRole.USER, content=query)
            ]
        )
        
        # Call the LLM
        response = llm.completion(request)
        
        # Send response back
        ctx.send_dict({
            "response": response.choices[0].message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        })
```

## Asynchronous Usage

```python
@agent.processor(clz=QueryRequest, depends_on=["llm"])
async def process_query_async(self, ctx: agent.ProcessContext, llm: LLM):
    query = ctx.payload.query
    
    # Create chat completion request
    request = ChatCompletionRequest(
        messages=[
            ChatMessage(role=ChatMessageRole.SYSTEM, content="You are a helpful assistant."),
            ChatMessage(role=ChatMessageRole.USER, content=query)
        ]
    )
    
    # Call the LLM asynchronously
    response = await llm.async_completion(request)
    
    # Send response back
    ctx.send_dict({
        "response": response.choices[0].message.content,
        "model": response.model
    })
```

## Supported LLM Providers

The LiteLLMResolver supports a wide range of LLM providers through the LiteLLM library:

- **OpenAI**: GPT-3.5, GPT-4, etc.
- **Anthropic**: Claude, Claude Instant, etc.
- **Google**: Gemini, PaLM, etc.
- **Azure OpenAI**: Hosted OpenAI models
- **HuggingFace**: Open source models
- **Cohere**: Command models
- **Many others**: See [LiteLLM documentation](https://github.com/BerriAI/litellm#supported-models) for the full list

## Model Specification

Models are specified using the format defined by LiteLLM. Some examples:

| Provider | Model Specification |
|----------|---------------------|
| OpenAI | `"gpt-4"`, `"gpt-3.5-turbo"` |
| Anthropic | `"anthropic/claude-3-opus"`, `"anthropic/claude-instant-1"` |
| Google | `"google/gemini-pro"` |
| Azure OpenAI | `"azure/gpt-4"` |
| HuggingFace | `"huggingface/meta-llama/Llama-2-7b"` |

## API Keys

API keys can be provided in three ways (in order of precedence):

1. Directly in the resolver properties (`api_key` parameter)
2. Environment variables (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)
3. LiteLLM config file (see LiteLLM documentation)

## Cost Management

LiteLLM provides built-in cost tracking. You can access usage information from the response:

```python
response = llm.completion(request)
prompt_tokens = response.usage.prompt_tokens
completion_tokens = response.usage.completion_tokens
total_tokens = response.usage.total_tokens

# Estimate cost (provider and model dependent)
estimated_cost = total_tokens * 0.00002  # Example rate for GPT-3.5-turbo
```

## Error Handling

The LiteLLM resolver handles common errors like rate limits, timeouts, and model-specific errors:

```python
try:
    response = llm.completion(request)
    # Process response
except Exception as e:
    # Handle error
    error_message = str(e)
    if "rate limit" in error_message.lower():
        # Handle rate limiting
        time.sleep(5)
        # Retry or use fallback
    elif "context length" in error_message.lower():
        # Handle context length exceeded
        # Truncate input or use different model
    else:
        # Handle other errors
```

## Example: Multimodal Input

For models that support images (like GPT-4 Vision):

```python
from rustic_ai.core.guild.agent_ext.depends.llm.models import ImageURL

request = ChatCompletionRequest(
    messages=[
        ChatMessage(
            role=ChatMessageRole.USER,
            content=[
                {"type": "text", "text": "What's in this image?"},
                {"type": "image_url", "image_url": ImageURL(url="https://example.com/image.jpg")}
            ]
        )
    ]
)

response = llm.completion(request)
```

## Related Resolvers

Other LLM-related resolvers that might be useful in conjunction with LiteLLMResolver:

- OpenAI Embeddings (from LangChain package)
- Vector stores (for retrieval-augmented generation)
- KV stores (for caching responses) 