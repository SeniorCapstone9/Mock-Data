# AI Analysis & Clinical Intelligence

After the transcript is generated, the system uses a local Large Language Model (LLM) to extract clinical insights.

**Engine**: Ollama
**Model**: `llama3`

## Features

All AI processing is defined in `server/services.py:process_transcript_with_ai`.

### 1. PII Redaction
**Goal**: Remove personally identifiable information (Names, Dates, SSN, etc.) for privacy.
**Prompt Strategy**: "Replace redacted information with [REDACTED]. Keep the speaker labels..."
**Output**: A sanitized version of the full transcript.

### 2. SOAP Note Generation
**Goal**: Create a structured clinical note.
**Format**:
*   **S**ubjective: What the patient says (symptoms, history).
*   **O**bjective: Observations and test results.
*   **A**ssessment: Diagnosis and clinical impression.
*   **P**lan: Treatment, medications, and follow-up.

### 3. Title Generation
**Goal**: Create a concise, human-readable summary title for the dashboard list view.
**Example**: "Cardiology Follow-up", "Pediatric Flu Checkup".

### 4. Advanced Clinical Analytics
**Goal**: Extract structured data for aggregation and trends.
**Format**: JSON

Parsing logic enforces a strict JSON schema from the LLM response to extract:
*   **Sentiment**: (e.g., "Anxious", "Calm", "Painful").
*   **Medical Tags**: List of 3-5 key terms (e.g., "Hypertension", "Type 2 Diabetes").
*   **Action Items**: Concrete tasks for the patient.

## Error Handling

If Ollama is not running or the model is not pulled:
1.  The system catches the exception.
2.  Returns fallback values (e.g., "Untitled Session").
3.  The raw transcript is preserved, but analytics will be empty.
