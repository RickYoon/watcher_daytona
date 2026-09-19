"""Sponsor check 2/3 — Nosana: call an Ollama endpoint running on a Nosana GPU node."""
import os, sys, requests
from dotenv import load_dotenv
load_dotenv()
URL = os.environ["NOSANA_LLM_URL"].rstrip("/")
MODEL = os.environ.get("NOSANA_MODEL", "qwen2.5:7b")

if len(sys.argv) > 1 and sys.argv[1] == "pull":
    with requests.post(f"{URL}/api/pull", json={"name": MODEL}, stream=True, timeout=1800) as r:
        for line in r.iter_lines():
            print(line.decode()[:120])
    sys.exit()

print(requests.get(f"{URL}/api/tags", timeout=30).json())
r = requests.post(f"{URL}/api/generate", json={"model": MODEL, "prompt": "Say hi in 5 words.", "stream": False}, timeout=120)
print(r.json()["response"])
