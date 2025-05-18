# MarvinAgent

The `MarvinAgent` is a specialized agent that provides text classification and data extraction capabilities using Prefect's Marvin library, enabling structured information retrieval from unstructured text.

## Purpose

This agent serves as a bridge to Marvin's AI-powered classification and extraction capabilities. It can categorize text into predefined categories and extract structured data based on specified schemas, turning unstructured text into structured information.

## When to Use

Use the `MarvinAgent` when your application needs to:

- Classify text into predefined categories
- Extract structured information from unstructured text
- Convert natural language to structured data
- Implement intent recognition in conversational systems
- Parse complex text into standardized formats
- Extract entities, attributes, or key information from text

## Message Types

### Input Messages

#### ClassifyRequest

A request to classify text into one of several categories:

```python
class ClassifyRequest(BaseModel):
    source_text: str  # The text to classify
    categories: List[str]  # List of possible categories
    instructions: Optional[str] = None  # Optional additional instructions
```

#### ExtractRequest

A request to extract structured data from text:

```python
class ExtractRequest(BaseModel):
    source_text: str  # The text to extract data from
    extraction_spec: ExtractionSpec  # Specification for extraction
```

Where `ExtractionSpec` defines:
```python
class ExtractionSpec(BaseModel):
    extraction_class: Type  # Pydantic model defining the data structure to extract
    extraction_instructions: Optional[str] = None  # Optional instructions
```

#### ClassifyAndExtractRequest

A request to both classify text and extract relevant data based on the classification:

```python
class ClassifyAndExtractRequest(BaseModel):
    source_text: str  # The text to process
    categories: List[str]  # Possible categories for classification
    classification_instructions: Optional[str] = None  # Instructions for classification
    category_to_extraction_class: Dict[str, Type]  # Mapping categories to extraction models
    category_to_extraction_instructions: Dict[str, str] = {}  # Instructions for each category
```

### Output Messages

#### ClassifyResponse

Response to a classification request:

```python
class ClassifyResponse(BaseModel):
    source_text: str  # The original text
    category: str  # The identified category
```

#### ExtractResponse

Response to an extraction request:

```python
class ExtractResponse(BaseModel):
    source_text: str  # The original text
    extracted_data: Any  # The extracted structured data
```

#### ClassifyAndExtractResponse

Response to a combined classify and extract request:

```python
class ClassifyAndExtractResponse(BaseModel):
    source_text: str  # The original text
    category: str  # The identified category
    extracted_data: Any  # The extracted data
```

## Behavior

### Classification

1. The agent receives a `ClassifyRequest` with text and possible categories
2. It calls Marvin's classification function to identify the most appropriate category
3. The agent returns a `ClassifyResponse` with the identified category

### Extraction

1. The agent receives an `ExtractRequest` with text and an extraction specification
2. It calls Marvin's extraction function to parse the text into the specified structure
3. The agent returns an `ExtractResponse` with the extracted data

### Combined Classification and Extraction

1. The agent receives a `ClassifyAndExtractRequest` with text, categories, and extraction specifications
2. It first classifies the text into one of the provided categories
3. Based on the classification, it selects the appropriate extraction model
4. It extracts structured data using the selected model
5. The agent returns a `ClassifyAndExtractResponse` with both the category and extracted data

## Sample Usage

```python
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.marvin.classifier_agent import MarvinAgent

# Create the agent spec
marvin_agent_spec = (
    AgentBuilder(MarvinAgent)
    .set_id("classifier_extractor")
    .set_name("Text Analyzer")
    .set_description("Classifies text and extracts structured data")
    .build_spec()
)

# Add to guild
guild_builder.add_agent_spec(marvin_agent_spec)
```

## Example Classification Request

```python
from rustic_ai.core.agents.commons import ClassifyRequest

# Define some categories
categories = ["complaint", "inquiry", "feedback", "support_request"]

# Create a classification request
classify_request = ClassifyRequest(
    source_text="I've been trying to access my account for two days but keep getting an error message. Can someone help me?",
    categories=categories,
    instructions="Classify customer service messages"
)

# Send to the agent
client.publish("default_topic", classify_request)
```

## Example Extraction Request

```python
from pydantic import BaseModel
from rustic_ai.core.agents.commons import ExtractRequest, ExtractionSpec

# Define an extraction model
class CustomerIssue(BaseModel):
    problem_type: str
    duration: str
    urgency_level: str
    requires_account_access: bool

# Create an extraction request
extract_request = ExtractRequest(
    source_text="I've been trying to access my account for two days but keep getting an error message. Can someone help me?",
    extraction_spec=ExtractionSpec(
        extraction_class=CustomerIssue,
        extraction_instructions="Extract details about customer service issues"
    )
)

# Send to the agent
client.publish("default_topic", extract_request)
```

## Technical Details

The agent uses:
- Prefect's Marvin library for classification and extraction
- Asynchronous processing for classification requests
- Synchronous processing for combined classification and extraction

## Notes and Limitations

- Requires the Marvin library, which in turn uses LLMs for its functionality
- Quality of classification and extraction depends on the clarity of instructions
- Classification works best with well-defined, distinct categories
- Extraction is more reliable with clearly structured data in the source text
- More complex extraction schemas may require more detailed instructions
- For best results, provide clear examples in extraction instructions
- Marvin may use API calls to external LLMs, which could have rate limits or costs
- Classification and extraction quality depend on the underlying LLM used by Marvin 