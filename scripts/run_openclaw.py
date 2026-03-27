#!/usr/bin/env python3
"""
run_openclaw.py - OpenClaw automation via Ollama
Supports both CPU and GPU execution modes.
"""

import argparse
import json
import os
import sys
import requests
import time

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME  = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")


def check_ollama():
    """Verify Ollama is running and the model is available."""
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        print(f"[INFO] Ollama is running. Available models: {models}")
        if MODEL_NAME not in models:
            print(f"[WARN] Model '{MODEL_NAME}' not found. Pulling...")
            pull_model()
        return True
    except Exception as e:
        print(f"[ERROR] Cannot reach Ollama at {OLLAMA_HOST}: {e}")
        sys.exit(1)


def pull_model():
    """Pull the OpenClaw/deepseek model via Ollama."""
    payload = {"name": MODEL_NAME, "stream": False}
    r = requests.post(f"{OLLAMA_HOST}/api/pull", json=payload, timeout=300)
    r.raise_for_status()
    print(f"[INFO] Model '{MODEL_NAME}' pulled successfully.")


def run_inference(prompt: str, device: str = "cpu") -> str:
    """Send a prompt to Ollama and return the response."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_gpu": 1 if device == "gpu" else 0,
        },
    }
    print(f"[INFO] Running inference on {device.upper()} | Model: {MODEL_NAME}")
    r = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=120)
    r.raise_for_status()
    result = r.json()
    return result.get("response", "")


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Ollama Automation")
    parser.add_argument(
        "--device",
        choices=["cpu", "gpu"],
        default="cpu",
        help="Device to use for inference (default: cpu)",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="Hello! Introduce yourself as OpenClaw assistant powered by Ollama.",
        help="Prompt to send to the model",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  OpenClaw Ollama Automation")
    print(f"  Device : {args.device.upper()}")
    print(f"  Host   : {OLLAMA_HOST}")
    print(f"  Model  : {MODEL_NAME}")
    print("=" * 60)

    check_ollama()

    response = run_inference(args.prompt, device=args.device)
    print("\n[RESPONSE]")
    print(response)

    # Persist output for downstream jobs
    with open("openclaw_output.json", "w") as f:
        json.dump({"device": args.device, "model": MODEL_NAME, "response": response}, f, indent=2)
    print("\n[INFO] Output saved to openclaw_output.json")


if __name__ == "__main__":
    main()
