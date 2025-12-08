# System Architecture

This document provides a high-level overview of the AI Medical Scribe application architecture.

## Overview

The application is a full-stack web application designed to automatic medical documentation. It captures audio from a doctor-patient encounter, transcribes it, identifies speakers, and uses Generative AI (LLMs) to produce clinical notes and analytics.

## Technology Stack

### Frontend (Client)
*   **Framework**: React 18 (Vite)
*   **Language**: JavaScript (ES6+)
*   **Routing**: React Router DOM
*   **HTTP Client**: Axios
*   **Styling**: Plain CSS (with CSS variables for theming)
*   **Icons**: Lucide React
*   **Visualization**: Recharts (for analytics charts)
*   **Key Components**:
    *   `Recorder.jsx`: Handles browser-based audio recording and blob processing.
    *   `Dashboard.jsx` / `AdminDashboard.jsx`: Role-specific conceptual views.

### Backend (Server)
*   **Framework**: FastAPI (Python 3.10+)
*   **Server**: Uvicorn (ASGI)
*   **Database**: SQLite (local) with SQLAlchemy ORM
*   **Authentication**: OAuth2 with Password Flow (JWT)
*   **Background Tasks**: `fastapi.BackgroundTasks` for non-blocking audio processing.

### AI & ML Pipeline
*   **Transcription**: `faster-whisper` (CTranslate2 backend for optimized inference).
*   **Speaker Diarization**: `pyannote.audio` (Speaker-Diarization-3.1).
*   **Generative AI**: `Ollama` (running `llama3` locally) for NLP tasks.
*   **Audio Processing**: `ffmpeg` for format conversion and normalization.

## Data Flow

1.  **Capture**: User records audio in the browser (`Recorder.jsx`) or uploads a file.
2.  **Upload**: Audio is sent to `POST /api/upload` as `multipart/form-data`.
3.  **Queue**: Server saves the file temporarily and triggers a background task.
4.  **Processing** (Async):
    *   **Convert**: Audio converted to 16kHz Mono WAV.
    *   **Transcribe**: Whisper model converts speech to text segments.
    *   **Diarize**: Pyannote identifies "who spoke when".
    *   **Align**: System merges text segments with speaker labels.
    *   **Analyze**: Transcript is sent to Ollama for:
        *   PII Redaction
        *   SOAP Note Generation
        *   Clinical Analytics (Sentiment, Tags)
5.  **Storage**: Results are saved to the SQLite `records` table.
6.  **Retrieval**: Client polls or fetches `GET /api/results/{id}` to display the processed data.
