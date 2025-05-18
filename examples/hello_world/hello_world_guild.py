#!/usr/bin/env python3
"""
Example: Hello World Guild

This example demonstrates how to create a simple guild with a hello world agent.
"""

from rustic_ai.core.guild.builders import GuildBuilder, AgentBuilder
from rustic_ai.agents.utils.user_proxy_agent import UserProxyAgent
from rustic_ai.core.agents.base import BaseAgent
from rustic_ai.ui_protocol.types import TextFormat
from pydantic import BaseModel


# Define a simple HelloWorldAgent
class HelloResponse(BaseModel):
    greeting: str
    recipient: str


class HelloWorldAgent(BaseAgent):
    """A simple agent that responds with a greeting."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    async def on_message(self, topic: str, message) -> None:
        """Handle incoming messages."""
        if isinstance(message, TextFormat):
            # If we receive a text message, respond with a greeting
            response = HelloResponse(
                greeting="Hello",
                recipient=message.text if message.text else "World"
            )
            await self.client.publish("user_message_broadcast", response)


def main():
    """Main function to create and run the hello world guild."""
    
    # Create a guild builder
    guild_builder = GuildBuilder(guild_name="HelloWorldGuild") \
        .set_description("A simple hello world guild") \
        .set_execution_engine("rustic_ai.core.guild.execution.sync.sync_exec_engine.SyncExecutionEngine") \
        .set_messaging(
            backend_module="rustic_ai.core.messaging.backend",
            backend_class="InMemoryMessagingBackend",
            backend_config={}
        )
    
    # Create a user proxy agent to handle user interaction
    user_agent_spec = AgentBuilder(UserProxyAgent) \
        .set_id("user_agent") \
        .set_name("User Interface") \
        .set_description("Handles user interactions") \
        .build_spec()
    
    # Create our hello world agent
    hello_agent_spec = AgentBuilder(HelloWorldAgent) \
        .set_id("hello_agent") \
        .set_name("Hello World Agent") \
        .set_description("Responds with greetings") \
        .build_spec()
    
    # Add the agents to the guild
    guild_builder.add_agent_spec(user_agent_spec)
    guild_builder.add_agent_spec(hello_agent_spec)
    
    # Launch the guild
    guild = guild_builder.launch()
    
    print(f"Guild '{guild.name}' launched with {guild.get_agent_count()} agent(s).")
    print("Type a name to receive a greeting, or 'exit' to quit.")
    
    # Simple command loop
    while True:
        user_input = input("> ")
        if user_input.lower() == "exit":
            break
        
        # Send the user input to the guild
        guild.get_agent("user_agent").client.publish("default_topic", TextFormat(text=user_input))
    
    # Shutdown the guild when done
    guild.shutdown()
    print("Guild shut down.")


if __name__ == "__main__":
    main() 