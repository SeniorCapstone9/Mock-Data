# Authentication & Security

This system implements Role-Based Access Control (RBAC) using JWT (JSON Web Tokens).

## Authentication Flow

1.  **Login**: User submits username/password to `POST /token`.
2.  **Verification**: Server hashes the password (bcrypt) and compares it with the stored hash.
3.  **Token Generation**: If valid, the server signs a JWT containing the `sub` (username) and `role`.
    *   **Algorithm**: HS256
    *   **Expiry**: 30 minutes (configurable in `auth.py`)
4.  **Storage**: Client stores the token in `localStorage`.
5.  **Requests**: All protected endpoints require the `Authorization: Bearer <token>` header.

## User Roles

The system is designed with three distinct roles:

### 1. Admin (`role="admin"`)
*   **Permissions**: Full system access.
*   **Capabilities**:
    *   Create new accounts (Doctors, Patients, other Admins).
    *   View all user accounts.
    *   View *global* analytics trends.
    *   View *all* transcripts (but sees the **Redacted** version by default in the list view logic).
*   **Dashboard**: `AdminDashboard.jsx`

### 2. Doctor (`role="doctor"`)
*   **Permissions**: Clinical access.
*   **Capabilities**:
    *   Record/Upload new audio sessions.
    *   View only *their own* patient encounters (linked via `doctor_id`).
    *   View full unredacted transcripts and SOAP notes.
*   **Dashboard**: `Dashboard.jsx`

### 3. Patient (`role="patient"`)
*   **Permissions**: Personal access.
*   **Capabilities**:
    *   View only *their own* medical records (linked via `patient_id`).
    *   Cannot upload or edit records.
*   **Portal**: `PatientPortal.jsx`

## Security Implementation Details

*   **File**: `server/auth.py`
    *   `get_current_user`: Decodes JWT and retrieves user.
    *   `get_current_active_admin`: Dependency that enforces Admin role.
    *   `get_current_doctor`: Dependency that enforces Doctor or Admin role.
*   **Password Hashing**: Uses `passlib` with `bcrypt`.
*   **Environment**: The `SECRET_KEY` is loaded from the `.env` file. **Crucial**: This must be changed from the default for production.

## Default Credentials
On first run, the system creates a default superuser:
*   **Username**: `admin`
*   **Password**: `admin`
