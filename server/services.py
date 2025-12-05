import os
import json
import torch
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
import ollama
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

# Initialize Models
# Run on GPU (MPS) if available, else CPU. Faster-Whisper supports 'auto' or 'cpu'.
# On Mac M-series, 'cpu' with 'int8' is very fast, or 'cuda' is not available.
# faster-whisper uses CTranslate2 which supports CoreML or CPU.
# For M4 Pro, 'cpu' with 'float16' or 'int8' is good.
whisper_model = WhisperModel("large-v3", device="cpu", compute_type="int8")

# Pyannote Pipeline
try:
    diarization_pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=HF_TOKEN
    )
    # Move to MPS if available for PyTorch
    if torch.backends.mps.is_available():
        diarization_pipeline.to(torch.device("mps"))
except Exception as e:
    print(f"Warning: Could not load Pyannote pipeline. Diarization will be disabled. Error: {e}")
    diarization_pipeline = None

async def transcribe_audio(file_path: str):
    try:
        # 1. Transcribe with Faster-Whisper
        segments, info = whisper_model.transcribe(file_path, beam_size=5)
        
        transcript_segments = []
        full_text = ""
        for segment in segments:
            transcript_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
            full_text += segment.text + " "

        # 2. Diarize with Pyannote (if available)
        diarization_result = []
        if diarization_pipeline:
            # Pyannote expects a file path
            diarization = diarization_pipeline(file_path)
            
            # Match diarization with transcript segments (simple alignment)
            # This is a naive alignment. For production, use better alignment or WhisperX.
            # Here we just list speakers and their time ranges.
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                diarization_result.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })
        
        # Merge Transcript and Diarization
        # Naive merge: Assign speaker to segment if overlaps significantly
        final_transcript = []
        for segment in transcript_segments:
            assigned_speaker = "Unknown"
            max_overlap = 0
            
            seg_start = segment['start']
            seg_end = segment['end']
            
            for dia in diarization_result:
                # Calculate overlap
                overlap_start = max(seg_start, dia['start'])
                overlap_end = min(seg_end, dia['end'])
                overlap = max(0, overlap_end - overlap_start)
                
                if overlap > max_overlap:
                    max_overlap = overlap
                    assigned_speaker = dia['speaker']
            
            final_transcript.append({
                "speaker": assigned_speaker,
                "text": segment['text'],
                "start": seg_start,
                "end": seg_end
            })

        return json.dumps(final_transcript, indent=2)

    except Exception as e:
        print(f"Transcription Error: {e}")
        raise e

def process_transcript_with_ai(transcript_json: str):
    try:
        data = json.loads(transcript_json)
        full_text = ""
        for item in data:
            full_text += f"Speaker {item['speaker']}: {item['text']}\n"

        # 1. Redaction with Ollama
        redaction_prompt = f"""
        You are a medical scribe. Redact all PII (names, dates, locations, phone numbers, etc.) from the following transcript. 
        Replace redacted information with [REDACTED]. Keep the speaker labels and the rest of the text exactly as is.
        
        Transcript:
        {full_text}
        """
        
        redaction_response = ollama.chat(model='llama3', messages=[
            {'role': 'user', 'content': redaction_prompt},
        ])
        redacted_transcript = redaction_response['message']['content']

        # 2. SOAP Note with Ollama
        soap_prompt = f"""
        You are a medical scribe. Create a professional SOAP note (Subjective, Objective, Assessment, Plan) based on the following transcript.
        Use professional medical terminology.
        
        Transcript:
        {full_text}
        """

        soap_response = ollama.chat(model='llama3', messages=[
            {'role': 'user', 'content': soap_prompt},
        ])
        soap_summary = soap_response['message']['content']

        return redacted_transcript, soap_summary

    except Exception as e:
        print(f"Ollama Error: {e}")
        # Fallback if Ollama fails (e.g. model not pulled)
        return "Error processing with Ollama. Ensure 'llama3' is pulled.", "Error processing with Ollama."
