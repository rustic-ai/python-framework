#!/usr/bin/env python3
"""
Example: Stateful Counter Agent

This example demonstrates how to create an agent that maintains state across messages.
"""

from rustic_ai.core.guild.builders import GuildBuilder, AgentBuilder
from rustic_ai.core.agents.base import BaseAgent
from rustic_ai.ui_protocol.types import TextFormat
from pydantic import BaseModel
from typing import Dict, List, Optional


# Define message models
class CounterRequest(BaseModel):
    """Request to manipulate a counter."""
    action: str  # "increment", "decrement", "reset", or "get"
    counter_name: str = "default"
    amount: int = 1


class CounterResponse(BaseModel):
    """Response with counter information."""
    counter_name: str
    value: int
    previous_value: Optional[int] = None
    action: str


# Define a stateful agent
class CounterAgent(BaseAgent):
    """An agent that maintains counters in its state."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize agent state
        self.counters: Dict[str, int] = {}
        print(f"CounterAgent initialized: {self.id}")
    
    def get_counter(self, name: str) -> int:
        """Get the current value of a counter, initializing it if needed."""
        if name not in self.counters:
            self.counters[name] = 0
        return self.counters[name]
    
    def set_counter(self, name: str, value: int) -> None:
        """Set a counter to a specific value."""
        self.counters[name] = value
    
    def increment_counter(self, name: str, amount: int = 1) -> int:
        """Increment a counter by the specified amount."""
        current = self.get_counter(name)
        self.counters[name] = current + amount
        return current
    
    def reset_counter(self, name: str) -> int:
        """Reset a counter to zero."""
        current = self.get_counter(name)
        self.counters[name] = 0
        return current
    
    async def on_message(self, topic: str, message) -> None:
        """Handle incoming messages."""
        if isinstance(message, TextFormat):
            await self.handle_text_command(message.text if message.text else "")
        elif isinstance(message, CounterRequest):
            await self.handle_counter_request(message)
    
    async def handle_text_command(self, text: str) -> None:
        """Parse and handle text commands."""
        parts = text.strip().split()
        
        if not parts:
            await self.client.publish("user_message_broadcast", TextFormat(
                text="Available commands: INCREMENT [name] [amount], DECREMENT [name] [amount], RESET [name], GET [name], LIST"
            ))
            return
        
        command = parts[0].upper()
        
        if command == "INCREMENT":
            name = parts[1] if len(parts) > 1 else "default"
            amount = int(parts[2]) if len(parts) > 2 else 1
            
            prev_value = self.increment_counter(name, amount)
            current = self.get_counter(name)
            
            await self.client.publish("user_message_broadcast", CounterResponse(
                counter_name=name,
                value=current,
                previous_value=prev_value,
                action="increment"
            ))
        
        elif command == "DECREMENT":
            name = parts[1] if len(parts) > 1 else "default"
            amount = int(parts[2]) if len(parts) > 2 else 1
            
            prev_value = self.increment_counter(name, -amount)
            current = self.get_counter(name)
            
            await self.client.publish("user_message_broadcast", CounterResponse(
                counter_name=name,
                value=current,
                previous_value=prev_value,
                action="decrement"
            ))
        
        elif command == "RESET":
            name = parts[1] if len(parts) > 1 else "default"
            prev_value = self.reset_counter(name)
            
            await self.client.publish("user_message_broadcast", CounterResponse(
                counter_name=name,
                value=0,
                previous_value=prev_value,
                action="reset"
            ))
        
        elif command == "GET":
            name = parts[1] if len(parts) > 1 else "default"
            value = self.get_counter(name)
            
            await self.client.publish("user_message_broadcast", CounterResponse(
                counter_name=name,
                value=value,
                action="get"
            ))
        
        elif command == "LIST":
            counter_list = [f"{name}: {value}" for name, value in self.counters.items()]
            if not counter_list:
                counter_list = ["No counters defined"]
            
            await self.client.publish("user_message_broadcast", TextFormat(
                text="Counters:\n" + "\n".join(counter_list)
            ))
        
        else:
            await self.client.publish("user_message_broadcast", TextFormat(
                text=f"Unknown command: {command}\nAvailable commands: INCREMENT, DECREMENT, RESET, GET, LIST"
            ))
    
    async def handle_counter_request(self, request: CounterRequest) -> None:
        """Handle structured counter requests."""
        action = request.action.lower()
        name = request.counter_name
        
        if action == "increment":
            prev_value = self.increment_counter(name, request.amount)
            current = self.get_counter(name)
            
            await self.client.publish("user_message_broadcast", CounterResponse(
                counter_name=name,
                value=current,
                previous_value=prev_value,
                action="increment"
            ))
        
        elif action == "decrement":
            prev_value = self.increment_counter(name, -request.amount)
            current = self.get_counter(name)
            
            await self.client.publish("user_message_broadcast", CounterResponse(
                counter_name=name,
                value=current,
                previous_value=prev_value,
                action="decrement"
            ))
        
        elif action == "reset":
            prev_value = self.reset_counter(name)
            
            await self.client.publish("user_message_broadcast", CounterResponse(
                counter_name=name,
                value=0,
                previous_value=prev_value,
                action="reset"
            ))
        
        elif action == "get":
            value = self.get_counter(name)
            
            await self.client.publish("user_message_broadcast", CounterResponse(
                counter_name=name,
                value=value,
                action="get"
            ))
        
        else:
            await self.client.publish("user_message_broadcast", TextFormat(
                text=f"Unknown action: {action}"
            ))


def main():
    """Main function to create and run a guild with the counter agent."""
    
    # Create a guild builder
    guild_builder = GuildBuilder(guild_name="CounterGuild") \
        .set_description("A guild with a stateful counter agent") \
        .set_execution_engine("rustic_ai.core.guild.execution.sync.sync_exec_engine.SyncExecutionEngine") \
        .set_messaging(
            backend_module="rustic_ai.core.messaging.backend",
            backend_class="InMemoryMessagingBackend",
            backend_config={}
        )
    
    # Create the counter agent
    counter_agent_spec = AgentBuilder(CounterAgent) \
        .set_id("counter_agent") \
        .set_name("Counter Agent") \
        .set_description("Maintains counters with state") \
        .build_spec()
    
    # Add the agent to the guild
    guild_builder.add_agent_spec(counter_agent_spec)
    
    # Launch the guild
    guild = guild_builder.launch()
    
    print(f"Guild '{guild.name}' launched with {guild.get_agent_count()} agent(s).")
    print("Available commands:")
    print("  INCREMENT [name] [amount] - Increment a counter")
    print("  DECREMENT [name] [amount] - Decrement a counter")
    print("  RESET [name] - Reset a counter to zero")
    print("  GET [name] - Get the current value of a counter")
    print("  LIST - List all counters and their values")
    print("  exit - Quit the program")
    
    # Simple command loop
    while True:
        user_input = input("> ")
        if user_input.lower() == "exit":
            break
        
        # Send the user input to the guild
        guild.get_agent("counter_agent").client.publish("default_topic", TextFormat(text=user_input))
    
    # Shutdown the guild when done
    guild.shutdown()
    print("Guild shut down.")


if __name__ == "__main__":
    main() 