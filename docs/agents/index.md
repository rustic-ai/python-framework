# RusticAI Agents Documentation

Welcome to the RusticAI Agents documentation. This section provides detailed information about the agents available in the RusticAI framework.

## What is an Agent?

In RusticAI, an agent is a specialized component that performs specific tasks within a guild (multi-agent system). Each agent:

- Processes specific types of messages
- Maintains its own state
- Can interact with external services
- Communicates with other agents through a message-based system

## Available Agents

RusticAI includes several specialized agents for various tasks:

### Web and API Agents
- [PlaywrightScraperAgent](playwright/playwright_scraper_agent.md) - Web scraping using Playwright
- [SERPAgent](serpapi/serp_agent.md) - Search engine results via SerpAPI

### Language Model Agents
- [LiteLLMAgent](litellm/litellm_agent.md) - Interface to various LLMs via LiteLLM
- [SimpleLLMAgent](core/simple_llm_agent.md) - Basic LLM agent implementation
- [LLMPhiAgent](huggingface/llm_phi_agent.md) - Interface to Phi-2 language model

### AI Media Generation
- [RunwaymlStableDiffusionAgent](huggingface/runwayml_stable_diffusion_agent.md) - Image generation using Stable Diffusion
- [Image2ImageAgent](huggingface/image2image_agent.md) - Image-to-image transformation with Pix2Pix
- [SpeechT5TTSAgent](huggingface/speecht5_tts_agent.md) - Text-to-speech synthesis

### NLP Agents
- [SquadAgent](huggingface/squad_agent.md) - Question answering using the SQuAD model
- [MarvinAgent](marvin/marvin_agent.md) - Classification and data extraction

### Utility Agents
- [VectorAgent](core/vector_agent.md) - Document indexing and similarity search
- [ProbeAgent](core/probe_agent.md) - Testing utility for monitoring agent interactions

### System Agents
- [UserProxyAgent](core/user_proxy_agent.md) - Interface between users and the guild
- [GuildManagerAgent](core/guild_manager_agent.md) - Manages guild state and operations

## Creating Custom Agents

For guidance on creating your own agents, see the [Creating Your First Agent](../howto/creating_your_first_agent.md) guide. 