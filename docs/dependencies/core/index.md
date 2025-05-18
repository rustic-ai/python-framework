# Core Dependencies

The Core package provides several essential dependency resolvers that form the foundation of RusticAI's dependency injection system.

## Available Resolvers

- [FileSystemResolver](filesystem.md) - Provides access to file system operations with configurable base paths and protocols
- [InMemoryKVStoreResolver](in_memory_kvstore.md) - Simple key-value store backed by in-memory storage
- [PythonExecExecutorResolver](python_exec_executor.md) - Safe execution of Python code with configurable import restrictions
- [InProcessCodeInterpreterResolver](in_process_interpreter.md) - In-process Python code interpretation for agent code execution
- [EnvSecretProviderResolver](env_secret_provider.md) - Environment variable-based secret management

## Usage

Core dependencies can be used across any agent in the RusticAI ecosystem. They provide fundamental capabilities like storage, code execution, and security that are useful in many agent scenarios.

For details on how to configure and use each resolver, please refer to the specific documentation links above. 