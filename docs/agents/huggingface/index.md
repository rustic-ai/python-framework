# HuggingFace Agents

This section contains documentation for RusticAI's HuggingFace integration, which provides access to various AI models from the Hugging Face ecosystem.

## Available Agents

- [LLMPhiAgent](llm_phi_agent.md) - Interface to Microsoft's Phi-2 language model
- [RunwaymlStableDiffusionAgent](runwayml_stable_diffusion_agent.md) - Image generation using Stable Diffusion
- [Image2ImageAgent](image2image_agent.md) - Image-to-image transformation with Pix2Pix
- [SpeechT5TTSAgent](speecht5_tts_agent.md) - Text-to-speech synthesis
- [SquadAgent](squad_agent.md) - Question answering using the SQuAD model

## Overview

HuggingFace agents enable seamless integration with the HuggingFace ecosystem, allowing you to incorporate state-of-the-art AI models into your RusticAI applications. These agents cover a wide range of capabilities, from text generation and question answering to image creation and speech synthesis.

## Use Cases

- Text generation using language models
- Image generation and manipulation
- Speech synthesis from text
- Question answering from context
- Multi-modal AI applications
- Local model inference (where supported)

## Getting Started

To use HuggingFace agents, you'll need:

1. The appropriate HuggingFace libraries installed in your environment
2. Sufficient hardware resources for models running locally
3. A HuggingFace API key for remote inference (when applicable)
4. Proper configuration of the respective agent in your guild

Refer to the individual agent documentation for detailed implementation instructions. 