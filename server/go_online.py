import subprocess
import time
import json
import sys
import os
import urllib.request

def get_tunnels():
    try:
        with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels") as response:
            data = json.loads(response.read().decode())
            return data['tunnels']
    except Exception:
        return []

def start_ngrok(port):
    print(f"Starting ngrok for port {port}...")
    # Run ngrok in background
    # We use nohup or similar to keep it running? 
    # Actually just Popen is fine if we keep this script alive, but the user wants to "run a script" then have it work.
    # If this script exits, Popen might kill children unless we detach.
    # But for a "helper tool", staying open is fine.
    try:
        process = subprocess.Popen(['ngrok', 'http', str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return process
    except FileNotFoundError:
        print("Error: 'ngrok' command not found. Please install ngrok first.")
        sys.exit(1)

def main():
    print("--- Medical Scribe Remote Access Tool ---")
    print("Initializing tunnels...")

    # specialized logic: kill existing ngrok might be too aggressive? 
    # Let's just try to start.

    # 1. Start Backend Tunnel (8002)
    p_backend = start_ngrok(8002)
    time.sleep(3) # Give it time to connect

    tunnels = get_tunnels()
    backend_url = None
    for t in tunnels:
        if t['config']['addr'].endswith(':8002') or '8002' in t['config']['addr']:
            backend_url = t['public_url']
            break
    
    if not backend_url:
        print("Failed to start backend tunnel. Check if ngrok is authenticated or if you hit a limit.")
        p_backend.terminate()
        return

    print(f"Backend Online: {backend_url}")

    print("\n" + "="*50)
    print("INSTRUCTIONS:")
    print("1. Your ENTIRE APPLICATION is now accessible at this single link:")
    print(f"\n   {backend_url}")
    print("\n   (Login, Dashboard, and Uploads will all work seamlessly)")
    print("="*50)
    print("Press Ctrl+C to stop the tunnel.")

    try:
        p_backend.wait()
    except KeyboardInterrupt:
        print("\nStopping tunnels...")
        p_backend.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
