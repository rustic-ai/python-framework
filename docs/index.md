# RusticAI Documentation

Welcome to the official documentation for RusticAI, a powerful framework for building intelligent multi-agent systems in Python. RusticAI provides a flexible, modular architecture for creating, deploying, and managing AI agents that can work together to solve complex problems.

## What is RusticAI?

RusticAI is designed to simplify the development of agent-based systems by providing:

- **Guild-based Architecture**: Organize agents into cohesive groups called "guilds" that work together toward common goals
- **Dependency Injection**: Easily configure and manage the resources your agents need
- **State Management**: Robust mechanisms for handling agent state across interactions
- **Message Passing**: Standardized communication between agents
- **Extensibility**: A plugin-based system that makes it easy to integrate with external services and AI providers

Whether you're building a simple conversational assistant or a complex multi-agent system with specialized roles, RusticAI provides the infrastructure you need to focus on your application logic rather than agent coordination.

## Getting Started

New to RusticAI? Here are the best places to begin:

- [Core Concepts](core/index.md): Learn about the foundational architecture and concepts
- [Creating Your First Agent](howto/creating_your_first_agent.md): A step-by-step guide to building your first agent
- [Creating a Guild](howto/creating_a_guild.md): Learn how to organize multiple agents to work together

## Core Components

RusticAI is built around these core components:

- [Agents](agents/index.md): The building blocks of intelligent systems that can perceive, reason, and act
- [Guilds](core/guilds.md): Organized collections of agents working together toward common goals
- [Messaging](core/messaging.md): Communication infrastructure for agents to exchange information
- [Execution](core/execution.md): How agent code gets executed within the RusticAI framework
- [State Management](core/state_management.md): Managing persistence across agent interactions
- [Dependencies](dependencies/index.md): Resources and services that agents can access through dependency injection

## Integrations

RusticAI integrates with popular AI tools and services:

- [LiteLLM](agents/litellm/index.md): Unified interface for various LLM providers
- [HuggingFace](agents/huggingface/index.md): Leverage HuggingFace models for text, image, and speech processing
- [Playwright](agents/playwright/index.md): Web automation and scraping capabilities
- [SerpAPI](agents/serpapi/index.md): Web search integration for information retrieval
- [Marvin](agents/marvin/index.md): AI function calling and structured extraction
- [Ray](ray/index.md): Distributed and parallel execution
- [Chroma](dependencies/chroma/index.md): Vector database for semantic search
- [Redis](dependencies/redis/index.md): Fast key-value storage for agent state
- [LangChain](dependencies/langchain/index.md): Utilities for working with language models

## API Reference

For detailed API information, check out the [API Reference](api/index.md) which provides comprehensive documentation of all public interfaces.

## Showcase

Explore [Example Applications](showcase/index.md) to see RusticAI in action and get inspiration for your own projects.

## Contributing

RusticAI is an open-source project, and contributions are welcome! See our [Contributing Guide](contributing.md) to learn how you can help improve the framework. 