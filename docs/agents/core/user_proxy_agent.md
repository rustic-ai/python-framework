# UserProxyAgent

The `UserProxyAgent` serves as an interface between human users and a RusticAI guild, handling the translation of user inputs into agent messages and formatting agent responses for user consumption.

## Purpose

This agent acts as a bridge between external users and the guild's internal messaging system. It provides a consistent interface for users to interact with the guild, handles various input/output formats, and maintains user-specific state.

## When to Use

Use the `UserProxyAgent` when you need to:

- Create a user-facing interface to a RusticAI guild
- Manage user sessions and conversations
- Format content for display to users
- Route user requests to appropriate specialized agents
- Build applications with direct user interaction

## Configuration

The `UserProxyAgent` is configured through the `UserProxyAgentProps` class, which allows setting:

```python
class UserProxyAgentProps(BaseAgentProps):
    default_target: Optional[str] = None  # Default agent to send messages to
    include_message_history: bool = True  # Whether to include message history
    max_history_messages: int = 10  # Maximum number of messages in history
    user_id: Optional[str] = None  # ID of the user this agent represents
```

## Message Types

### Input Messages

#### UserMessage

A message from a user to the system:

```python
class UserMessage(BaseModel):
    content: str  # The user's message text
    target: Optional[str] = None  # Optional target agent ID
```

#### UserChatRequest

A chat message with optional content parts (text, images, etc.):

```python
class UserChatRequest(BaseModel):
    content: Optional[List[ContentPart]] = None  # Content parts
    target: Optional[str] = None  # Optional target agent ID
```

### Output Messages

#### UserChatResponse

A formatted response for display to the user:

```python
class UserChatResponse(BaseModel):
    content: Union[str, List[ContentPart]]  # Response content
    format: Optional[TextFormat] = TextFormat.MARKDOWN  # Text format
```

#### SystemAlert

A system message or alert for the user:

```python
class SystemAlert(BaseModel):
    title: str  # Alert title
    content: str  # Alert content
    level: AlertLevel = AlertLevel.INFO  # Alert importance level
```

## Behavior

1. The agent receives a message from the user interface
2. It processes the message based on type:
   - Basic user messages are converted to appropriate formats
   - Chat requests are formatted with content parts
   - Messages are routed to the specified target or default target
3. The agent maintains a conversation history for context
4. Responses from other agents are formatted for user consumption
5. System alerts and status updates are sent to the user interface

## Sample Usage

```python
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.agents.utils.user_proxy_agent import UserProxyAgent, UserProxyAgentProps

# Create the agent spec with configuration
user_proxy_spec = (
    AgentBuilder(UserProxyAgent)
    .set_id("user_proxy")
    .set_name("User Interface")
    .set_description("Interface between user and the system")
    .set_properties(
        UserProxyAgentProps(
            default_target="llm_agent",  # Default target is the LLM agent
            max_history_messages=15,  # Remember 15 messages of history
            user_id="user-123"  # Associate with specific user
        )
    )
    .build_spec()
)

# Add to guild
guild_builder.add_agent_spec(user_proxy_spec)
```

## Integration with User Interfaces

The `UserProxyAgent` is typically integrated with:

1. **Web interfaces** - Through WebSocket connections or REST APIs
2. **Chat interfaces** - For conversational applications
3. **Command-line interfaces** - For developer tools and scripts
4. **Mobile apps** - Via appropriate API endpoints

### Example Web Integration

```python
# In a web server route handler
@app.route("/chat", methods=["POST"])
def handle_chat():
    user_id = get_user_id_from_session()
    message_content = request.json.get("message")
    
    # Get the user's proxy agent ID (or create one if it doesn't exist)
    user_proxy_id = get_or_create_user_proxy(user_id)
    
    # Send message to the user's proxy agent
    guild.publish_message(
        UserMessage(content=message_content),
        recipient=user_proxy_id
    )
    
    # In a real implementation, would use WebSockets or
    # some other mechanism to stream back the response
    return {"status": "message_sent"}
```

## Guild Refresh Capabilities

The `UserProxyAgent` implements the `GuildRefreshMixin`, which allows it to:

1. Request a refresh of the guild state
2. Update its knowledge of available agents
3. Discover new capabilities as agents are added or removed
4. Adapt routing based on the current guild configuration

## Notes and Limitations

- Each user typically needs their own `UserProxyAgent` instance
- For multi-user applications, agent IDs should incorporate user identifiers
- The agent maintains state in memory by default, so consider persistence for production
- Consider security implications when exposing guild functionality to users
- Message history is kept in memory, so be mindful of memory usage with many users 