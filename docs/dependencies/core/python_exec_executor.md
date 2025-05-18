# PythonExecExecutorResolver

The `PythonExecExecutorResolver` provides a secure way for agents to execute Python code dynamically. It includes safeguards like import whitelisting to prevent potentially harmful operations.

## Overview

- **Type**: `DependencyResolver[CodeExecutor]`
- **Provided Dependency**: `PythonExecExecutor`
- **Package**: `rustic_ai.core.guild.agent_ext.depends.code_execution.stateful.python_exec_executor`

## Security Features

- **Import Whitelisting**: Only pre-approved modules can be imported
- **Agent Isolation**: Each agent gets its own execution environment
- **Default Imports**: Common, safe packages can be pre-imported
- **No File System Access**: By default, file system access is restricted

## Configuration

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `whitelisted_imports` | `Set[str]` | Set of package names that are allowed to be imported | `None` (all imports blocked) |
| `default_imports` | `Dict[str, str]` | Dictionary mapping import names to their module paths | `None` (no default imports) |

## Usage

### Guild Configuration

```python
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.guild.dsl import DependencySpec

guild_builder = (
    GuildBuilder("code_guild", "Code Execution Guild", "Guild with Python execution capabilities")
    .add_dependency_resolver(
        "code_executor",
        DependencySpec(
            class_name="rustic_ai.core.guild.agent_ext.depends.code_execution.stateful.python_exec_executor.PythonExecExecutorResolver",
            properties={
                "whitelisted_imports": ["numpy", "pandas", "matplotlib.pyplot"],
                "default_imports": {
                    "np": "numpy",
                    "pd": "pandas",
                    "plt": "matplotlib.pyplot"
                }
            }
        )
    )
)
```

### Agent Usage

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.agent_ext.depends.code_execution.stateful.python_exec_executor import PythonExecExecutor

class CodeExecutionAgent(Agent):
    @agent.processor(clz=CodeRequest, depends_on=["code_executor"])
    def execute_code(self, ctx: agent.ProcessContext, code_executor: PythonExecExecutor):
        code = ctx.payload.code
        input_data = ctx.payload.input_data
        
        # Execute the code with the provided input data
        result = code_executor.execute(
            code=code,
            globals_dict={"input_data": input_data},
            return_globals=["output"]
        )
        
        if result.success:
            output = result.globals.get("output", "No output variable defined")
            ctx.send_dict({"status": "success", "output": output})
        else:
            ctx.send_dict({"status": "error", "error": result.error})
```

## Execution Results

The `execute()` method returns an `ExecutionResult` object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Whether the execution was successful |
| `error` | `str` | Error message if `success` is `False` |
| `stdout` | `str` | Captured standard output |
| `stderr` | `str` | Captured standard error |
| `globals` | `Dict[str, Any]` | Global variables after execution (if `return_globals` specified) |

## State Management

The `PythonExecExecutor` preserves state between executions for the same agent. This means:

1. Variables defined in one execution are available in the next
2. Functions and classes persist across executions
3. Each agent gets its own isolated execution environment

## Security Considerations

To prevent security issues:

- Carefully select which imports to whitelist
- Never whitelist system modules that can execute shell commands (`os`, `subprocess`, etc.)
- Use input validation before passing user-generated code to the executor
- Monitor resource usage to prevent runaway computations
- Consider using timeouts for code execution

## Example: Data Analysis Agent

```python
@agent.processor(clz=AnalysisRequest, depends_on=["code_executor"])
def run_analysis(self, ctx: agent.ProcessContext, code_executor: PythonExecExecutor):
    # Let's assume we have pandas whitelisted
    code = """
    import pandas as pd
    
    # Process the input data
    df = pd.DataFrame(input_data)
    
    # Perform some analysis
    summary = df.describe()
    correlation = df.corr()
    
    # Set output variable to be returned
    output = {
        "summary": summary.to_dict(),
        "correlation": correlation.to_dict()
    }
    """
    
    result = code_executor.execute(
        code=code,
        globals_dict={"input_data": ctx.payload.data},
        return_globals=["output"]
    )
    
    if result.success:
        ctx.send_dict({"analysis_results": result.globals["output"]})
    else:
        ctx.send_dict({"error": result.error})
```

## Related Resolvers

- [InProcessCodeInterpreterResolver](in_process_interpreter.md) - For simpler code execution needs 