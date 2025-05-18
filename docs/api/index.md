# RusticAI API Reference

Welcome to the API reference documentation for RusticAI. This section provides detailed information about the public API interfaces available for interacting with the RusticAI framework.

## Overview

The RusticAI API allows you to:

- Create and manage guilds and agents programmatically
- Interact with existing agent systems
- Build integrations with external services
- Monitor and control RusticAI deployments

## API Categories

- **Core API** - Essential interfaces for creating and managing multi-agent systems
- **Client API** - Utilities for interacting with RusticAI guilds from external applications
- **Management API** - Administrative interfaces for monitoring and controlling deployments
- **Extension API** - Interfaces for extending and customizing RusticAI components

## Usage Examples

```python
# Example: Creating a guild using the API
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.guild.dsl import GuildSpec

# Build guild specification
guild_spec = GuildBuilder(guild_name="ExampleGuild") \
    .set_description("An example guild created via API") \
    .build_spec()

# Instantiate and launch the guild
guild = guild_spec.instantiate()
```

## API Reference

Comprehensive documentation for each API component is currently under development. Please check back for updates, or refer to the code repository for the most up-to-date information. 