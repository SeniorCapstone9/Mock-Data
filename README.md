# AI Medical Scribe Demo

This is a demonstration of an AI-powered Medical Scribe application. It records audio, transcribes it, diarizes speakers (Doctor/Patient), and uses local LLMs (Ollama) to generate SOAP notes, titles, and clinical analytics.

## Prerequisites

Before running the application, ensure you have the following installed:

1.  **Node.js & npm** (for the client) - [Download](https://nodejs.org/)
2.  **Python 3.10+** (for the server) - [Download](https://www.python.org/downloads/)
3.  **FFmpeg** (System dependency for audio processing)
    *   **Mac**: `brew install ffmpeg`
    *   **Windows**: [Download](https://ffmpeg.org/download.html) and add to PATH.
    *   **Linux**: `sudo apt install ffmpeg`
4.  **Ollama** (for local LLM inference) - [Download](https://ollama.com/)
    *   **Important**: You must pull the `llama3` model before running.
    *   Run: `ollama pull llama3`

## Installation

### 1. Clone the Repository

```bash
git clone <repository_url>
cd demoSTT
```

### 2. Server Setup

Navigate to the server directory and set up the Python environment.

```bash
cd server
```

**Create and Activate Virtual Environment:**

*   **Mac/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
*   **Windows:**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

**Install Dependencies:**

```bash
pip install -r requirements.txt
```

**Environment Variables:**

Create a `.env` file in the `server` directory. You can copy the example:

```bash
cp .env.example .env
```

Edit `.env` and add your HuggingFace Token (Required for Speaker Diarization):
*   To get a token, sign up at [HuggingFace](https://huggingface.co/settings/tokens).
*   You must also accept the user agreement key for `pyannote/speaker-diarization-3.1`.

### 3. Client Setup

Open a new terminal window, navigate to the client directory, and install dependencies.

```bash
cd client
npm install
```

---

## Running the Application

### 1. Start Ollama
Ensure Ollama is running in the background.
```bash
ollama serve
```

### 2. Start the Server
In your `server` terminal (with venv activated):

```bash
uvicorn main:app --reload --port 8002
```
*The server will start at `http://localhost:8002`. On first run, it will automatically create the database and a default admin user.*

### 3. Start the Client
In your `client` terminal:

```bash
npm run dev
```
*The client will start at `http://localhost:5173` (or similar).*

---

## Usage

### Logging In
Go to the client URL (e.g., `http://localhost:5173`). Login with the default admin credentials:

*   **Username:** `admin`
*   **Password:** `admin`

### Troubleshooting "Admin Not Working"
If you receive "Invalid credentials" or the login fails:

1.  **Check the Port**: The client is hardcoded to look for the server at `http://localhost:8002`. Ensure you started the server with `--port 8002`. If it's running on port 8000 (default), the connection will fail, but the error message will still say "Invalid credentials".
2.  **Reset Database**:
    *   Stop the server.
    *   Delete `server/medical_scribe.db`.
    *   Restart the server. The `admin` user will be recreated.
3.  **Check Logs**: Look at the terminal running the server. If you don't see any request when you click "Sign In", the client can't reach the server (likely port issue).

### Common Issues
*   **"Ollama Error"**: Make sure `ollama serve` is running and you have run `ollama pull llama3`.
*   **"Diarization Error"**: Ensure your `HF_TOKEN` is valid in `.env` and you have accepted the terms on HuggingFace for the `pyannote/speaker-diarization-3.1` model.

## Documentation

For detailed information on how the system works, check out the full documentation in the `docs/` folder:

*   **[System Architecture](docs/architecture.md)**: High-level overview and tech stack.
*   **[Authentication & Security](docs/authentication.md)**: How login, JWT, and Roles work.
*   **[Transcription Pipeline](docs/transcription_pipeline.md)**: Details on Whisper, Pyannote, and audio processing.
*   **[AI Analysis](docs/ai_analysis.md)**: How Ollama generates SOAP notes and analytics.
*   **[Database Schema](docs/database_schema.md)**: Breakdown of the User and Record tables.
*   **[Frontend Guide](docs/frontend_guide.md)**: Component structure and routing.
*   **[API Reference](docs/api_reference.md)**: List of all backend endpoints.
