# EnvSecretProviderDependencyResolver

The `EnvSecretProviderDependencyResolver` provides a secure way for agents to access sensitive configuration values like API keys, credentials, and tokens from environment variables, without exposing the actual secrets in code or configuration files.

## Overview

- **Type**: `DependencyResolver[SecretProvider]`
- **Provided Dependency**: `EnvSecretProvider`
- **Package**: `rustic_ai.core.guild.agent_ext.depends.secrets.env_secret_provider`

## Features

- **Environment-Based**: Retrieves secrets from environment variables
- **Prefix Support**: Optional prefix for environment variable names
- **Default Values**: Fallback values for missing environment variables
- **Caching**: Secrets are cached for efficient retrieval
- **Guild-Specific Secrets**: Can scope secrets to specific guilds

## Configuration

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `prefix` | `str` | Prefix for environment variable names | `""` (empty string) |
| `default_values` | `Dict[str, str]` | Default values for secrets | `{}` (empty dict) |

## Usage

### Guild Configuration

```python
from rustic_ai.core.guild.builders import GuildBuilder
from rustic_ai.core.guild.dsl import DependencySpec

guild_builder = (
    GuildBuilder("my_guild", "Secret Guild", "Guild with access to environment secrets")
    .add_dependency_resolver(
        "secrets",
        DependencySpec(
            class_name="rustic_ai.core.guild.agent_ext.depends.secrets.env_secret_provider.EnvSecretProviderDependencyResolver",
            properties={
                "prefix": "RUSTICAI_",
                "default_values": {
                    "api_url": "https://api.example.com"
                }
            }
        )
    )
)
```

### Agent Usage

```python
from rustic_ai.core.guild import Agent, agent
from rustic_ai.core.guild.agent_ext.depends.secrets.env_secret_provider import EnvSecretProvider

class ApiAgent(Agent):
    @agent.processor(clz=ApiRequest, depends_on=["secrets"])
    def call_api(self, ctx: agent.ProcessContext, secrets: EnvSecretProvider):
        # Get API key from environment variable RUSTICAI_API_KEY
        api_key = secrets.get_secret("api_key")
        
        # Get API URL from environment variable RUSTICAI_API_URL or use default
        api_url = secrets.get_secret("api_url")
        
        # Use the secrets to make an API call
        response = self._make_api_call(api_url, api_key, ctx.payload.request_data)
        
        ctx.send_dict({"response": response})
        
    def _make_api_call(self, url, key, data):
        # Implementation of API call
        return {"status": "success", "data": "API response"}
```

## Secret Retrieval

The `EnvSecretProvider` class provides these methods:

| Method | Description |
|--------|-------------|
| `get_secret(name: str) -> str` | Get a secret by name |
| `has_secret(name: str) -> bool` | Check if a secret exists |
| `list_available_secrets() -> List[str]` | List all available secret names (without values) |

## Environment Variable Naming

Given a `prefix` of `"RUSTICAI_"` and a secret name `"api_key"`, the resolver will look for an environment variable named `RUSTICAI_API_KEY` (the secret name is automatically upper-cased).

## Security Best Practices

1. **Don't hardcode secrets**: Never include actual secrets in your code or configuration files
2. **Use environment variables**: Set secrets as environment variables or use a secure secret management service
3. **Limit access**: Only provide access to secrets that agents actually need
4. **Rotate secrets**: Regularly update API keys and other credentials
5. **Review logs**: Ensure secrets aren't accidentally logged

## Examples

### Setting Environment Variables

```bash
# Set environment variables before starting your application
export RUSTICAI_API_KEY=your_api_key_here
export RUSTICAI_DATABASE_URL=postgresql://user:password@localhost/db
```

### Using Guild-Specific Secrets

```python
@agent.processor(clz=ConfigRequest, depends_on=["secrets"])
def handle_config(self, ctx: agent.ProcessContext, secrets: EnvSecretProvider):
    # Get guild-specific environment variables if they exist
    # For a guild with ID "payment_guild", will look for RUSTICAI_PAYMENT_GUILD_API_KEY
    guild_api_key = secrets.get_guild_secret(self.guild_id, "api_key")
    
    # Or use a more explicit approach
    payment_key = secrets.get_secret(f"{self.guild_id}_api_key")
    
    ctx.send_dict({"configured": True})
```

### Fallback to Default Values

```python
@agent.processor(clz=ServerRequest, depends_on=["secrets"])
def handle_server_request(self, ctx: agent.ProcessContext, secrets: EnvSecretProvider):
    # If RUSTICAI_SERVER_URL isn't set, will use the default value
    server_url = secrets.get_secret("server_url")
    
    ctx.send_dict({"server": server_url})
```

## Use Cases

- **API Integration**: Securely use API keys for external services
- **Database Access**: Store database connection credentials
- **Authentication**: Manage authentication tokens for services
- **Configuration**: Centralize sensitive configuration
- **Multi-Environment Setup**: Different secrets for development, testing, and production

## Alternative Secret Managers

For more advanced secret management needs, consider:

- Using a cloud-based secret manager (AWS Secrets Manager, Google Secret Manager, Azure Key Vault)
- Implementing a custom `DependencyResolver` that integrates with your preferred secret management solution
- Using Hashicorp Vault or similar tools for enterprise-grade secret management 