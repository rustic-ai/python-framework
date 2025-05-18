#!/usr/bin/env python
"""
Hello World Guild Example

This example demonstrates how to create a guild with multiple agents that interact with each other.

Run this example with:
    python examples/hello_world/hello_world_guild.py
"""

import asyncio
import time
from pydantic import BaseModel

from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.builders import AgentBuilder, GuildBuilder
from rustic_ai.core.guild.dsl import AgentSpec, BaseAgentProps
from rustic_ai.core.agents.testutils.probe_agent import ProbeAgent


class GreetRequest(BaseModel):
    """A simple model for greeting requests."""
    name: str


class GreetResponse(BaseModel):
    """A model for greeting responses."""
    greeting: str


class HelloAgent(Agent[BaseAgentProps]):
    """An agent that responds to greeting requests."""

    def __init__(self, agent_spec: AgentSpec[BaseAgentProps]):
        super().__init__(agent_spec)
        print(f"HelloAgent initialized with ID: {self.id}")

    @agent.processor(clz=GreetRequest)
    def greet(self, ctx: agent.ProcessContext[GreetRequest]):
        """Process a greeting request and respond with a greeting."""
        name = ctx.payload.name
        print(f"[{self.name}] Received greeting request for: {name}")
        
        # Create and send a response
        response = GreetResponse(greeting=f"Hello, {name}!")
        ctx.send(response)
        print(f"[{self.name}] Sent response: {response.greeting}")


class EchoAgent(Agent[BaseAgentProps]):
    """An agent that echoes back any greeting responses it receives."""

    def __init__(self, agent_spec: AgentSpec[BaseAgentProps]):
        super().__init__(agent_spec)
        print(f"EchoAgent initialized with ID: {self.id}")

    @agent.processor(clz=GreetResponse)
    def echo_greeting(self, ctx: agent.ProcessContext[GreetResponse]):
        """Echo back a greeting response."""
        greeting = ctx.payload.greeting
        print(f"[{self.name}] Received greeting: {greeting}")
        print(f"[{self.name}] Echoing back: {greeting} (Echo!)")
        
        # Send a new greeting request with the original message
        ctx.send(GreetRequest(name=f"{greeting} (Echo!)"))


async def main():
    # Create and launch a guild
    guild = GuildBuilder("hello_world_guild", "Hello World Guild", "A simple guild for demonstration") \
        .launch(add_probe=True)
    
    # Get the probe agent for monitoring messages
    probe_agent = guild.get_agent_of_type(ProbeAgent)
    print(f"Created guild with ID: {guild.id}")
    
    # Create and launch our agents
    hello_agent_spec = AgentBuilder(HelloAgent) \
        .set_name("Greeter") \
        .set_description("An agent that responds to greeting requests") \
        .build_spec()
    
    echo_agent_spec = AgentBuilder(EchoAgent) \
        .set_name("Echo") \
        .set_description("An agent that echoes back greetings") \
        .build_spec()
    
    guild.launch_agent(hello_agent_spec)
    guild.launch_agent(echo_agent_spec)
    
    print("\nAgents in the guild:")
    for agent_spec in guild.list_agents():
        print(f"- {agent_spec.name} (ID: {agent_spec.id}, Type: {agent_spec.class_name})")
    
    # Send an initial greeting request using the probe agent
    print("\nSending initial greeting request...")
    probe_agent.publish("default_topic", GreetRequest(name="World"))
    
    # Wait for messages to be processed
    print("\nWaiting for messages to be processed...")
    
    # Sleep for 2 seconds to allow messages to be processed
    # In a real application, you would use a more robust synchronization method
    await asyncio.sleep(2)
    
    # Print all messages captured by the probe
    messages = probe_agent.get_messages()
    print(f"\nCaptured {len(messages)} messages:")
    for i, msg in enumerate(messages, 1):
        print(f"\nMessage {i}:")
        print(f"  From: {msg.sender.name} ({msg.sender.id})")
        print(f"  Format: {msg.format}")
        if "greeting" in msg.payload:
            print(f"  Payload: {msg.payload['greeting']}")
        elif "name" in msg.payload:
            print(f"  Payload: {msg.payload['name']}")

    # Shutdown the guild
    guild.shutdown()
    print("\nGuild shutdown complete")


if __name__ == "__main__":
    asyncio.run(main()) 