# PlaywrightScraperAgent

The `PlaywrightScraperAgent` is a web scraping agent that uses the [Playwright](https://playwright.dev/) framework to automate browser interactions and extract content from web pages.

## Purpose

This agent provides automated web scraping capabilities within a RusticAI guild, enabling retrieval of web content for further processing. It's designed to handle requests for scraping multiple URLs and returns the scraped content in the requested format.

## When to Use

Use the `PlaywrightScraperAgent` when your application needs to:

- Extract content from web pages
- Store web content for later analysis
- Convert HTML content to more processable formats like Markdown
- Get web content for LLM processing or other AI tasks

## Dependencies

The `PlaywrightScraperAgent` requires:

- **filesystem** (Guild-level dependency): A file system implementation for storing scraped content

## Message Types

### Input Messages

#### WebScrapingRequest

A request to scrape web pages.

```python
class WebScrapingRequest(BaseModel):
    id: str  # ID of the request
    links: List[MediaLink]  # URLs to scrape
    output_format: ScrapingOutputFormat = ScrapingOutputFormat.TEXT_HTML  # Output format
    transformer_options: JsonDict = {}  # Options for transforming the content
```

The `ScrapingOutputFormat` enum supports:
- `TEXT_HTML`: Returns the content as HTML
- `MARKDOWN`: Converts the HTML to Markdown before returning

### Output Messages

#### MediaLink

For each URL successfully scraped, a `MediaLink` message is emitted with the scraped content:

```python
class MediaLink(BaseModel):
    url: str  # Path to the scraped file
    name: str  # Filename
    metadata: Dict  # Metadata including original URL, title, etc.
    on_filesystem: bool  # Always True for scraped content
    mimetype: str  # Content type
    encoding: str  # Always "utf-8"
```

#### WebScrapingCompleted

Sent when all requested URLs have been processed:

```python
class WebScrapingCompleted(BaseModel):
    id: str  # ID of the original request
    links: List[MediaLink]  # List of all successfully scraped URLs
```

#### ErrorMessage

Sent when scraping fails for a specific URL:

```python
class ErrorMessage(BaseModel):
    agent_type: str
    error_type: str
    error_message: str
```

## Behavior

1. The agent launches a headless Chrome browser using Playwright
2. For each URL in the request:
   - Navigates to the URL
   - Checks for successful HTTP status (200)
   - Extracts the page content
   - Transforms the content (to Markdown if requested)
   - Stores the content to the filesystem
   - Emits a MediaLink message for the stored content
3. After processing all URLs, it emits a WebScrapingCompleted message

The scraped content is saved in the `scraped_data/` directory with filenames based on a hash of the content.

## Sample Usage

```python
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.core.guild.agent_ext.depends.dependency_resolver import DependencySpec
from rustic_ai.playwright.agent import PlaywrightScraperAgent

# Define a file system dependency
filesystem = DependencySpec(
    class_name="rustic_ai.core.guild.agent_ext.depends.filesystem.FileSystemResolver",
    properties={
        "path_base": "/tmp",
        "protocol": "file",
        "storage_options": {
            "auto_mkdir": True,
        },
    },
)

# Create the agent spec
playwright_agent_spec = (
    AgentBuilder(PlaywrightScraperAgent)
    .set_id("web_scraper")
    .set_name("Web Scraper")
    .set_description("Scrapes web content using Playwright")
    .build_spec()
)

# Add dependency to guild when launching
guild_builder.add_dependency("filesystem", filesystem)
guild_builder.add_agent_spec(playwright_agent_spec)
```

## Example Request

```python
from rustic_ai.core.agents.commons.media import MediaLink
from rustic_ai.playwright.agent import WebScrapingRequest, ScrapingOutputFormat

# Create a request to scrape two URLs and convert to Markdown
request = WebScrapingRequest(
    links=[
        MediaLink(url="https://example.com"),
        MediaLink(url="https://rustic.ai/docs"),
    ],
    output_format=ScrapingOutputFormat.MARKDOWN
)

# Send to the agent via messaging system
client.publish("default_topic", request)
```

## Notes and Limitations

- The agent requires a working installation of Playwright and a browser
- For security, it's recommended to run with appropriate sandboxing
- Consider rate limiting and respecting robots.txt for production use
- Large pages may consume significant memory 