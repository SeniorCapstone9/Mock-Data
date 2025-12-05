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
    from pyannote.audio.core.task import Specifications, Problem, Resolution
    torch.serialization.add_safe_globals([torch.torch_version.TorchVersion, Specifications, Problem, Resolution])
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
                "text": segment.text,
                "avg_logprob": segment.avg_logprob
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

        # Calculate Metadata
        duration = transcript_segments[-1]['end'] if transcript_segments else 0.0
        word_count = len(full_text.split())
        
        # Calculate Average Confidence
        total_confidence = sum([s.avg_logprob for s in segments]) # This is logprob, need to convert or just use as score. 
        # Actually faster-whisper segment has 'avg_logprob'. Probability is exp(avg_logprob).
        # Let's approximate confidence.
        avg_confidence = 0.0
        if transcript_segments:
            import math
            avg_confidence = sum([math.exp(s['avg_logprob']) for s in transcript_segments]) / len(transcript_segments)

        speaker_count = len(set([s['speaker'] for s in final_transcript]))

        return {
            "json": json.dumps(final_transcript, indent=2),
            "duration": duration,
            "word_count": word_count,
            "confidence": avg_confidence,
            "speaker_count": speaker_count
        }

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

        # 3. Generate Title
        title_prompt = f"""
        You are a medical scribe. Generate a very short, descriptive title (3-5 words) for this session based on the transcript. 
        Examples: "Cardiology Follow-up", "Pediatric Flu Checkup", "Diabetes Management Consultation".
        Do not use quotes or prefixes. Just the title.
        
        Transcript:
        {full_text}
        """
        title_response = ollama.chat(model='llama3', messages=[
            {'role': 'user', 'content': title_prompt},
        ])
        title = title_response['message']['content'].strip().strip('"')

        # 4. Advanced Analytics (Sentiment, Tags, Action Items)
        analytics_prompt = f"""
        You are a medical AI. Analyze the following transcript and extract:
        1. Sentiment: One word (e.g., "Anxious", "Calm", "Painful", "Relieved", "Neutral").
        2. Medical Tags: A list of 3-5 key medical terms or conditions discussed.
        3. Action Items: A list of concrete tasks for the patient (e.g., "Take medication", "Follow up").
        
        Return ONLY valid JSON in this format:
        {{
            "sentiment": "String",
            "tags": ["Tag1", "Tag2"],
            "action_items": ["Action 1", "Action 2"]
        }}
        
        Transcript:
        {full_text}
        """
        analytics_response = ollama.chat(model='llama3', messages=[
            {'role': 'user', 'content': analytics_prompt},
        ], format='json')
        
        analytics_json = json.loads(analytics_response['message']['content'])
        
        return redacted_transcript, soap_summary, title, full_text, analytics_json

    except Exception as e:
        print(f"Ollama Error: {e}")
        # Fallback if Ollama fails (e.g. model not pulled)
        return "Error processing with Ollama. Ensure 'llama3' is pulled.", "Error processing with Ollama.", "Untitled Session", "", {}
