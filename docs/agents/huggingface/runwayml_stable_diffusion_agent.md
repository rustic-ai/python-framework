# RunwaymlStableDiffusionAgent

The `RunwaymlStableDiffusionAgent` is an image generation agent that creates images from text prompts using Stability AI's Stable Diffusion model.

## Purpose

This agent provides text-to-image generation capabilities within a RusticAI guild, enabling the creation of images from natural language descriptions. It uses Stable Diffusion 3.5, a powerful diffusion model capable of generating high-quality images.

## When to Use

Use the `RunwaymlStableDiffusionAgent` when your application needs to:

- Generate images from text descriptions
- Create visual content based on textual prompts
- Produce illustrations or artwork programmatically
- Visualize concepts or ideas described in text
- Add image generation capabilities to your AI system

## Configuration

The `RunwaymlStableDiffusionAgent` is configured through the `RunwaymlStableDiffusionProps` class, which allows setting:

```python
class RunwaymlStableDiffusionProps(PyTorchAgentProps):
    model_id: str = "stabilityai/stable-diffusion-3.5-medium"  # The model ID to load from Hugging Face
```

The agent inherits from the `PyTorchAgentProps` base class, which provides:

```python
class PyTorchAgentProps(BaseAgentProps):
    torch_device: str = "cuda" if torch.cuda.is_available() else "cpu"  # Device to run the model on
```

## Dependencies

The `RunwaymlStableDiffusionAgent` requires:

- **filesystem** (Guild-level dependency): A file system implementation for storing generated images

## Message Types

### Input Messages

#### ImageGenerationRequest

A request to generate images:

```python
class ImageGenerationRequest(BaseModel):
    generation_prompt: str  # The text prompt describing the desired image
    num_images: int = 1  # Number of images to generate
    guidance_scale: float = 7.5  # How closely to follow the prompt (higher = more faithful)
    num_inference_steps: int = 50  # Number of denoising steps (higher = better quality, slower)
    height: int = 1024  # Height of the generated image
    width: int = 1024  # Width of the generated image
    image_format: str = "png"  # Output format for the image
```

### Output Messages

#### ImageGenerationResponse

Sent when image generation is completed:

```python
class ImageGenerationResponse(BaseModel):
    files: List[MediaLink]  # List of generated image files
    errors: List[str]  # Any errors that occurred during generation
    request: str  # The original request (JSON string)
```

Each `MediaLink` contains:
- url: Path to the generated image file
- name: Filename (UUID-based)
- mimetype: Content type (image/png)
- on_filesystem: Always True for generated images

#### ErrorMessage

Sent when image generation fails:

```python
class ErrorMessage(BaseModel):
    agent_type: str
    error_type: str  # "ImageGenerationError"
    error_message: str
```

## Behavior

1. The agent receives an `ImageGenerationRequest` with a text prompt
2. The prompt is processed through the Stable Diffusion pipeline
3. The specified number of images are generated with the requested parameters
4. The images are saved to files with generated UUID filenames
5. A `MediaLink` is created for each generated image
6. An `ImageGenerationResponse` containing all the image links is sent
7. If any errors occur, an `ErrorMessage` is sent

## Sample Usage

```python
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.guild.agent_ext.depends.dependency_resolver import DependencySpec
from rustic_ai.huggingface.agents.diffusion.stable_diffusion_agent import (
    RunwaymlStableDiffusionAgent,
    RunwaymlStableDiffusionProps
)

# Define a file system dependency
filesystem = DependencySpec(
    class_name="rustic_ai.core.guild.agent_ext.depends.filesystem.FileSystemResolver",
    properties={
        "path_base": "/tmp",
        "protocol": "file",
        "storage_options": {
            "auto_mkdir": True,
        },
    },
)

# Create the agent spec
sd_agent_spec = (
    AgentBuilder(RunwaymlStableDiffusionAgent)
    .set_id("image_generator")
    .set_name("Image Generator")
    .set_description("Generates images from text using Stable Diffusion")
    .set_properties(
        RunwaymlStableDiffusionProps(
            model_id="stabilityai/stable-diffusion-3.5-medium",  # Default model
            torch_device="cuda:0"  # Specify GPU device if needed
        )
    )
    .build_spec()
)

# Add dependency to guild when launching
guild_builder.add_dependency("filesystem", filesystem)
guild_builder.add_agent_spec(sd_agent_spec)
```

## Example Request

```python
from rustic_ai.huggingface.agents.models import ImageGenerationRequest

# Create an image generation request
image_request = ImageGenerationRequest(
    generation_prompt="A serene forest lake at sunset with mountains in the background",
    num_images=2,  # Generate 2 variations
    guidance_scale=8.0,  # Slightly higher guidance for more prompt adherence
    num_inference_steps=30,  # Fewer steps for faster generation
    height=768,
    width=768
)

# Send to the agent
client.publish("default_topic", image_request)
```

## Technical Details

The agent uses:
- Hugging Face's `diffusers` library with the `StableDiffusion3Pipeline`
- Stability AI's Stable Diffusion 3.5 model
- PyTorch for tensor operations
- Automatic hardware detection to use GPU when available

## Notes and Limitations

- Requires significant VRAM to run efficiently (at least 8GB recommended)
- Performance is much better with a GPU
- Generation time depends on the number of inference steps and image size
- First-time initialization may take longer as models are downloaded
- Large image sizes (>1024x1024) may require more memory
- Model is run locally, so consider hardware requirements when deploying
- Consider using a custom `model_id` for different versions of Stable Diffusion 