#!/usr/bin/env python
"""
Dependency Injection Example

This example demonstrates how to use dependency injection in agents.
It shows how to:
1. Create a dependency resolver
2. Configure dependencies in an AgentSpec
3. Inject dependencies into agent message handlers

Run this example with:
    python examples/basic_agents/dependency_injection_example.py
"""

import asyncio
from pydantic import BaseModel
from typing import Dict, Any, List

from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.builders import AgentBuilder, GuildBuilder
from rustic_ai.core.guild.dsl import AgentSpec, BaseAgentProps, DependencySpec
from rustic_ai.core.guild.agent_ext.depends.dependency_resolver import DependencyResolver
from rustic_ai.core.agents.testutils.probe_agent import ProbeAgent


# ==== Sample External Services =====

class DatabaseService:
    """A mock database service."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.data = {}
        print(f"DatabaseService initialized with connection: {connection_string}")
    
    def save(self, key: str, value: Any) -> None:
        """Save data to the 'database'."""
        self.data[key] = value
        print(f"DB: Saved {key}={value}")
    
    def get(self, key: str) -> Any:
        """Get data from the 'database'."""
        value = self.data.get(key, None)
        print(f"DB: Retrieved {key}={value}")
        return value


class ApiService:
    """A mock API service."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        print(f"ApiService initialized with key: {api_key} and URL: {base_url}")
    
    def call_api(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate an API call."""
        print(f"API: Calling {endpoint} with {data}")
        return {"endpoint": endpoint, "input": data, "result": "success"}


# ==== Dependency Resolvers =====

class DatabaseResolver(DependencyResolver):
    """Resolver for the DatabaseService dependency."""
    
    def __init__(self, connection_string: str = "memory://default"):
        self.connection_string = connection_string
        self._db_instance = None
    
    def resolve(self, guild_id: str, agent_id: str = None) -> DatabaseService:
        """Resolve the database service."""
        if self._db_instance is None:
            self._db_instance = DatabaseService(self.connection_string)
        return self._db_instance


class ApiServiceResolver(DependencyResolver):
    """Resolver for the ApiService dependency."""
    
    def __init__(self, api_key: str = "default_key", base_url: str = "https://api.example.com"):
        self.api_key = api_key
        self.base_url = base_url
        self._api_instance = None
    
    def resolve(self, guild_id: str, agent_id: str = None) -> ApiService:
        """Resolve the API service."""
        if self._api_instance is None:
            self._api_instance = ApiService(self.api_key, self.base_url)
        return self._api_instance


# ==== Message Models =====

class DataRequest(BaseModel):
    """A request to save or retrieve data."""
    action: str  # "save" or "get"
    key: str
    value: Any = None


class ApiRequest(BaseModel):
    """A request to call an API."""
    endpoint: str
    data: Dict[str, Any]


class Response(BaseModel):
    """A generic response."""
    success: bool
    message: str
    data: Any = None


# ==== Agent Implementation =====

class DependencyInjectionAgent(Agent[BaseAgentProps]):
    """
    An agent that demonstrates dependency injection.
    
    This agent has two handlers:
    1. handle_data_request - uses a database dependency
    2. handle_api_request - uses an API service dependency
    """
    
    def __init__(self, agent_spec: AgentSpec[BaseAgentProps]):
        super().__init__(agent_spec)
        print(f"DependencyInjectionAgent initialized with ID: {self.id}")
    
    @agent.processor(clz=DataRequest, depends_on=["database"])
    def handle_data_request(self, ctx: agent.ProcessContext[DataRequest], database: DatabaseService):
        """Handle data storage requests with an injected database dependency."""
        request = ctx.payload
        action = request.action.lower()
        
        print(f"[{self.name}] Handling data request: {action} for key '{request.key}'")
        
        if action == "save":
            database.save(request.key, request.value)
            ctx.send(Response(
                success=True,
                message=f"Data saved for key '{request.key}'",
                data={"key": request.key, "value": request.value}
            ))
        elif action == "get":
            value = database.get(request.key)
            ctx.send(Response(
                success=True,
                message=f"Data retrieved for key '{request.key}'",
                data={"key": request.key, "value": value}
            ))
        else:
            ctx.send(Response(
                success=False,
                message=f"Unknown action: {action}",
                data=None
            ))
    
    @agent.processor(clz=ApiRequest, depends_on=["api_service"])
    def handle_api_request(self, ctx: agent.ProcessContext[ApiRequest], api_service: ApiService):
        """Handle API requests with an injected API service dependency."""
        request = ctx.payload
        
        print(f"[{self.name}] Handling API request for endpoint '{request.endpoint}'")
        
        try:
            result = api_service.call_api(request.endpoint, request.data)
            ctx.send(Response(
                success=True,
                message=f"API call to '{request.endpoint}' successful",
                data=result
            ))
        except Exception as e:
            ctx.send(Response(
                success=False,
                message=f"API call failed: {str(e)}",
                data=None
            ))


async def main():
    # Create and launch a guild
    guild = GuildBuilder("dependency_guild", "Dependency Injection Guild", "A guild demonstrating dependency injection") \
        .launch(add_probe=True)
    
    # Get the probe agent for monitoring messages
    probe_agent = guild.get_agent_of_type(ProbeAgent)
    print(f"Created guild with ID: {guild.id}")
    
    # Define dependencies for our agent
    dependencies = {
        "database": DependencySpec(
            class_name="__main__.DatabaseResolver",
            properties={"connection_string": "memory://test_db"}
        ),
        "api_service": DependencySpec(
            class_name="__main__.ApiServiceResolver",
            properties={"api_key": "test_api_key", "base_url": "https://test.example.com"}
        )
    }
    
    # Create and launch our agent with dependencies
    agent_spec = AgentBuilder(DependencyInjectionAgent) \
        .set_name("DependencyAgent") \
        .set_description("Agent demonstrating dependency injection") \
        .set_dependency_map(dependencies) \
        .build_spec()
    
    guild.launch_agent(agent_spec)
    
    print("\nAgents in the guild:")
    for agent_spec in guild.list_agents():
        print(f"- {agent_spec.name} (ID: {agent_spec.id}, Type: {agent_spec.class_name})")
    
    # Test data storage
    print("\n--- Testing Database Dependency ---")
    print("Sending 'save' request...")
    probe_agent.publish("default_topic", DataRequest(action="save", key="greeting", value="Hello, World!"))
    await asyncio.sleep(1)  # Wait for processing
    
    # Check saved data
    print("\nSending 'get' request...")
    probe_agent.publish("default_topic", DataRequest(action="get", key="greeting"))
    await asyncio.sleep(1)  # Wait for processing
    
    # Test API service
    print("\n--- Testing API Service Dependency ---")
    print("Sending API request...")
    probe_agent.publish("default_topic", ApiRequest(
        endpoint="users",
        data={"id": 123, "action": "fetch"}
    ))
    await asyncio.sleep(1)  # Wait for processing
    
    # Print all messages
    messages = probe_agent.get_messages()
    print(f"\nCaptured {len(messages)} response message(s):")
    for i, msg in enumerate(messages, 1):
        print(f"\nResponse {i}:")
        print(f"Success: {msg.payload.get('success', False)}")
        print(f"Message: {msg.payload.get('message', 'N/A')}")
        if "data" in msg.payload and msg.payload["data"]:
            print(f"Data: {msg.payload['data']}")
    
    # Shutdown the guild
    guild.shutdown()
    print("\nGuild shutdown complete")


if __name__ == "__main__":
    asyncio.run(main()) 