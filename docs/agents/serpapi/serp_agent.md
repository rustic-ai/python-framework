# SERPAgent

The `SERPAgent` provides search engine capabilities to a RusticAI guild by integrating with the [SerpAPI](https://serpapi.com/) service, which offers access to search results from various search engines.

## Purpose

This agent allows access to structured search engine results, enabling information retrieval capabilities within a guild. It acts as a bridge between your application and search engines like Google, Bing, DuckDuckGo, and others.

## When to Use

Use the `SERPAgent` when your application needs to:

- Retrieve information from search engines
- Get structured search results for a query
- Access multiple search engines through a unified interface
- Gather web information without directly scraping websites

## Configuration

The `SERPAgent` requires an API key from SerpAPI. This should be set as an environment variable:

```
SERP_API_KEY=your_api_key_here
```

## Message Types

### Input Messages

#### SERPQuery

A request to search for information.

```python
class SERPQuery(BaseModel):
    engine: str  # Search engine to use (google, bing, etc.)
    query: str  # The search query
    id: str = ""  # Optional ID for tracking
    num: Optional[int] = 12  # Number of results to return
    start: Optional[int] = 0  # Starting position for pagination
```

Supported search engines include:
- google
- bing
- baidu
- yahoo
- duckduckgo
- ebay
- yandex
- home_depot
- google_scholar
- youtube
- walmart
- google_maps
- google_patents

### Output Messages

#### SERPResults

Sent when a search is successfully completed:

```python
class SERPResults(BaseModel):
    engine: str  # The engine used for search
    query: str  # The query that was searched
    count: int  # Number of results returned
    id: str = ""  # ID from the original request
    results: List[MediaLink]  # The search results
    total_results: Optional[int] = None  # Total number of results available
```

Each result is a `MediaLink` with metadata containing:
- title: The title of the search result
- favicon: The favicon URL of the result website
- search_position: The position in search results
- snippet: A text snippet from the result
- date: Publication date if available
- query_id: ID of the original query

#### SearchError

Sent when a search fails:

```python
class SearchError(BaseModel):
    id: str = ""  # ID from the original request
    response: JsonDict  # Error details from SerpAPI
```

## Behavior

1. The agent receives a search query with a specified search engine
2. It formats the query appropriately for the chosen search engine
3. The query is sent to SerpAPI
4. Results are transformed into a structured format with rich metadata
5. The agent returns the results as a `SERPResults` message with `MediaLink` objects for each result

## Sample Usage

```python
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.serpapi.agent import SERPAgent

# Create the agent spec
serp_agent_spec = (
    AgentBuilder(SERPAgent)
    .set_id("search_agent")
    .set_name("Search Agent")
    .set_description("Provides search engine results using SerpAPI")
    .build_spec()
)

# Add to guild
guild_builder.add_agent_spec(serp_agent_spec)
```

## Example Request

```python
from rustic_ai.serpapi.agent import SERPQuery

# Create a search request
search_request = SERPQuery(
    engine="google",
    query="rustic ai multi-agent systems",
    num=5  # Request 5 results
)

# Send to the agent
client.publish("default_topic", search_request)
```

## Example Response

The agent responds with a `SERPResults` message containing search results:

```python
SERPResults(
    engine="google",
    query="rustic ai multi-agent systems",
    count=5,
    results=[
        MediaLink(
            url="https://example.com/result1",
            name="result1.html",
            metadata={
                "title": "RusticAI: A Framework for Multi-Agent Systems",
                "snippet": "RusticAI is a powerful framework for building...",
                "search_position": 1,
                # Other metadata...
            },
            mimetype="text/html",
            encoding="utf-8"
        ),
        # More results...
    ],
    total_results=14700
)
```

## Notes and Limitations

- Requires a SerpAPI key with sufficient quota
- Search engines have different parameters and return slightly different result structures
- Rate limits apply based on your SerpAPI subscription level
- Search results reflect what's available through SerpAPI's service, which may have slight delays compared to direct searches 