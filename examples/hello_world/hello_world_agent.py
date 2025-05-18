#!/usr/bin/env python
"""
Hello World Agent Example

This example demonstrates a simple agent that processes greeting messages.

Run this example with:
    python examples/hello_world/hello_world_agent.py
"""

from pydantic import BaseModel

from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.dsl import AgentSpec, BaseAgentProps
from rustic_ai.core.messaging.core import JsonDict
from rustic_ai.core.messaging.core.message import Message, AgentTag
from rustic_ai.core.utils.priority import Priority
from rustic_ai.core.utils.gemstone_id import GemstoneGenerator


class GreetRequest(BaseModel):
    """A simple model for greeting requests."""
    name: str


class GreetResponse(BaseModel):
    """A model for greeting responses."""
    greeting: str


class HelloWorldAgent(Agent[BaseAgentProps]):
    """A simple agent that responds to greeting requests."""

    def __init__(self, agent_spec: AgentSpec):
        super().__init__(agent_spec)
        print(f"Hello World Agent initialized with ID: {self.id} and name: {self.name}")

    @agent.processor(clz=GreetRequest)
    def greet(self, ctx: agent.ProcessContext[GreetRequest]):
        """Process a greeting request and respond with a greeting."""
        name = ctx.payload.name
        print(f"Received greeting request for: {name}")
        
        # Create and send a response
        response = GreetResponse(greeting=f"Hello, {name}!")
        ctx.send(response)
        print(f"Sent response: {response.greeting}")

    @agent.processor(clz=JsonDict)
    def greet_from_dict(self, ctx: agent.ProcessContext[JsonDict]):
        """Handle a raw JSON greeting."""
        raw_payload = ctx.payload
        if "name" in raw_payload:
            name = raw_payload["name"]
            print(f"Received raw JSON greeting request for: {name}")
            ctx.send_dict({"greeting": f"Hello, {name}!"})
            print(f"Sent raw JSON response: Hello, {name}!")


if __name__ == "__main__":
    # Create a simple generator for message IDs
    gemstone_gen = GemstoneGenerator(machine_id=1)
    
    # Create the agent
    hello_agent = HelloWorldAgent(
        AgentSpec(
            id="hello_agent",
            name="Hello World Agent",
            description="A simple agent that responds to greetings",
            class_name=HelloWorldAgent.get_qualified_class_name(),
        )
    )
    
    # Create a message with a GreetRequest payload
    message = Message(
        id_obj=gemstone_gen.get_id(Priority.NORMAL),
        topics=["test_topic"],
        sender=AgentTag(id="test_sender", name="Test Sender"),
        payload=GreetRequest(name="World").model_dump(),
        format=GreetRequest.model_json_schema()["$id"],
    )
    
    # Process the message
    print("\nSending structured message...")
    hello_agent._on_message(message)
    
    # Create a message with a raw JSON payload
    raw_message = Message(
        id_obj=gemstone_gen.get_id(Priority.NORMAL),
        topics=["test_topic"],
        sender=AgentTag(id="test_sender", name="Test Sender"),
        payload={"name": "JSON World"},
        format="rustic_ai.core.messaging.core.JsonDict",  # Format for raw JSON
    )
    
    # Process the raw message
    print("\nSending raw JSON message...")
    hello_agent._on_message(raw_message) 