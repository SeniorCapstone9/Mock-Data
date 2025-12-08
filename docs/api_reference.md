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
