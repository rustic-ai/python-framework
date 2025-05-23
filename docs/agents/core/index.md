# Core Agents

RusticAI provides several built-in agents as part of the core package. These agents serve as foundational components for building more complex agent systems or can be used directly in your applications.

## Available Core Agents

- [GuildManagerAgent](guild_manager_agent.md) - A system agent that manages the lifecycle of guilds and their agents
- [UserProxyAgent](user_proxy_agent.md) - Represents human users within the agent ecosystem
- [VectorAgent](vector_agent.md) - Provides vector operations for semantic search and retrieval
- [SimpleLLMAgent](simple_llm_agent.md) - A basic agent for integrating with language models
- [ProbeAgent](probe_agent.md) - A utility agent for testing and monitoring

## Using Core Agents

Core agents can be incorporated into your guild directly by referencing their class paths in your guild specification. They provide essential functionality that many applications need out of the box.

For custom use cases, these agents can serve as examples or be extended to create more specialized behavior.

See the individual agent documentation pages for detailed information on each agent's capabilities and configuration options. 