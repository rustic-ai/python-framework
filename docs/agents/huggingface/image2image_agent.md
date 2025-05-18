# Image2ImageAgent

The `Image2ImageAgent` provides image-to-image transformation capabilities within a RusticAI guild using the Pix2Pix model, enabling conditional image generation and editing.

## Purpose

This agent allows transformation of source images based on text instructions, performing tasks like style transfer, image modification, or feature addition. It uses the Pix2Pix model, which specializes in conditional image-to-image translation.

## When to Use

Use the `Image2ImageAgent` when your application needs to:

- Transform existing images based on text instructions
- Edit images in a controlled manner
- Apply specific modifications to visual content
- Generate variations of existing images
- Implement controlled image manipulation based on natural language

## Configuration

The `Image2ImageAgent` is configured through the `Pix2PixProps` class, which allows setting:

```python
class Pix2PixProps(PyTorchAgentProps):
    model_id: str = "timbrooks/instruct-pix2pix"  # The model ID to load from Hugging Face
```

The agent inherits from the `PyTorchAgentProps` base class, which provides:

```python
class PyTorchAgentProps(BaseAgentProps):
    torch_device: str = "cuda" if torch.cuda.is_available() else "cpu"  # Device to run the model on
```

## Dependencies

The `Image2ImageAgent` requires:

- **filesystem** (Guild-level dependency): A file system implementation for storing transformed images

## Message Types

### Input Messages

#### ImageEditRequest

A request to transform an image:

```python
class ImageEditRequest(BaseModel):
    source_image: MediaLink  # The source image to transform
    instruction: str  # Text instruction describing the desired transformation
    num_inference_steps: int = 20  # Number of inference steps (higher = better quality)
    image_guidance_scale: float = 1.5  # How closely to follow the source image
    guidance_scale: float = 7.5  # How closely to follow the instruction
    strength: float = 0.8  # Amount of noise added (higher = more transformation)
    image_format: str = "png"  # Output format for the image
    width: Optional[int] = None  # Optional width to resize to
    height: Optional[int] = None  # Optional height to resize to
```

### Output Messages

#### ImageEditResponse

Sent when image transformation is completed:

```python
class ImageEditResponse(BaseModel):
    files: List[MediaLink]  # List of transformed image files
    errors: List[str]  # Any errors that occurred during processing
    request: str  # The original request (JSON string)
```

Each `MediaLink` contains:
- url: Path to the generated image file
- name: Filename (UUID-based)
- mimetype: Content type (image/png)
- on_filesystem: Always True for generated images
- metadata: Contains information about the transformation

#### ErrorMessage

Sent when image transformation fails:

```python
class ErrorMessage(BaseModel):
    agent_type: str
    error_type: str  # "ImageTransformationError"
    error_message: str
```

## Behavior

1. The agent receives an `ImageEditRequest` with a source image and instruction
2. The source image is loaded and preprocessed
3. The image is transformed according to the instruction using the Pix2Pix model
4. The transformed image is saved to a file with a generated UUID filename
5. A `MediaLink` is created for the transformed image
6. An `ImageEditResponse` containing the image link is sent
7. If any errors occur, an `ErrorMessage` is sent

## Sample Usage

```python
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.guild.agent_ext.depends.dependency_resolver import DependencySpec
from rustic_ai.huggingface.agents.diffusion.pix2pix import Image2ImageAgent, Pix2PixProps

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
pix2pix_agent_spec = (
    AgentBuilder(Image2ImageAgent)
    .set_id("image_editor")
    .set_name("Image Editor")
    .set_description("Transforms images based on text instructions using Pix2Pix")
    .set_properties(
        Pix2PixProps(
            model_id="timbrooks/instruct-pix2pix",  # Default model
            torch_device="cuda:0"  # Specify GPU device if needed
        )
    )
    .build_spec()
)

# Add dependency to guild when launching
guild_builder.add_dependency("filesystem", filesystem)
guild_builder.add_agent_spec(pix2pix_agent_spec)
```

## Example Request

```python
from rustic_ai.core.agents.commons.media import MediaLink
from rustic_ai.huggingface.agents.models import ImageEditRequest

# Create an image edit request
edit_request = ImageEditRequest(
    source_image=MediaLink(
        url="/path/to/source/image.jpg",
        name="source_image.jpg",
        on_filesystem=True,
        mimetype="image/jpeg"
    ),
    instruction="Make it look like a winter scene with snow",
    guidance_scale=9.0,  # Higher guidance for more faithful adherence to instruction
    strength=0.7  # Slightly lower strength to preserve more of the original
)

# Send to the agent
client.publish("default_topic", edit_request)
```

## Technical Details

The agent uses:
- Hugging Face's `diffusers` library with the `StableDiffusionInstructPix2PixPipeline`
- Tim Brooks' Instruct-Pix2Pix model
- PyTorch for tensor operations
- PIL for image manipulation
- Automatic hardware detection to use GPU when available

## Notes and Limitations

- Requires significant VRAM to run efficiently (at least 8GB recommended)
- Performance is much better with a GPU
- Quality of transformations depends heavily on the clarity of instructions
- Works best with certain types of transformations (e.g., style changes, weather effects)
- First-time initialization may take longer as models are downloaded
- Larger images require more memory and processing time
- The `strength` parameter controls how much of the original image is preserved versus changed
- The `image_guidance_scale` controls how closely the output adheres to the input image structure 