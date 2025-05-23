#!/usr/bin/env python3
"""
Example: Dependency Injection

This example demonstrates how to use dependency injection in RusticAI agents.
"""

from rustic_ai.core.guild.builders import GuildBuilder, AgentBuilder
from rustic_ai.core.guild.agent_ext.depends.dependency_resolver import DependencySpec
from rustic_ai.core.agents.base import BaseAgent
from rustic_ai.ui_protocol.types import TextFormat
from pydantic import BaseModel
import logging


# Define a simple database interface
class Database:
    """A simple database interface."""
    
    def __init__(self, connection_string: str, max_connections: int = 10):
        self.connection_string = connection_string
        self.max_connections = max_connections
        self.data = {}
        print(f"Database initialized with connection string: {connection_string}")
    
    def save(self, key: str, value: str) -> None:
        """Save a value to the database."""
        self.data[key] = value
        print(f"Saved to database: {key} = {value}")
    
    def get(self, key: str) -> str:
        """Get a value from the database."""
        value = self.data.get(key, "NOT FOUND")
        print(f"Retrieved from database: {key} = {value}")
        return value


# Define a simple logger
class Logger:
    """A simple logger service."""
    
    def __init__(self, log_level: str = "INFO"):
        self.log_level = log_level
        print(f"Logger initialized with level: {log_level}")
    
    def log(self, message: str) -> None:
        """Log a message."""
        print(f"[LOG] {message}")


# Response model for our agent
class DataResponse(BaseModel):
    key: str
    value: str
    source: str


# Agent that uses dependency injection
class DatabaseAgent(BaseAgent):
    """An agent that uses a database dependency."""
    
    # These will be injected from the dependency map
    database: Database
    logger: Logger
    
    def __init__(self, database: Database, logger: Logger, **kwargs):
        super().__init__(**kwargs)
        self.database = database
        self.logger = logger
        self.logger.log(f"DatabaseAgent initialized: {self.id}")
    
    async def on_message(self, topic: str, message) -> None:
        """Handle incoming messages."""
        if isinstance(message, TextFormat):
            text = message.text if message.text else ""
            self.logger.log(f"Received message: {text}")
            
            # Parse as "GET key" or "SET key value"
            parts = text.split(maxsplit=2)
            
            if len(parts) >= 2 and parts[0].upper() == "GET":
                key = parts[1]
                self.logger.log(f"Getting value for key: {key}")
                value = self.database.get(key)
                
                # Send response
                response = DataResponse(
                    key=key,
                    value=value,
                    source="database" if value != "NOT FOUND" else "none"
                )
                await self.client.publish("user_message_broadcast", response)
            
            elif len(parts) >= 3 and parts[0].upper() == "SET":
                key = parts[1]
                value = parts[2]
                self.logger.log(f"Setting key {key} to value: {value}")
                self.database.save(key, value)
                
                # Send confirmation
                response = DataResponse(
                    key=key,
                    value=value,
                    source="user"
                )
                await self.client.publish("user_message_broadcast", response)
            
            else:
                self.logger.log("Invalid command. Use 'GET key' or 'SET key value'")
                await self.client.publish("user_message_broadcast", TextFormat(
                    text="Invalid command. Use 'GET key' or 'SET key value'"
                ))


def main():
    """Main function to create and run the guild with dependency injection."""
    
    # Create dependency specifications
    database_dependency = DependencySpec(
        class_name="__main__.Database",
        properties={
            "connection_string": "sqlite:///in-memory",
            "max_connections": 5
        }
    )
    
    logger_dependency = DependencySpec(
        class_name="__main__.Logger",
        properties={
            "log_level": "DEBUG"
        }
    )
    
    # Create a guild builder
    guild_builder = GuildBuilder(guild_name="DatabaseGuild") \
        .set_description("A guild with dependency injection") \
        .set_execution_engine("rustic_ai.core.guild.execution.sync.sync_exec_engine.SyncExecutionEngine") \
        .set_messaging(
            backend_module="rustic_ai.core.messaging.backend",
            backend_class="InMemoryMessagingBackend",
            backend_config={}
        )
    
    # Add dependencies to the guild
    guild_builder.add_dependency("database", database_dependency)
    guild_builder.add_dependency("logger", logger_dependency)
    
    # Create the database agent
    db_agent_spec = AgentBuilder(DatabaseAgent) \
        .set_id("db_agent") \
        .set_name("Database Agent") \
        .set_description("Provides access to the database") \
        .build_spec()
    
    # Add the agent to the guild
    guild_builder.add_agent_spec(db_agent_spec)
    
    # Launch the guild
    guild = guild_builder.launch()
    
    print(f"Guild '{guild.name}' launched with {guild.get_agent_count()} agent(s).")
    print("Available commands:")
    print("  SET key value - Store a value in the database")
    print("  GET key - Retrieve a value from the database")
    print("  exit - Quit the program")
    
    # Simple command loop
    while True:
        user_input = input("> ")
        if user_input.lower() == "exit":
            break
        
        # Send the user input to the guild
        guild.get_agent("db_agent").client.publish("default_topic", TextFormat(text=user_input))
    
    # Shutdown the guild when done
    guild.shutdown()
    print("Guild shut down.")


if __name__ == "__main__":
    main() 