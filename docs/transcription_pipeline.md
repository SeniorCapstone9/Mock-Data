# Audio Processing & Transcription Pipeline

The core functionality of the application is transforming raw audio into structured, diarized clinical text. This process occurs asynchronously in the background.

## Pipeline Steps

### 1. Pre-processing
**File**: `server/main.py:process_file_background`

Incoming files (webm, mp3, m4a, etc.) are standardized using `ffmpeg`.
*   **Format**: WAV
*   **Sample Rate**: 16,000 Hz (Optimal for Whisper)
*   **Channels**: Mono (1)
*   **Codec**: `pcm_s16le`

```python
subprocess.run(["ffmpeg", "-i", file_path, "-ar", "16000", "-ac", "1", ...])
```

### 2. Transcription (ASR)
**Library**: `faster-whisper`
**Model**: `large-v3`
**Compute**: CPU (Int8) or GPU (if available)

We use `faster-whisper` (a CTranslate2 implementation of OpenAI's Whisper) for up to 4x speed and memory efficiency.
*   **Input**: The 16k WAV file.
*   **Output**: A list of segments containing text, start time, end time, and log-probability.

### 3. Speaker Diarization
**Library**: `pyannote.audio`
**Model**: `pyannote/speaker-diarization-3.1`
**Requirements**: HuggingFace Token (`HF_TOKEN`)

This step identifies individual speakers in the audio stream.
*   **Input**: The same 16k WAV file.
*   **Output**: A timeline of "Turns" (Start, End, Speaker Label).

*> Note: If the `HF_TOKEN` is missing or invalid, this step is skipped, and all text is attributed to "Unknown".*

### 4. Alignment & Merging
**File**: `server/services.py:transcribe_audio`

The system must merge the **Text Segments** (from Whisper) with the **Speaker Turns** (from Pyannote).

**Algorithm**:
1.  Iterate through each Whisper text segment.
2.  Compare its time range (Start -> End) with all Diarization turns.
3.  Calculate the **Time Overlap** between the text segment and the speaker turn.
4.  Assign the speaker with the maximum overlap to that segment.

### 5. Metadata Calculation
*   **Duration**: Derived from the last segment's timestamp.
*   **Word Count**: Sum of words in the final text.
*   **Confidence**: Derived from the average `avg_logprob` of the Whisper segments (converted to probability).
*   **Speaker Count**: Unique number of speaker labels found.
