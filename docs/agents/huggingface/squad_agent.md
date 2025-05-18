# SquadAgent

The `SquadAgent` is a question-answering agent that uses a model trained on the Stanford Question Answering Dataset (SQuAD) to extract answers from provided context.

## Purpose

This agent provides extractive question-answering capabilities within a RusticAI guild. Given a context passage and a question, it can locate and extract the relevant answer from the context, enabling precise information retrieval.

## When to Use

Use the `SquadAgent` when your application needs to:

- Extract specific information from longer text passages
- Answer factual questions based on provided context
- Implement extractive question-answering functionality
- Retrieve precise answers rather than generated responses
- Process documents and extract key information

## Message Types

### Input Messages

#### QuestionWithContext

A request containing a question and its context:

```python
class QuestionWithContext(BaseModel):
    context: str  # The text passage containing the answer
    question: str  # The question to answer
```

### Output Messages

#### SquadAnswer

The answer extracted from the context:

```python
class SquadAnswer(BaseModel):
    text: str  # The extracted answer text
```

#### ErrorMessage

Sent when question answering fails:

```python
class ErrorMessage(BaseModel):
    agent_type: str
    error_type: str  # "InferenceError"
    error_message: str
```

## Behavior

1. The agent receives a `QuestionWithContext` message with a context passage and a question
2. It formats the input for the SQuAD model (deepset/roberta-base-squad2)
3. The request is sent to the Hugging Face Inference API
4. The model extracts the most relevant answer span from the context
5. The agent returns a `SquadAnswer` with the extracted text
6. If any errors occur, an `ErrorMessage` is sent

## Sample Usage

```python
from rustic_ai.core.guild.builders import AgentBuilder
from rustic_ai.huggingface.agents.nlp.squad_agent import SquadAgent

# Create the agent spec
squad_agent_spec = (
    AgentBuilder(SquadAgent)
    .set_id("qa_agent")
    .set_name("Question Answering")
    .set_description("Extracts answers from context using SQuAD")
    .build_spec()
)

# Add to guild
guild_builder.add_agent_spec(squad_agent_spec)
```

## Example Request

```python
from rustic_ai.huggingface.agents.nlp.squad_agent import QuestionWithContext

# Create a question-answering request
qa_request = QuestionWithContext(
    context="The Taj Mahal, found in the Indian state of Uttar Pradesh, is one of the Seven Wonders of the Modern World. It was built in the 17th century by Mughal emperor Shah Jahan as a mausoleum for his third wife, Mumtaz Mahal. The Taj Mahal is a fine example of Mughal architecture, which is a blend of Islamic, Persian, Turkish and Indian architectural styles.",
    question="Who was Mumtaz Mahal?"
)

# Send to the agent
client.publish("default_topic", qa_request)
```

## Example Response

The agent responds with a `SquadAnswer`:

```python
SquadAnswer(
    text="his third wife"
)
```

## Technical Details

The agent leverages:
- Hugging Face's Inference API
- deepset/roberta-base-squad2 model, a RoBERTa model fine-tuned on SQuAD 2.0
- Inherits from `HuggingfaceInferenceMixin` to handle API communication

## Notes and Limitations

- Requires a Hugging Face API key set as the `HUGGINGFACE_API_KEY` environment variable
- Only performs extractive QA (extracts spans from the context, doesn't generate new text)
- Performance depends on the relevance of the provided context
- Questions must be answerable from the given context
- The model works best with factual, specific questions
- Context length is limited; very long contexts may need to be split
- Performance may vary based on context complexity and question type
- The agent operates in REMOTE mode, relying on the Hugging Face API rather than local inference 