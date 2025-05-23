# LLMPhiAgent

The `LLMPhiAgent` provides access to Microsoft's Phi-2 language model within a RusticAI guild, enabling text generation capabilities using a locally-run model.

## Purpose

This agent serves as a language model interface using Microsoft's Phi-2, a compact yet powerful LLM capable of various text generation tasks. It runs the model locally using Hugging Face's Transformers library.

## When to Use

Use the `LLMPhiAgent` when your application needs to:

- Generate text using a locally-run language model
- Have lower latency than cloud-based LLMs
- Work in environments with limited or no internet access
- Use a lightweight language model with good performance
- Avoid sending sensitive data to external API services

## Configuration

The `LLMPhiAgent` is configured through the `PhiAgentProps` class, which allows setting:

```python
class PhiAgentProps(PyTorchAgentProps):
    model_id: str = "microsoft/phi-2"  # The model ID to load from Hugging Face
```

The agent inherits from the `PyTorchAgentProps` base class, which provides:

```python
class PyTorchAgentProps(BaseAgentProps):
    torch_device: str = "cuda" if torch.cuda.is_available() else "cpu"  # Device to run the model on
```

## Message Types

### Input Messages

#### GenerationPromptRequest

A request for text generation:

```python
class GenerationPromptRequest(BaseModel):
    generation_prompt: str  # The prompt text to complete
```

### Output Messages

#### GenerationPromptResponse

The response with the generated text:

```python
class GenerationPromptResponse(BaseModel):
    generation_prompt: str  # The original prompt
    generated_response: str  # The generated text
```

## Behavior

1. The agent receives a `GenerationPromptRequest` containing a text prompt
2. It tokenizes the prompt using the Phi-2 tokenizer
3. The tokens are processed through the Phi-2 model
4. The generated text is decoded from the output tokens
5. The agent returns a `GenerationPromptResponse` containing both the original prompt and the generated text

## Sample Usage

```python
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.huggingface.agents.llm.phi_agent import LLMPhiAgent, PhiAgentProps

# Create the agent spec
phi_agent_spec = (
    AgentBuilder(LLMPhiAgent)
    .set_id("phi_agent")
    .set_name("Phi-2 LLM")
    .set_description("Text generation using Microsoft's Phi-2 model")
    .set_properties(
        PhiAgentProps(
            model_id="microsoft/phi-2",  # Default is microsoft/phi-2
            torch_device="cuda:0"  # Specify GPU device if needed
        )
    )
    .build_spec()
)

# Add to guild
guild_builder.add_agent_spec(phi_agent_spec)
```

## Example Request

```python
from rustic_ai.core.agents.commons.message_formats import GenerationPromptRequest

# Create a generation request
request = GenerationPromptRequest(
    generation_prompt="The benefits of multi-agent systems include"
)

# Send to the agent
client.publish("default_topic", request)
```

## Example Response

The agent responds with a `GenerationPromptResponse`:

```python
GenerationPromptResponse(
    generation_prompt="The benefits of multi-agent systems include",
    generated_response="The benefits of multi-agent systems include improved problem-solving capabilities, enhanced system robustness, distributed computing efficiency, and the ability to solve complex tasks that single agents cannot handle effectively. Multi-agent systems can also adapt to changing environments and scale more effectively than monolithic systems."
)
```

## Technical Details

The agent leverages:
- Hugging Face's `transformers` library for model loading and inference
- Microsoft's Phi-2 model, a 2.7B parameter language model
- PyTorch for the underlying computation
- Automatic hardware detection to use GPU when available

## Notes and Limitations

- Requires significant RAM/VRAM to load the model (at least 8GB recommended)
- Performance depends on the hardware available (GPU highly recommended)
- The model has a context length limitation of approximately 2,048 tokens
- First-time initialization may take longer as models are downloaded
- While Phi-2 is smaller than models like GPT-4, it still provides good performance on many tasks
- Consider using the `torch_device` property to control which GPU device the model uses in multi-GPU systems 