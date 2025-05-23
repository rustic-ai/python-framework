# Writing Effective Tests for RusticAI Agents

This guide provides practical advice and patterns for writing effective tests for RusticAI agents. It builds on the concepts in the [Testing Agents](testing_agents.md) guide, with a focus on real-world testing examples from the RusticAI codebase.

## Key Testing Patterns in RusticAI

When examining tests across the RusticAI ecosystem (including specialized agents like PlaywrightAgent, SERPAgent, and LiteLLMAgent), several effective patterns emerge:

1. **Isolation testing** with `wrap_agent_for_testing`
2. **Integration testing** with probe agents
3. **Targeted dependency mocking** for external service dependencies
4. **Async testing** with `asyncio` for agents with asynchronous operations
5. **Environment setup and cleanup** using pytest fixtures
6. **Conditional tests** that skip when external service credentials aren't available

## Testing External Service Agents

Many RusticAI agents integrate with external services like APIs, databases, or other tools. Here's a pattern for testing such agents:

```python
import pytest
import os
from unittest.mock import patch

from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.messaging.core.message import AgentTag, Message
from rustic_ai.core.utils.priority import Priority
from rustic_ai.core.utils.basic_class_utils import get_qualified_class_name
from rustic_ai.testing.helpers import wrap_agent_for_testing
from rustic_ai.your_module.agent import YourServiceAgent, ServiceRequest, ServiceResponse

class TestYourServiceAgent:
    # Test with real API if credentials are available
    @pytest.mark.skipif(
        os.getenv("YOUR_API_KEY") is None, 
        reason="YOUR_API_KEY environment variable not set"
    )
    def test_with_real_api(self, generator):
        # Create and wrap the agent
        agent, results = wrap_agent_for_testing(
            AgentBuilder(YourServiceAgent)
            .set_name("TestServiceAgent")
            .set_id("test_agent")
            .set_description("Test Service Agent")
            .build(),
            generator,
        )
        
        # Create a test request message
        request = Message(
            topics="default_topic",
            sender=AgentTag(id="testerId", name="tester"),
            format=get_qualified_class_name(ServiceRequest),
            payload={"param1": "value1", "param2": "value2"},
            id_obj=generator.get_id(Priority.NORMAL),
        )
        
        # Send the message
        agent._on_message(request)
        
        # Assert on the results
        assert len(results) == 1
        assert results[0].in_response_to == request.id
        
        # Validate the response
        response = ServiceResponse.model_validate(results[0].payload)
        assert response.success == True
        assert response.data is not None
    
    # Test with mocked API
    def test_with_mocked_api(self, generator):
        # Mock the external service
        with patch("your_module.service.Client.call_api") as mock_api:
            # Configure the mock
            mock_api.return_value = {"result": "mocked_data"}
            
            # Create and wrap the agent
            agent, results = wrap_agent_for_testing(
                AgentBuilder(YourServiceAgent)
                .set_name("TestServiceAgent")
                .set_id("test_agent")
                .set_description("Test Service Agent")
                .build(),
                generator,
            )
            
            # Create a test request message
            request = Message(
                topics="default_topic",
                sender=AgentTag(id="testerId", name="tester"),
                format=get_qualified_class_name(ServiceRequest),
                payload={"param1": "value1", "param2": "value2"},
                id_obj=generator.get_id(Priority.NORMAL),
            )
            
            # Send the message
            agent._on_message(request)
            
            # Assert the mock was called correctly
            mock_api.assert_called_once_with("value1", "value2")
            
            # Assert on the results
            assert len(results) == 1
            response = ServiceResponse.model_validate(results[0].payload)
            assert response.data["result"] == "mocked_data"
```

## Testing Asynchronous Agents

For agents that perform asynchronous operations (like web scraping or API calls), your tests need to account for the asynchronous nature:

```python
import asyncio
import pytest

from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.testing.helpers import wrap_agent_for_testing
from rustic_ai.your_module.agent import AsyncAgent

class TestAsyncAgent:
    @pytest.mark.asyncio  # Requires pytest-asyncio
    async def test_async_operation(self, generator):
        # Create and wrap the agent
        agent, results = wrap_agent_for_testing(
            AgentBuilder(AsyncAgent)
            .set_name("TestAsyncAgent")
            .set_id("test_agent")
            .build(),
            generator,
        )
        
        # Create and send a test message
        # ... code to create message ...
        agent._on_message(message)
        
        # Wait for async operations to complete
        # This is important! We need to give the async operations time to run
        tries = 0
        while True:
            await asyncio.sleep(0.5)  # Wait a bit
            tries += 1
            # Exit when we get the expected results or timeout
            if len(results) > 0 or tries > 10:
                break
        
        # Now perform assertions
        assert len(results) > 0
        # ... more specific assertions ...
```

## Testing with External Dependencies

Agents often depend on external services. You can inject mock or real dependencies during testing:

```python
from rustic_ai.core.guild.agent_ext.depends.dependency_resolver import DependencySpec
from rustic_ai.testing.helpers import wrap_agent_for_testing

def test_agent_with_dependencies(generator):
    # Define test dependencies
    filesystem = DependencySpec(
        class_name="rustic_ai.core.guild.agent_ext.depends.filesystem.FileSystemResolver",
        properties={
            "path_base": "/tmp/test", 
            "protocol": "file",
            "storage_options": {"auto_mkdir": True},
        },
    )
    
    # Create and wrap the agent with dependencies
    agent, results = wrap_agent_for_testing(
        AgentBuilder(YourAgent)
        .set_id("test_agent")
        .set_name("TestAgent")
        .build(),
        generator,
        {"filesystem": filesystem},  # Inject dependencies here
    )
    
    # Create and send a test message
    # ... code to create and send message ...
    
    # You can even access and test the injected dependency
    fs = filesystem.to_resolver().resolve(agent.guild_id, "GUILD_GLOBAL")
    assert fs.exists(some_path)
```

## Testing Agent Error Handling

Good agent tests not only verify correct behavior but also proper error handling:

```python
def test_error_handling(generator):
    # Create and wrap the agent
    agent, results = wrap_agent_for_testing(
        AgentBuilder(YourAgent)
        .set_name("TestAgent")
        .set_id("test_agent")
        .build(),
        generator,
    )
    
    # 1. Test with invalid input
    invalid_message = create_message_with_invalid_payload()
    agent._on_message(invalid_message)
    
    # Verify agent produces appropriate error response
    assert len(results) == 1
    assert results[0].is_error_message
    assert "Invalid input" in results[0].payload.get("error", "")
    
    # 2. Test when a dependency fails
    with patch("some_dependency.method") as mock_dep:
        mock_dep.side_effect = Exception("Dependency failed")
        
        results.clear()  # Clear previous results
        valid_message = create_valid_message()
        agent._on_message(valid_message)
        
        # Verify agent handles dependency failure gracefully
        assert len(results) == 1
        assert results[0].is_error_message
        assert "Dependency failed" in results[0].payload.get("error", "")
```

## Integration Testing with Probe Agent

The `ProbeAgent` is a powerful tool for testing agent interactions within a guild:

```python
import pytest
import time

from rustic_ai.core.agents.testutils.probe_agent import ProbeAgent
from rustic_ai.core.guild.builders import AgentBuilder, GuildBuilder

@pytest.fixture
def test_guild():
    # Create a guild for testing
    guild = GuildBuilder("test_guild", "Test Guild", "Guild for testing").launch(add_probe=True)
    
    # Add your test agents
    agent1_spec = AgentBuilder(Agent1Class).set_name("Agent1").build_spec()
    agent2_spec = AgentBuilder(Agent2Class).set_name("Agent2").build_spec()
    
    guild.launch_agent(agent1_spec)
    guild.launch_agent(agent2_spec)
    
    # Get the probe agent
    probe_agent = guild.get_agent_of_type(ProbeAgent)
    
    # Return guild and probe agent
    try:
        yield guild, probe_agent
    finally:
        # Always clean up
        guild.shutdown()

def test_agent_interaction(test_guild):
    guild, probe_agent = test_guild
    
    # Send an initial message to trigger interaction
    probe_agent.publish("default_topic", StartMessage(data="test"))
    
    # Wait for messages to be processed
    time.sleep(1)
    
    # Get all messages captured by the probe
    messages = probe_agent.get_messages()
    
    # Verify the correct sequence of interactions
    assert len(messages) >= 2
    assert messages[0].sender.id == "agent1"
    assert messages[1].sender.id == "agent2"
    # ... more detailed assertions about message content ...
```

## Testing LLM-based Agents

For agents that use language models (like LiteLLMAgent), you can use the mock_response pattern:

```python
from rustic_ai.core.guild.agent_ext.depends.llm.models import (
    ChatCompletionRequest, SystemMessage, UserMessage
)

def test_llm_agent(probe_agent, guild):
    # Create and add the LLM agent to the guild
    agent = AgentBuilder(LLMAgent) \
        .set_name("Test LLM Agent") \
        .set_id("llm_agent") \
        .build()
    
    guild._add_local_agent(agent)
    
    # Create a request with a mock response to avoid real API calls
    chat_completion_request = ChatCompletionRequest(
        messages=[UserMessage(content="What is the capital of France?")],
        mock_response="The capital of France is Paris.",  # Mock response
    )
    
    # Send the request
    probe_agent.publish_dict(
        guild.DEFAULT_TOPIC,
        chat_completion_request,
        format=ChatCompletionRequest,
    )
    
    time.sleep(1)  # Wait for processing
    
    # Check the results
    messages = probe_agent.get_messages()
    assert len(messages) == 1
    assert "Paris" in messages[0].payload["choices"][0]["message"]["content"]
```

## Common Testing Pitfalls and Solutions

### 1. Race Conditions in Async Tests

**Problem**: Tests sometimes pass, sometimes fail due to timing issues.

**Solution**: Use `asyncio.sleep()` with retries to wait for operations to complete:

```python
# Instead of a fixed sleep time:
tries = 0
while True:
    await asyncio.sleep(0.2)
    tries += 1
    # Exit condition based on expected state
    if len(results) > 0 or tries > 10:  # Timeout after 10 tries
        break
```

### 2. Resource Cleanup in Tests

**Problem**: Tests leave behind resources that affect other tests.

**Solution**: Use pytest fixtures with cleanup:

```python
@pytest.fixture
def resource_fixture():
    # Setup
    resource = create_resource()
    
    yield resource  # Provide the resource to the test
    
    # Cleanup (always runs, even if test fails)
    resource.cleanup()
```

### 3. External Service Dependency

**Problem**: Tests fail when run without access to external services.

**Solution**: Use `pytest.mark.skipif` to conditionally skip tests:

```python
@pytest.mark.skipif(
    os.getenv("REQUIRED_API_KEY") is None,
    reason="API key not available"
)
def test_with_external_service():
    # Test that requires external service
```

## Best Practices Summary

1. **Parametrize Common Tests**: Use `@pytest.mark.parametrize` to run the same test with different inputs.

2. **Keep Dependencies Consistent**: Use the same dependency structure in tests as in production code.

3. **Test Failure Modes**: Don't just test the happy path; test how your agent handles errors.

4. **Mock External Services**: Use `unittest.mock.patch` to replace external API calls.

5. **Combine Unit and Integration Tests**: Test components in isolation first, then together.

6. **Use Descriptive Test Names**: Make your test names describe the behavior being tested.

7. **Isolate Test State**: Ensure tests don't interfere with each other's state.

## Real-World Examples from RusticAI

To see these patterns in action, examine the test suites for these agents:

1. **PlaywrightAgent**: Tests asynchronous web scraping with injected filesystem dependency
2. **SERPAgent**: Tests API calls with both real and mocked services
3. **LiteLLMAgent**: Tests LLM integration with mock responses

These examples demonstrate how to effectively test agents with different requirements and complexity levels.

## Conclusion

Effective testing is crucial for building reliable agent-based systems. By following these patterns and guidelines, you can create tests that validate your agents' behavior, handle edge cases, and catch regressions early. Remember that good tests not only verify that the right thing happens when the right input is provided, but also that the right thing happens when something goes wrong. 