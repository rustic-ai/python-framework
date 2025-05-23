# InProcessCodeInterpreterResolver

The `InProcessCodeInterpreterResolver` provides a lightweight Python code execution environment that runs code directly in the current process. It offers a simpler alternative to `PythonExecExecutorResolver` for cases where full isolation isn't required.

## Overview

- **Type**: `DependencyResolver[CodeRunner]`
- **Provided Dependency**: `InProcessCodeInterpreter`
- **Package**: `rustic_ai.core.guild.agent_ext.depends.code_execution.stateless.in_process_interpreter`

## Features

- **Fast Execution**: Runs code directly in the current process without spawning subprocesses
- **Stateless**: Each execution is independent (no variables persisting between runs)
- **Lightweight**: Minimal overhead compared to other execution methods
- **Simple API**: Easy-to-use interface for basic code execution needs

## Limitations

- **Security**: Less isolated than other executors - use only with trusted code
- **Stateless**: Variables don't persist between executions (by design)
- **Resource Management**: Shares resources with the main application

## Configuration

The resolver has minimal configuration options:

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `timeout_seconds` | `int` | Maximum execution time in seconds | `5` |

## Usage

### Guild Configuration

```python
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.guild.dsl import DependencySpec

guild_builder = (
    GuildBuilder("simple_code_guild", "Simple Code Guild", "Guild with basic Python execution")
    .add_dependency_resolver(
        "code_runner",
        DependencySpec(
            class_name="rustic_ai.core.guild.agent_ext.depends.code_execution.stateless.in_process_interpreter.InProcessCodeInterpreterResolver",
            properties={
                "timeout_seconds": 10
            }
        )
    )
)
```

### Agent Usage

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.agent_ext.depends.code_execution.stateless.in_process_interpreter import InProcessCodeInterpreter

class SimpleCodeAgent(Agent):
    @agent.processor(clz=SimpleCodeRequest, depends_on=["code_runner"])
    def run_simple_code(self, ctx: agent.ProcessContext, code_runner: InProcessCodeInterpreter):
        code = ctx.payload.code
        
        # Execute the code
        result = code_runner.run(code)
        
        if result.success:
            ctx.send_dict({
                "status": "success",
                "output": result.output,
                "result_value": result.result
            })
        else:
            ctx.send_dict({
                "status": "error",
                "error": result.error
            })
```

## Execution Results

The `run()` method returns a `CodeRunResult` object with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Whether the execution was successful |
| `error` | `str` | Error message if `success` is `False` |
| `output` | `str` | Captured standard output |
| `result` | `Any` | The value of the last expression evaluated |

## Example: Simple Calculation

```python
@agent.processor(clz=CalculationRequest, depends_on=["code_runner"])
def perform_calculation(self, ctx: agent.ProcessContext, code_runner: InProcessCodeInterpreter):
    expression = ctx.payload.expression
    
    # Safe way to calculate expressions
    code = f"""
    result = {expression}
    print(f"Calculating: {expression} = {{result}}")
    """
    
    result = code_runner.run(code)
    
    if result.success:
        ctx.send_dict({
            "expression": expression,
            "result": result.result,
            "calculation_log": result.output
        })
    else:
        ctx.send_dict({
            "expression": expression,
            "error": result.error
        })
```

## Security Considerations

The `InProcessCodeInterpreter` runs code directly in the same process as your application, which means:

1. **Use only with trusted code**: Never run untrusted user input through this interpreter
2. **Resource access**: Code has access to the same resources as your application
3. **Imports**: All available Python modules can be imported
4. **System calls**: System operations can be performed if the relevant modules are imported

For executing untrusted code, use `PythonExecExecutorResolver` which provides better isolation.

## Use Cases

- **Simple calculations**: Evaluate mathematical expressions
- **Data transformations**: Apply simple transformations to data
- **Testing**: Quick execution of agent-generated code in development
- **Configuration evaluation**: Dynamic configuration logic

## When to Use

Choose `InProcessCodeInterpreterResolver` when:

- You need simple, fast code execution
- The code is trusted (not from external users)
- You don't need state to persist between executions
- The lower overhead compared to `PythonExecExecutorResolver` is beneficial

## Related Resolvers

- [PythonExecExecutorResolver](python_exec_executor.md) - For stateful, secure Python execution with better isolation 