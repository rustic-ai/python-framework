# LangChain Integration

This section contains documentation for RusticAI's LangChain integration, which allows you to leverage LangChain components within your RusticAI agent applications.

## Overview

LangChain is a framework for developing applications powered by language models. The RusticAI LangChain integration enables you to:

- Use LangChain components within RusticAI agents
- Leverage LangChain tools and utilities
- Access LangChain's document loaders and retrievers
- Integrate LangChain's memory systems

## Features

- **LangChain Agent Integration** - Use LangChain agents within RusticAI guilds
- **Tool Compatibility** - Access LangChain's extensive tool ecosystem
- **Document Processing** - Use LangChain's document processing capabilities
- **Memory Systems** - Leverage LangChain's conversation memory mechanisms

## Getting Started

To use the LangChain integration, you'll need:

1. LangChain installed in your environment
2. RusticAI core framework configured properly
3. Any necessary API keys for specific LangChain features

### Basic Example

```python
from rustic_ai.langchain.adapters import LangChainToolAdapter
from langchain.tools import WikipediaQueryRun
from langchain.utilities import WikipediaAPIWrapper

# Create a LangChain tool
wikipedia_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

# Adapt it for use in RusticAI
adapted_tool = LangChainToolAdapter(tool=wikipedia_tool)

# Now you can use this tool within your RusticAI agents
```

## Documentation

Comprehensive documentation for all LangChain integration features is currently under development. Please check back for updates as we expand this section. 