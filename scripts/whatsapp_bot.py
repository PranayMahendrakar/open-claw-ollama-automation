#!/usr/bin/env python3
"""
whatsapp_bot.py - WhatsApp automation bot powered by OpenClaw + Ollama
- Replies to ALL incoming messages (no prefix needed)
- Loads memory/knowledge.md as system prompt (Pranay's identity)
- Auto-exits after BOT_TIMEOUT seconds (prevents GitHub Actions hang)
"""

import os
import subprocess
import sys
import requests
import pathlib

OLLAMA_HOST  = os.getenv('OLLAMA_HOST',  'http://localhost:11434')
MODEL_NAME   = os.getenv('OLLAMA_MODEL', 'deepseek-r1:1.5b')
BOT_TIMEOUT  = int(os.getenv('BOT_TIMEOUT', '300'))   # 5 min default, set 0 for no timeout
REPO_ROOT    = pathlib.Path(__file__).parent.parent
KNOWLEDGE_FILE = REPO_ROOT / 'memory' / 'knowledge.md'
NODE_BOT_FILE  = pathlib.Path(__file__).parent / 'wa_client.js'


def load_knowledge() -> str:
        if KNOWLEDGE_FILE.exists():
                    content = KNOWLEDGE_FILE.read_text(encoding='utf-8')
                    print(f'[INFO] Loaded knowledge.md ({len(content)} chars)')
                    return content
        print('[WARN] knowledge.md not found - bot will have no personality context')
        return ''


def ask_ollama(prompt: str, system: str) -> str:
        payload = {
            'model': MODEL_NAME,
            'prompt': prompt,
            'system': system,
            'stream': False,
            'options': {'temperature': 0.7}
}
    try:
                r = requests.post(f'{OLLAMA_HOST}/api/generate', json=payload, timeout=90)
                r.raise_for_status()
                reply = r.json().get('response', '').strip()
                # Strip <think>...</think> tags that deepseek-r1 sometimes adds
                import re
                reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL).strip()
                return reply or 'I had trouble thinking of a reply. Try again!'
except Exception as e:
        return f'Sorry, the AI is unavailable right now. ({e})'


def build_wa_client_js(system_prompt: str) -> str:
        # Escape backticks and backslashes for embedding in JS template literal
        safe_system = system_prompt.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
    return f'''const {{ Client, LocalAuth }} = require('whatsapp-web.js');
    const qrcode = require('qrcode-terminal');
    const axios  = require('axios');

    const OLLAMA_HOST  = process.env.OLLAMA_HOST  || 'http://localhost:11434';
    const OLLAMA_MODEL = process.env.OLLAMA_MODEL || 'deepseek-r1:1.5b';
    const BOT_TIMEOUT  = parseInt(process.env.BOT_TIMEOUT || '300', 10);
    const SYSTEM_PROMPT = `{safe_system}`;

    const client = new Client({{
