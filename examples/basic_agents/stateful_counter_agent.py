#!/usr/bin/env python
"""
Stateful Counter Agent Example

This example demonstrates how to create an agent that maintains state across messages
using RusticAI's state management capabilities.

Run this example with:
    python examples/basic_agents/stateful_counter_agent.py
"""

import asyncio
from pydantic import BaseModel

from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.builders import AgentBuilder, GuildBuilder
from rustic_ai.core.guild.dsl import AgentSpec, BaseAgentProps, GuildTopics
from rustic_ai.core.agents.testutils.probe_agent import ProbeAgent
from rustic_ai.core.state.models import StateOwner, StateUpdateFormat, StateUpdateRequest


class CounterAgentProps(BaseAgentProps):
    """Properties for the CounterAgent."""
    initial_count: int = 0
    increment_by: int = 1


class IncrementRequest(BaseModel):
    """Request to increment the counter."""
    increment_by: int = 1
    get_current: bool = True


class CounterResponse(BaseModel):
    """Response with the current counter value."""
    count: int
    times_incremented: int


class CounterAgent(Agent[CounterAgentProps]):
    """
    An agent that maintains a counter in its state.
    
    This agent demonstrates:
    1. Using a custom properties class
    2. Reading properties from the agent spec
    3. Maintaining state using StateUpdateRequest
    4. Responding with the current state
    """

    def __init__(self, agent_spec: AgentSpec[CounterAgentProps]):
        super().__init__(agent_spec)
        # Initialize member variables from props
        self.increment_by = agent_spec.props.increment_by
        self.times_incremented = 0
        
        # Initialize state - note we don't directly modify self._state
        # Instead, we'll use the appropriate state update mechanism
        print(f"CounterAgent initialized with ID: {self.id}")
        print(f"Initial increment_by: {self.increment_by}")

    @agent.processor(clz=IncrementRequest)
    def increment_counter(self, ctx: agent.ProcessContext[IncrementRequest]):
        """
        Increment the counter and optionally return the current value.
        Demonstrates state management by updating the agent's state.
        """
        # Get the increment value from the request or use the default
        increment_by = ctx.payload.increment_by if ctx.payload.increment_by else self.increment_by
        get_current = ctx.payload.get_current
        
        # Get current count from state or use 0 if not present
        current_count = self._state.get("count", 0)
        
        # Calculate new count
        new_count = current_count + increment_by
        self.times_incremented += 1
        
        print(f"[{self.name}] Incrementing counter by {increment_by} to {new_count}")
        print(f"[{self.name}] Times incremented: {self.times_incremented}")
        
        # Update state using StateUpdateRequest
        self.update_state(
            ctx=ctx,
            update_format=StateUpdateFormat.MERGE_DICT,
            update={
                "count": new_count,
                "times_incremented": self.times_incremented
            }
        )
        
        # Respond with current count if requested
        if get_current:
            ctx.send(CounterResponse(
                count=new_count,
                times_incremented=self.times_incremented
            ))


async def main():
    # Create and launch a guild
    guild = GuildBuilder("counter_guild", "Counter Guild", "A guild with a stateful counter agent") \
        .launch(add_probe=True)
    
    # Get the probe agent for monitoring messages
    probe_agent = guild.get_agent_of_type(ProbeAgent)
    print(f"Created guild with ID: {guild.id}")
    
    # Create and launch a counter agent
    counter_agent_spec = AgentBuilder(CounterAgent) \
        .set_name("Counter") \
        .set_description("A stateful counter agent") \
        .set_properties(CounterAgentProps(initial_count=0, increment_by=5)) \
        .build_spec()
    
    guild.launch_agent(counter_agent_spec)
    
    print("\nAgents in the guild:")
    for agent_spec in guild.list_agents():
        print(f"- {agent_spec.name} (ID: {agent_spec.id}, Type: {agent_spec.class_name})")
    
    # Send increment requests with the probe agent
    print("\nSending increment requests...")
    
    # First increment
    print("\n--- First Increment ---")
    probe_agent.publish("default_topic", IncrementRequest())
    await asyncio.sleep(1)  # Wait for processing
    
    # Check messages
    messages = probe_agent.get_messages()
    print(f"Captured {len(messages)} message(s):")
    for msg in messages:
        if "count" in msg.payload:
            print(f"Count: {msg.payload['count']}, Times incremented: {msg.payload['times_incremented']}")
    
    # Clear messages for next round
    probe_agent.clear_messages()
    
    # Second increment with custom value
    print("\n--- Second Increment (custom value: 10) ---")
    probe_agent.publish("default_topic", IncrementRequest(increment_by=10))
    await asyncio.sleep(1)  # Wait for processing
    
    # Check messages again
    messages = probe_agent.get_messages()
    print(f"Captured {len(messages)} message(s):")
    for msg in messages:
        if "count" in msg.payload:
            print(f"Count: {msg.payload['count']}, Times incremented: {msg.payload['times_incremented']}")
    
    # Shutdown the guild
    guild.shutdown()
    print("\nGuild shutdown complete")


if __name__ == "__main__":
    asyncio.run(main()) 