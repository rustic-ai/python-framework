# SpeechT5TTSAgent

The `SpeechT5TTSAgent` is a text-to-speech synthesis agent that converts text into spoken audio using Microsoft's SpeechT5 model via Hugging Face.

## Purpose

This agent provides text-to-speech (TTS) capabilities within a RusticAI guild, enabling conversion of text content into natural-sounding speech. It uses the Microsoft SpeechT5 model, which produces high-quality speech synthesis.

## When to Use

Use the `SpeechT5TTSAgent` when your application needs to:

- Convert text to spoken audio
- Generate voice responses for users
- Create audio content from textual data
- Add voice capabilities to your AI system
- Make information more accessible through audio formats

## Dependencies

The `SpeechT5TTSAgent` requires:

- **filesystem** (Guild-level dependency): A file system implementation for storing generated audio files

## Message Types

### Input Messages

#### GenerationPromptRequest

A request to convert text to speech:

```python
class GenerationPromptRequest(BaseModel):
    generation_prompt: str  # The text to convert to speech
```

### Output Messages

#### MediaLink

When synthesis is successful, a `MediaLink` message is emitted with the audio content:

```python
class MediaLink(BaseModel):
    url: str  # Path to the generated audio file
    name: str  # Filename
    metadata: Dict  # Metadata including sampling rate
    on_filesystem: bool  # Always True for generated audio
    mimetype: str  # Content type (audio/wav)
```

#### ErrorMessage

Sent when speech synthesis fails:

```python
class ErrorMessage(BaseModel):
    agent_type: str
    error_type: str  # "SpeechGenerationError" or "FileWriteError"
    error_message: str
```

## Behavior

1. The agent receives a `GenerationPromptRequest` with text content
2. It processes the text through the SpeechT5 TTS pipeline
3. The synthesized speech is saved to a WAV file with a generated UUID filename
4. A `MediaLink` message is emitted with a reference to the generated audio file
5. If any errors occur during synthesis or file writing, an `ErrorMessage` is sent

## Sample Usage

```python
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.guild.agent_ext.depends.dependency_resolver import DependencySpec
from rustic_ai.huggingface.agents.text_to_speech.speecht5_tts_agent import SpeechT5TTSAgent

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
tts_agent_spec = (
    AgentBuilder(SpeechT5TTSAgent)
    .set_id("tts_agent")
    .set_name("Text-to-Speech")
    .set_description("Converts text to spoken audio using SpeechT5")
    .build_spec()
)

# Add dependency to guild when launching
guild_builder.add_dependency("filesystem", filesystem)
guild_builder.add_agent_spec(tts_agent_spec)
```

## Example Request

```python
from rustic_ai.core.agents.commons.message_formats import GenerationPromptRequest

# Create a text-to-speech request
tts_request = GenerationPromptRequest(
    generation_prompt="Welcome to RusticAI, a powerful multi-agent framework."
)

# Send to the agent
client.publish("default_topic", tts_request)
```

## Technical Details

The agent uses:
- The Hugging Face `transformers` library with the `text-to-speech` pipeline
- Microsoft's SpeechT5 model (`microsoft/speecht5_tts`)
- Speaker embeddings from the CMU Arctic dataset for voice characteristics
- SoundFile for writing WAV audio files

## Notes and Limitations

- The agent uses a fixed speaker embedding, resulting in consistent voice characteristics
- Only produces WAV format audio files
- Requires a significant amount of memory for the SpeechT5 model
- First-time initialization may take longer as models are downloaded
- Currently only supports English text input 