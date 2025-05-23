# RusticAI Examples

This directory contains example code demonstrating how to use the RusticAI framework for building agent-based systems. These examples range from simple "hello world" implementations to more complex demos showcasing specific features of the framework.

## Directory Structure

- **`hello_world/`**: Basic introductory examples to get started with RusticAI
  - `hello_world_agent.py`: A simple standalone agent example
  - `hello_world_guild.py`: A simple guild with multiple interacting agents

- **`basic_agents/`**: Examples demonstrating core agent capabilities
  - `stateful_counter_agent.py`: Demonstrates state management in agents
  - `dependency_injection_example.py`: Shows how to use dependency injection

- **`demo_projects/`**: More complex examples showing real-world use cases
  - `simple_llm_agent.py`: Integration with LLM services

- **`guild_specs/`**: JSON specifications for various guild configurations
  - `simple_echo_guild.json`: Simple guild with an echo agent
  - `multi_agent_guild.json`: Complex guild with multiple agents and routing

## Running the Examples

Most examples can be run directly using Python:

```bash
# Ensure you have activated your virtual environment
# For example, using Poetry:
poetry shell

# Run a specific example
python examples/hello_world/hello_world_agent.py
```

### Prerequisites

Before running these examples, make sure you have:

1. Installed RusticAI and its dependencies
2. Activated your virtual environment
3. Required environment variables set (for examples that use external services)

### External Services

Some examples, like `simple_llm_agent.py`, may attempt to connect to external services. These examples typically include mock implementations for demonstration purposes, but can be modified to use actual services by:

1. Uncommenting the relevant sections in the code
2. Setting required API keys as environment variables
3. Installing any additional required dependencies

## Learning Path

If you're new to RusticAI, we recommend exploring the examples in this order:

1. `hello_world/hello_world_agent.py` - Understand the basics of agents
2. `hello_world/hello_world_guild.py` - Learn how agents interact within a guild
3. `basic_agents/stateful_counter_agent.py` - Explore state management
4. `basic_agents/dependency_injection_example.py` - Understand dependency injection
5. `guild_specs/*.json` - Learn how to configure guilds using specifications
6. `demo_projects/` - See more complex, real-world implementations

## Related Documentation

For more detailed explanations and guides, refer to the following documentation:

- [Creating Your First Agent](../docs/howto/creating_your_first_agent.md)
- [Creating a Guild](../docs/howto/creating_a_guild.md)
- [State Management](../docs/howto/state_management.md)
- [Dependency Injection](../docs/howto/dependency_injection.md)
- [Testing Agents](../docs/howto/testing_agents.md)

## Contribution

Feel free to contribute your own examples by submitting a pull request. When adding examples, please:

1. Follow the existing directory structure
2. Include comprehensive comments explaining the code
3. Ensure the example demonstrates a specific feature or use case
4. Update this README to include your example

## License

These examples are provided under the same license as the RusticAI framework. 