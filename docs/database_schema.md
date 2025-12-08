# Database Schema

The application uses **SQLite** as the relational database, managed via **SQLAlchemy** ORM.

**File**: `server/database.py`

## Tables

### 1. `users`
Stores all registered users for the system.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique User ID |
| `username` | String | Unique login name |
| `hashed_password` | String | Bcrypt hash of the password |
| `role` | String | Role: `admin`, `doctor`, `patient` |

### 2. `records`
Stores the audio session metadata, transcription, and AI analysis results.

**Core Data**
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique Record ID |
| `filename` | String | Original filename of the upload |
| `status` | String | `processing`, `completed`, `failed` |
| `created_at` | DateTime | Upload timestamp (UTC) |

**Transcripts (Large Text)**
| Column | Type | Description |
| :--- | :--- | :--- |
| `raw_transcript` | Text | JSON dump of the whisper segments |
| `full_transcript` | Text | Formatted "Speaker: Text" string |
| `redacted_transcript` | Text | PII-redacted version of full_transcript |
| `soap_summary` | Text | The AI-generated SOAP Note |

**Analytics**
| Column | Type | Description |
| :--- | :--- | :--- |
| `duration` | Float | Audio duration in seconds |
| `word_count` | Integer | Total word count |
| `confidence` | Float | Average transcription confidence (0.0 - 1.0) |
| `speaker_count` | Integer | Number of distinct speakers |

**AI Metadata**
| Column | Type | Description |
| :--- | :--- | :--- |
| `sentiment` | String | Overall sentiment of the session |
| `medical_tags` | Text | JSON string array of tags |
| `action_items` | Text | JSON string array of tasks |

**Relationships**
| Column | Type | Description |
| :--- | :--- | :--- |
| `doctor_id` | FK (`users.id`) | The doctor who performed the session |
| `patient_id` | FK (`users.id`) | The patient the session is for |

## Relationships
*   **One-to-Many**: A `User` (Doctor) can have many `Record`s.
*   **One-to-Many**: A `User` (Patient) can have many `Record`s.
