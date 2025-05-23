# FileSystemResolver

The `FileSystemResolver` provides agents with secure, configurable access to the file system. It creates an isolated filesystem view for each agent, ensuring separation of concerns and preventing agents from accessing files outside their designated areas.

## Overview

- **Type**: `DependencyResolver[FileSystem]`
- **Provided Dependency**: `fsspec.implementations.dirfs.DirFileSystem`
- **Package**: `rustic_ai.core.guild.agent_ext.depends.filesystem.filesystem`

## Configuration

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `path_base` | `str` | Base path for files; agent directories will be created under this path | Required |
| `protocol` | `str` | File system protocol to use (e.g., 'file', 's3', 'gcs') | Required |
| `storage_options` | `dict` | Protocol-specific options for the underlying filesystem | Required |

## Usage

### Guild Configuration

```python
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.guild.dsl import DependencySpec

guild_builder = (
    GuildBuilder("my_guild", "File System Guild", "Guild with file system access")
    .add_dependency_resolver(
        "filesystem",
        DependencySpec(
            class_name="rustic_ai.core.guild.agent_ext.depends.filesystem.filesystem.FileSystemResolver",
            properties={
                "path_base": "/tmp/rusticai/files",
                "protocol": "file",
                "storage_options": {}
            }
        )
    )
)
```

### Agent Usage

```python
from fsspec.implementations.dirfs import DirFileSystem
from rustic_ai.core.guild import Agent, agent

class FileAgent(Agent):
    @agent.processor(clz=FileRequest, depends_on=["filesystem"])
    def handle_file_request(self, ctx: agent.ProcessContext, filesystem: DirFileSystem):
        # Use filesystem to read/write files
        with filesystem.open("data.txt", "w") as f:
            f.write("Hello, World!")
            
        with filesystem.open("data.txt", "r") as f:
            content = f.read()
            
        ctx.send_dict({"content": content})
```

## Path Isolation

The resolver creates agent-specific paths using the pattern:

```
{path_base}/{guild_id}/{agent_id}/
```

This ensures each agent has its own isolated file space, preventing one agent from accessing another's files.

## Supported Backends

`FileSystemResolver` leverages [fsspec](https://filesystem-spec.readthedocs.io/), which supports multiple storage backends:

- Local file system (`file://`)
- Amazon S3 (`s3://`)
- Google Cloud Storage (`gcs://`)
- Azure Blob Storage (`abfs://`)
- HDFS (`hdfs://`)
- HTTP/HTTPS (`http://`, `https://`)
- And many more

To use a particular backend, specify the appropriate protocol and include any authentication details in `storage_options`.

## Example: S3 Configuration

```python
DependencySpec(
    class_name="rustic_ai.core.guild.agent_ext.depends.filesystem.filesystem.FileSystemResolver",
    properties={
        "path_base": "my-bucket/agent-files",
        "protocol": "s3",
        "storage_options": {
            "key": "AWS_ACCESS_KEY",
            "secret": "AWS_SECRET_KEY",
            "client_kwargs": {"region_name": "us-west-2"}
        }
    }
)
```

## Security Considerations

- Ensure the `path_base` is in a safe location that doesn't contain sensitive system files
- When using cloud storage, follow the principle of least privilege for access credentials
- Consider implementing additional checks for sensitive operations in your agent code 