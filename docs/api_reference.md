# API Reference

Base URL: `http://localhost:8002`

## Authentication

### POST `/token`
Login to get an access token.
*   **Form Data**: `username`, `password`
*   **Returns**: `access_token` (JWT), `role`

## Users

### POST `/api/users` (Admin Only)
Create a new user.
*   **Body**: `{ "username": "...", "password": "...", "role": "..." }`

### GET `/api/users` (Admin Only)
List all users in the system.

### GET `/api/patients` (Doctor/Admin)
List all users with the `patient` role. Used for populating dropdowns.

## Records

### POST `/api/upload`
Upload an audio file to start processing.
*   **Content-Type**: `multipart/form-data`
*   **Fields**:
    *   `file`: The audio file.
    *   `patient_id`: (Optional) ID of the patient.
*   **Returns**: `{ "id": 1, "status": "processing" }`

### GET `/api/records`
List records visible to the current user.
*   **Doctor**: Sees records they created.
*   **Patient**: Sees records assigned to them.
*   **Admin**: Sees all records.

### GET `/api/results/{id}`
Get full details for a specific record.
*   **Returns**: Status, full transcripts, SOAP notes, analytics JSON.
*   **Access Control**: Enforced (Doctors can't see other doctors' patients, Patients can't see other patients).

### GET `/api/analytics`
Get aggregated statistics (Total sessions, word counts, tag clouds).

## Standalone Notification System (Doctor/Admin)

### POST `/api/notification-visits/import`
Import structured visit records in JSON.
*   **Body**:
    *   `{ "visits": [{ "visit_date": "2026-02-16", "location": "FL", "symptoms": ["flu","fever"] }], "source": "temp" }`
*   **Returns**: `{ "inserted": 10, "source": "temp" }`
*   **Notes**:
    *   `temp` is the default source and is intended for test runs.

### POST `/api/notification-visits/import-csv`
Import structured visit records from CSV.
*   **Content-Type**: `multipart/form-data`
*   **Fields**:
    *   `file`: CSV with headers `visit_date,location,symptoms`
    *   `source`: `import` or `mock` (optional)

### GET `/api/notification-visits`
List imported notification-visit records for debugging and validation.
*   **Query Params**: `days`, `location`, `limit`

### POST `/api/notifications/run`
Run the notification engine against `notification_visits` only.
*   **Body**: `{ "days": 7, "symptoms": ["flu"], "source": "temp", "delete_source_after_run": true }` (fields optional)
*   **Returns**: `{ "groups_processed": 5, "source_visits": 120, "alerts_upserted": 8, "deleted_source_visits": 120 }`
*   **Notes**:
    *   Default run mode uses `source=temp` and auto-cleans those visits after each run.

### GET `/api/notifications`
List generated notifications.
*   **Query Params**: `days`, `severity`, `location`, `symptom`, `limit`

### GET `/api/notifications/{id}`
Get details for a single notification.

### GET `/api/notifications/{id}/distribution`
Get symptom distribution for the notification's grouped day/location.

### POST `/api/notifications/{id}/send`
Send a notification to real recipients.
*   **Body**:
    *   `{ "emails": ["ops@example.com"], "include_email": true }`
*   **Notes**:
    *   Current version supports email delivery only.

### GET `/api/notifications/{id}/deliveries`
List delivery attempts for a notification.

Delivery configuration environment variables:
*   `SMTP_HOST` (for Gmail use `smtp.gmail.com`)
*   `SMTP_PORT` (for Gmail use `587`)
*   `SMTP_USER` (sender account email)
*   `SMTP_PASS` (sender account app password)
*   `SMTP_FROM` (sender email shown in outgoing message)
*   `SMTP_USE_TLS` (`true` or `false`, default `true`)
*   `NOTIFICATION_ALWAYS_EMAILS` (optional, comma-separated; blank by default)

## OCR / Notes

### POST `/api/scan-note`
Upload an image (JPEG/PNG) to be scanned.
*   **Content-Type**: `multipart/form-data`
*   **Fields**: `file`
*   **Returns**: `{ "id": 1, "extracted_text": "...", "created_at": "..." }`

### GET `/api/notes`
List all scanned notes for the current doctor.
