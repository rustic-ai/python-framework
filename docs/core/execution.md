# Execution

Execution in RusticAI Core is managed by execution engines, which control how agents are run, scheduled, and coordinated. This enables flexible deployment, from simple synchronous runs to advanced multithreaded or distributed setups.

## Purpose
- Manage the lifecycle and scheduling of agents
- Support different execution models (sync, multithreaded, etc.)
- Integrate with messaging and state management

## Execution Engines
- **SyncExecutionEngine**: Runs agents synchronously in the main thread/process.
- **MultithreadedExecutionEngine**: Runs agents in separate threads for concurrency.
- **Custom Engines**: Extendable for distributed or custom execution models.

| Engine | Concurrency Model | Suitable For | Key Config |
|--------|------------------|--------------|------------|
| `SyncExecutionEngine` | Single-thread | Tutorials, deterministic tests | — |
| `MultithreadedExecutionEngine` | Thread-per-agent / thread-pool | IO-bound tasks, WebSocket bots | `max_workers`, `thread_name_prefix` |
| *Custom* | Anything (asyncio, processes, Ray, etc.) | Specialised workloads | Implement `BaseExecutionEngine` |

### Configuring the Multithreaded Engine
```python
engine = MultithreadedExecutionEngine(max_workers=8, thread_name_prefix="agent-")
guild.launch_agent(spec, execution_engine=engine)
```

### Graceful Shutdown
All engines respect graceful stop semantics:
1. **Stop Request**: Call `guild.stop()` or send SIGINT / SIGTERM.
2. **Drain**: Execution engine stops accepting new messages; in-flight handlers finish.
3. **Teardown Hooks**: `@AgentFixtures.on_shutdown` hooks run to release resources.
4. **Join**: Threads / tasks joined with timeout to avoid hangs.

### Live Reload & Hot-Swap
For rapid development you can reload agent code without restarting the guild:

```python
guild.reload_agent(agent_id="agent-1", new_spec=updated_spec)
```

The execution engine swaps the wrapper in-place and re-attaches open state handles.

## Agent Wrappers
Agent wrappers encapsulate the logic for initializing, running, and shutting down agents within an execution engine. They handle:
- Dependency injection
- Messaging client setup
- State and guild context

## Example: Running an Agent with an Execution Engine
```python
from rustic_ai.core.guild import AgentBuilder, Guild
from rustic_ai.core.guild.execution import SyncExecutionEngine

# Create a guild and agent spec
guild = Guild(...)
agent_spec = AgentBuilder(...).set_name("Agent1").set_description("...").build_spec()

# Launch the agent using the default execution engine
guild.launch_agent(agent_spec)

# Or use a custom execution engine
engine = SyncExecutionEngine()
guild.launch_agent(agent_spec, execution_engine=engine)
```

## Advanced Topics
- **Agent Tracking**: Track running agents and their wrappers for management and monitoring.
- **Shutdown and Cleanup**: Properly stop agents and release resources.
- **Extending Execution Engines**: Implement custom scheduling, resource management, or distributed execution.

> See the [Guilds](guilds.md) and [Agents](agents.md) sections for how execution integrates with agent and guild lifecycles. 