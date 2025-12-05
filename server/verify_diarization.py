import os
from dotenv import load_dotenv
from pyannote.audio import Pipeline
import torch

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

print(f"HF_TOKEN present: {bool(HF_TOKEN)}")
if HF_TOKEN:
    print(f"Token length: {len(HF_TOKEN)}")
    print(f"Token starts with: {HF_TOKEN[:4]}...")

try:
    print("Attempting to load pipeline...")
    from pyannote.audio.core.task import Specifications, Problem, Resolution
    torch.serialization.add_safe_globals([torch.torch_version.TorchVersion, Specifications, Problem, Resolution])
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=HF_TOKEN
    )
    if pipeline:
        print("Pipeline loaded successfully!")
        if torch.backends.mps.is_available():
            print("MPS is available. Moving to MPS...")
            pipeline.to(torch.device("mps"))
            print("Moved to MPS.")
        else:
            print("MPS not available. Using CPU.")
    else:
        print("Pipeline failed to load (returned None). Check your token permissions on Hugging Face.")
except Exception as e:
    print(f"Error loading pipeline: {e}")
