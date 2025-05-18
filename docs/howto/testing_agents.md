# Testing Agents in RusticAI

This guide explains how to effectively test agents in the RusticAI framework. Testing is a crucial aspect of developing robust multi-agent systems, and RusticAI provides several utilities to make testing straightforward.

## Prerequisites

Before you begin, make sure you have:
- Installed RusticAI and its dependencies
- Basic understanding of agents (see [Creating Your First Agent](creating_your_first_agent.md))
- Familiarity with Python testing frameworks like pytest

## Types of Testing

When testing RusticAI agents, you'll typically perform several types of tests:

1. **Unit Tests**: Testing individual agents in isolation
2. **Integration Tests**: Testing how multiple agents interact within a guild
3. **System Tests**: Testing complete guild behaviors and workflows
4. **Performance Tests**: Testing agent performance under load

This guide primarily focuses on unit testing agents in isolation, which is the most common starting point.

## Using `wrap_agent_for_testing`

RusticAI provides a powerful utility `wrap_agent_for_testing` (from `rustic_ai.testing.helpers`) that simplifies agent testing by:

1. Setting up the agent in a testing environment
2. Managing dependencies
3. Capturing outgoing messages
4. Providing tools to simulate incoming messages

Here's how to use it:

```python
import pytest
from pydantic import BaseModel
from typing import List

from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.dsl import AgentSpec, BaseAgentProps
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.messaging.core.message import Message, AgentTag
from rustic_ai.core.utils.priority import Priority
from rustic_ai.core.utils.gemstone_id import GemstoneGenerator
from rustic_ai.testing.helpers import wrap_agent_for_testing

# Define message models
class GreetRequest(BaseModel):
    name: str

class GreetResponse(BaseModel):
    greeting: str

# Define the agent to test
class GreeterAgent(Agent[BaseAgentProps]):
    def __init__(self, agent_spec: AgentSpec[BaseAgentProps]):
        super().__init__(agent_spec)
    
    @agent.processor(clz=GreetRequest)
    def greet(self, ctx: agent.ProcessContext[GreetRequest]):
        name = ctx.payload.name
        ctx.send(GreetResponse(greeting=f"Hello, {name}!"))

# Test fixture
@pytest.fixture
def greeter_agent():
    # Create the agent instance
    agent = AgentBuilder(GreeterAgent)\
        .set_name("TestGreeter")\
        .build()
    
    # Set up for testing
    id_generator = GemstoneGenerator(machine_id=1)
    test_agent, results = wrap_agent_for_testing(agent, id_generator)
    
    return test_agent, results, id_generator

# Test function
def test_greeter_agent(greeter_agent):
    agent, results, id_generator = greeter_agent
    
    # Create a test message
    msg = Message(
        id_obj=id_generator.get_id(Priority.NORMAL),
        topics=["test_topic"],
        sender=AgentTag(id="test_sender", name="Test User"),
        payload=GreetRequest(name="Alice").model_dump(),
        format=GreetRequest.model_json_schema()["$id"],
    )
    
    # Deliver message to the agent
    agent._on_message(msg)
    
    # Verify the response
    assert len(results) == 1, "Expected exactly one response message"
    response = GreetResponse.model_validate(results[0].payload)
    assert response.greeting == "Hello, Alice!"
```

## Testing Agents with Dependencies

For agents that use dependency injection, you need to provide mock versions of the dependencies:

```python
from rustic_ai.core.guild.dsl import DependencySpec
from rustic_ai.core.guild.agent_ext.depends.dependency_resolver import DependencyResolver

# Mock database service
class MockDatabaseService:
    def __init__(self):
        self.data = {}
    
    def save(self, key, value):
        self.data[key] = value
        return True
    
    def get(self, key):
        return self.data.get(key)

# Mock database resolver
class MockDatabaseResolver(DependencyResolver):
    def resolve(self, guild_id, agent_id=None):
        return MockDatabaseService()

# Test for an agent with dependencies
def test_agent_with_database():
    # Create the agent instance
    agent = AgentBuilder(DatabaseAgent)\
        .set_name("TestDatabaseAgent")\
        .build()
    
    # Set up testing with mock dependencies
    id_generator = GemstoneGenerator(machine_id=1)
    dependencies = {
        "database": DependencySpec(
            class_name="__main__.MockDatabaseResolver",
            properties={}
        )
    }
    
    test_agent, results = wrap_agent_for_testing(
        agent,
        id_generator,
        dependencies=dependencies
    )
    
    # Create and send test messages...
    # ... assertions ...
```

## Testing Stateful Agents

When testing agents that maintain state, you need to consider how state updates are processed:

```python
def test_stateful_counter_agent():
    # Create and wrap the agent for testing
    agent = AgentBuilder(CounterAgent)\
        .set_name("TestCounter")\
        .build()
    
    id_generator = GemstoneGenerator(machine_id=1)
    test_agent, results = wrap_agent_for_testing(agent, id_generator)
    
    # The agent's _state is directly accessible in tests
    assert test_agent._state.get("count", 0) == 0
    
    # Send increment message
    msg = Message(
        id_obj=id_generator.get_id(Priority.NORMAL),
        topics=["test_topic"],
        sender=AgentTag(id="test_sender", name="Test User"),
        payload=IncrementRequest(amount=5).model_dump(),
        format=IncrementRequest.model_json_schema()["$id"],
    )
    
    test_agent._on_message(msg)
    
    # In testing, StateRefresherMixin will update _state directly
    # So we can check it after processing
    assert test_agent._state.get("count", 0) == 5
    
    # Also verify the response message
    assert len(results) == 1
    response = CounterResponse.model_validate(results[0].payload)
    assert response.count == 5
```

## Testing Asynchronous Handlers

If your agent has asynchronous handlers, you'll need to use pytest-asyncio:

```python
import pytest
import asyncio

# Decorate the test function with pytest.mark.asyncio
@pytest.mark.asyncio
async def test_async_agent():
    # Set up agent for testing
    agent, results, id_generator = setup_async_agent_for_testing()
    
    # Send test message
    test_message = create_test_message(id_generator)
    agent._on_message(test_message)
    
    # Allow time for async operations to complete
    await asyncio.sleep(0.1)
    
    # Now check the results
    assert len(results) == 1
    # ... more assertions ...
```

## Integration Testing with Multiple Agents

To test interactions between multiple agents, you can set up a test guild:

```python
@pytest.fixture
def test_guild():
    # Create a test guild with required agents
    guild = GuildBuilder("test_guild", "Test Guild", "Guild for testing")\
        .launch(add_probe=True)
    
    # Create and launch test agents
    agent1_spec = AgentBuilder(Agent1Class)\
        .set_name("Agent1")\
        .build_spec()
    
    agent2_spec = AgentBuilder(Agent2Class)\
        .set_name("Agent2")\
        .build_spec()
    
    guild.launch_agent(agent1_spec)
    guild.launch_agent(agent2_spec)
    
    # Return the guild and its probe agent
    probe_agent = guild.get_agent_of_type(ProbeAgent)
    yield guild, probe_agent
    
    # Cleanup after tests
    guild.shutdown()

def test_agent_interaction(test_guild):
    guild, probe_agent = test_guild
    
    # Send a message that should trigger a chain of agent interactions
    probe_agent.publish("default_topic", StartMessage(data="test"))
    
    # Allow time for message processing
    time.sleep(0.5)
    
    # Get messages captured by the probe
    messages = probe_agent.get_messages()
    
    # Verify the expected interaction happened
    assert len(messages) >= 2
    # ... detailed assertions about the messages ...
```

## Using Mocks for External Services

For agents that interact with external services, use unittest.mock to control test behavior:

```python
from unittest.mock import patch, MagicMock

def test_agent_with_external_service():
    # Create and wrap the agent
    agent, results, id_generator = setup_agent_for_testing()
    
    # Mock the external service call
    with patch("external_module.service_function") as mock_service:
        # Configure the mock
        mock_service.return_value = {"result": "mock_data"}
        
        # Send test message
        test_message = create_test_message(id_generator)
        agent._on_message(test_message)
        
        # Verify service was called with correct parameters
        mock_service.assert_called_once_with("expected_param")
        
        # Verify agent response
        assert len(results) == 1
        assert results[0].payload["data"] == "mock_data"
```

## Testing Error Handling

It's important to test how your agents handle errors:

```python
def test_agent_error_handling():
    agent, results, id_generator = setup_agent_for_testing()
    
    # Send a message that should trigger an error
    error_message = Message(
        id_obj=id_generator.get_id(Priority.NORMAL),
        topics=["test_topic"],
        sender=AgentTag(id="test_sender", name="Test User"),
        payload=InvalidRequest().model_dump(),
        format=InvalidRequest.model_json_schema()["$id"],
    )
    
    # The agent should handle the error and send an error message
    agent._on_message(error_message)
    
    # Verify error response
    assert len(results) == 1
    assert results[0].is_error_message
    assert "error" in results[0].payload
```

## Performance Testing

To test performance, you might want to measure how quickly an agent processes messages:

```python
import time

def test_agent_performance():
    agent, results, id_generator = setup_agent_for_testing()
    
    # Generate a large number of test messages
    messages = [create_test_message(id_generator, i) for i in range(100)]
    
    # Measure processing time
    start_time = time.time()
    
    for msg in messages:
        agent._on_message(msg)
    
    elapsed_time = time.time() - start_time
    
    # Assert on performance criteria
    assert elapsed_time < 1.0, f"Processing took too long: {elapsed_time:.2f}s"
    assert len(results) == 100, "Not all messages were processed"
```

## Debugging Tips

When tests fail, here are some debugging strategies:

1. **Increase Logging**: Add logging in your agent's handlers to trace execution paths.

2. **Inspect Test Messages**: Print the contents of `results` to see what messages the agent is actually sending.

3. **Check State**: For stateful agents, examine `_state` during test execution to verify it's being updated correctly.

4. **Step Through Execution**: Use a debugger to step through the agent's message processing flow.

5. **Isolate Components**: If testing a complex agent, try to isolate and test individual features first.

## Testing Best Practices

1. **Test Each Handler**: Create separate tests for each message handler in your agent.

2. **Cover Edge Cases**: Test how your agent handles unexpected inputs, missing fields, etc.

3. **Use Fixtures**: Create pytest fixtures for common setup code to keep tests DRY.

4. **Test State Transitions**: For stateful agents, verify that state transitions occur correctly.

5. **Mock External Dependencies**: Always mock external services and APIs for deterministic tests.

6. **Test Error Cases**: Ensure your agent handles errors gracefully.

7. **Keep Tests Fast**: Aim for quick-running tests to maintain a fast feedback loop during development.

## Example: A Complete Test Suite

Here's an example of a more complete test suite for an agent:

```python
import pytest
from pydantic import BaseModel
from typing import Dict, Any

from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.dsl import AgentSpec, BaseAgentProps
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.messaging.core.message import Message, AgentTag
from rustic_ai.core.utils.priority import Priority
from rustic_ai.core.utils.gemstone_id import GemstoneGenerator
from rustic_ai.testing.helpers import wrap_agent_for_testing

# Message models
class CalculationRequest(BaseModel):
    operation: str  # "add", "subtract", "multiply", "divide"
    a: float
    b: float

class CalculationResponse(BaseModel):
    result: float
    operation: str

# Agent implementation
class CalculatorAgent(Agent[BaseAgentProps]):
    def __init__(self, agent_spec: AgentSpec[BaseAgentProps]):
        super().__init__(agent_spec)
    
    @agent.processor(clz=CalculationRequest)
    def calculate(self, ctx: agent.ProcessContext[CalculationRequest]):
        req = ctx.payload
        result = None
        
        if req.operation == "add":
            result = req.a + req.b
        elif req.operation == "subtract":
            result = req.a - req.b
        elif req.operation == "multiply":
            result = req.a * req.b
        elif req.operation == "divide":
            if req.b == 0:
                ctx.send_error({"error": "Division by zero"})
                return
            result = req.a / req.b
        else:
            ctx.send_error({"error": f"Unknown operation: {req.operation}"})
            return
        
        ctx.send(CalculationResponse(
            result=result,
            operation=req.operation
        ))

# Test fixtures
@pytest.fixture
def calculator_setup():
    # Create agent
    agent = AgentBuilder(CalculatorAgent)\
        .set_name("TestCalculator")\
        .build()
    
    # Wrap for testing
    id_generator = GemstoneGenerator(machine_id=1)
    test_agent, results = wrap_agent_for_testing(agent, id_generator)
    
    return test_agent, results, id_generator

# Helper function to create test messages
def create_calc_message(id_generator, operation, a, b):
    return Message(
        id_obj=id_generator.get_id(Priority.NORMAL),
        topics=["test_topic"],
        sender=AgentTag(id="test_sender", name="Test User"),
        payload=CalculationRequest(operation=operation, a=a, b=b).model_dump(),
        format=CalculationRequest.model_json_schema()["$id"],
    )

# Test functions
def test_addition(calculator_setup):
    agent, results, id_generator = calculator_setup
    
    msg = create_calc_message(id_generator, "add", 2, 3)
    agent._on_message(msg)
    
    assert len(results) == 1
    response = CalculationResponse.model_validate(results[0].payload)
    assert response.result == 5
    assert response.operation == "add"

def test_division(calculator_setup):
    agent, results, id_generator = calculator_setup
    
    msg = create_calc_message(id_generator, "divide", 10, 2)
    agent._on_message(msg)
    
    assert len(results) == 1
    response = CalculationResponse.model_validate(results[0].payload)
    assert response.result == 5
    assert response.operation == "divide"

def test_division_by_zero(calculator_setup):
    agent, results, id_generator = calculator_setup
    
    msg = create_calc_message(id_generator, "divide", 10, 0)
    agent._on_message(msg)
    
    assert len(results) == 1
    assert results[0].is_error_message
    assert "error" in results[0].payload
    assert "Division by zero" in results[0].payload["error"]

def test_unknown_operation(calculator_setup):
    agent, results, id_generator = calculator_setup
    
    msg = create_calc_message(id_generator, "power", 2, 3)
    agent._on_message(msg)
    
    assert len(results) == 1
    assert results[0].is_error_message
    assert "Unknown operation" in results[0].payload["error"]
```

## Next Steps

Now that you understand how to test agents, you might want to:

- Learn about [state management in agents](state_management.md)
- Explore [dependency injection](dependency_injection.md)
- Understand how to [create a guild](creating_a_guild.md) with multiple agents

For complete examples, see the unit tests in the RusticAI framework codebase, which demonstrate best practices for testing various agent types. 