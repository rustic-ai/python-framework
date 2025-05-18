#!/usr/bin/env python3
"""
Example: Hello World Agent

This example demonstrates how to create a simple agent that responds with greetings.
"""

from rustic_ai.core.agents.base import BaseAgent
from rustic_ai.ui_protocol.types import TextFormat
from pydantic import BaseModel


# Define a response model for our agent
class HelloResponse(BaseModel):
    greeting: str
    recipient: str


class HelloWorldAgent(BaseAgent):
    """A simple agent that responds with a greeting."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.greeting_count = 0  # Track how many greetings we've sent
        print(f"HelloWorldAgent initialized: {self.id}")

    async def on_message(self, topic: str, message) -> None:
        """Handle incoming messages."""
        if isinstance(message, TextFormat):
            # If we receive a text message, respond with a greeting
            self.greeting_count += 1
            recipient = message.text if message.text else "World"
            
            print(f"Received message: {message.text}")
            print(f"Sending greeting #{self.greeting_count}")
            
            response = HelloResponse(
                greeting="Hello",
                recipient=recipient
            )
            await self.client.publish("user_message_broadcast", response)


# Example of how to use this agent in a guild
def usage_example():
    """Example code showing how to use the HelloWorldAgent."""
    from rustic_ai.core.guild.builders import GuildBuilder, AgentBuilder
    
    # Create a guild builder
    guild_builder = GuildBuilder(guild_name="HelloWorldGuild") \
        .set_description("A simple hello world guild")
    
    # Create our hello world agent
    hello_agent_spec = AgentBuilder(HelloWorldAgent) \
        .set_id("hello_agent") \
        .set_name("Hello World Agent") \
        .set_description("Responds with greetings") \
        .build_spec()
    
    # Add the agent to the guild
    guild_builder.add_agent_spec(hello_agent_spec)
    
    # Launch the guild
    guild = guild_builder.launch()
    
    # Now you can send messages to the agent
    # guild.get_agent("hello_agent").client.publish(
    #     "default_topic", TextFormat(text="User")
    # )
    
    # Shutdown the guild when done
    # guild.shutdown()


if __name__ == "__main__":
    print("This file defines the HelloWorldAgent class.")
    print("It is meant to be imported and used in a guild, not run directly.")
    print("\nHere's how you might use it:")
    print("""
    from rustic_ai.core.guild.builders import GuildBuilder, AgentBuilder
    from hello_world_agent import HelloWorldAgent
    
    # Create a guild builder
    guild_builder = GuildBuilder(guild_name="HelloWorldGuild")
    
    # Create our hello world agent
    hello_agent_spec = AgentBuilder(HelloWorldAgent) \\
        .set_id("hello_agent") \\
        .set_name("Hello World Agent") \\
        .build_spec()
    
    # Add the agent to the guild
    guild_builder.add_agent_spec(hello_agent_spec)
    
    # Launch the guild
    guild = guild_builder.launch()
    """) 