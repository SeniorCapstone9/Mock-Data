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


### 3. `scanned_notes`
Stores images and OCR text from physical notes.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique ID |
| `image_path` | String | Local path to the saved image |
| `extracted_text` | Text | Full text extracted via OCR |
| `created_at` | DateTime | Timestamp |
| `doctor_id` | FK (`users.id`) | Doctor who scanned the note |

### 4. `notification_visits`
Stores structured visit inputs for the standalone notification subsystem.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique ID |
| `visit_date` | Date | Visit day (`YYYY-MM-DD`) |
| `location` | String | State code (`FL`, `CA`) |
| `symptoms_json` | Text | JSON string array of symptoms |
| `source` | String | Data source (`temp`, `import`, `mock`) |
| `created_at` | DateTime | Insert timestamp |

### 5. `notifications`
Stores generated symptom alerts.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique alert ID |
| `created_at` | DateTime | Alert upsert timestamp |
| `group_date` | Date | Grouped date key |
| `location` | String | State code |
| `symptom` | String | Canonical symptom name |
| `severity` | String | `info`, `warning`, `critical` |
| `total_visits` | Integer | Total visits in the date/location group |
| `symptom_count` | Integer | Visits containing this symptom |
| `rate` | Float | `symptom_count / total_visits` |
| `threshold_used` | Float | Matched threshold value |
| `message` | Text | Human-readable alert message |

**Constraint**
* Unique key on (`group_date`, `location`, `symptom`) for upsert behavior.

### 6. `notification_deliveries`
Stores email/SMS delivery attempts for notification alerts.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Unique delivery ID |
| `notification_id` | FK (`notifications.id`) | Notification being delivered |
| `channel` | String | `email` (SMS reserved for future extension) |
| `recipient` | String | Email address or E.164 phone number |
| `status` | String | `sent` or `failed` |
| `provider` | String | `smtp` (Twilio reserved for future extension) |
| `error_message` | Text | Provider error (if failed) |
| `created_at` | DateTime | Attempt timestamp |

## Relationships
*   **One-to-Many**: A `User` (Doctor) can have many `Record`s.
*   **One-to-Many**: A `User` (Patient) can have many `Record`s.
*   **One-to-Many**: A `User` (Doctor) can have many `ScannedNote`s.
