# Frontend Developer Guide

The client is a Single Page Application (SPA) built with React and Vite.

## Directory Structure
```
client/src/
├── components/          # React Components
│   ├── AdminDashboard.jsx
│   ├── Dashboard.jsx    # Doctor's Dashboard
│   ├── Login.jsx
│   ├── PatientPortal.jsx
│   ├── Recorder.jsx     # Audio Capture Logic
│   └── Results.jsx      # Detail View
├── App.jsx              # Main Router
└── main.jsx             # Entry Point
```

## Key Components

### `Recorder.jsx`
*   **Goal**: Capture audio from the microphone and upload it found in `Dashboard.jsx`.
*   **Logic**:
    1.  Uses `navigator.mediaDevices.getUserMedia`.
    2.  Collects audio chunks into a `Blob`.
    3.  Once stopped, converts to a File object.
    4.  POSTs to `/api/upload` via `axios`.
*   **State**: Tracks recording time and status.

### `Results.jsx`
*   **Goal**: Display the completed session data.
*   **Logic**:
    1.  Fetches data from `/api/results/{id}`.
    2.  Parses the JSON strings for `medical_tags` and `action_items`.
    3.  Renders the SOAP note and Transcripts in tabs/sections.

### `AdminDashboard.jsx`
*   **Goal**: System management.
*   **Features**:
    *   **User Creation Form**: Adds new users to `users` table.
    *   **Charts**: Uses `recharts` to visualize global tag trends fetched from `/api/analytics`.

## Routing & Navigation
Routing is handled by `react-router-dom` in `App.jsx`.

*   `/login` -> `Login.jsx`
*   `/dashboard` -> `Dashboard.jsx` (Protected: Doctor)
*   `/admin` -> `AdminDashboard.jsx` (Protected: Admin)
*   `/portal` -> `PatientPortal.jsx` (Protected: Patient)
*   `/results/:id` -> `Results.jsx` (Protected)

## Styling
*   Uses standard CSS files.
*   **Theme**: Dark mode variables defined in `index.css` (e.g., `--primary`, `--bg-main`).
