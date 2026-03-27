#!/usr/bin/env python3
"""
whatsapp_bot.py - WhatsApp bot powered by OpenClaw + Ollama.
Replies to ALL messages. Loads knowledge.md as system prompt.
Auto-exits after BOT_TIMEOUT seconds.
"""

import os
import subprocess
import sys
import requests
import pathlib
import re

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
BOT_TIMEOUT = int(os.getenv("BOT_TIMEOUT", "300"))
REPO_ROOT = pathlib.Path(__file__).parent.parent
KNOWLEDGE_FILE = REPO_ROOT / "memory" / "knowledge.md"
NODE_BOT_FILE = pathlib.Path(__file__).parent / "wa_client.js"


def load_knowledge() -> str:
    if KNOWLEDGE_FILE.exists():
        content = KNOWLEDGE_FILE.read_text(encoding="utf-8")
        print(f"[INFO] Loaded knowledge.md ({len(content)} chars)")
        return content
    print("[WARN] knowledge.md not found - no personality context")
    return ""


def ask_ollama(prompt: str, system: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.7}
    }
    try:
        r = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=90)
        r.raise_for_status()
        reply = r.json().get("response", "").strip()
        reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL).strip()
        return reply or "I had trouble thinking of a reply. Try again!"
    except Exception as e:
        return f"Sorry, AI unavailable. ({e})"


def build_wa_client_js(system_prompt: str) -> str:
    safe = system_prompt.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    timeout_js = ""
    if BOT_TIMEOUT > 0:
        ms = BOT_TIMEOUT * 1000
        timeout_js = f"setTimeout(() => process.exit(0), {ms});"
    js = f"""
const {{ Client, LocalAuth }} = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const OLLAMA_HOST = process.env.OLLAMA_HOST || 'http://localhost:11434';
const MODEL = process.env.OLLAMA_MODEL || 'deepseek-r1:1.5b';
const SYSTEM = `{safe}`;
{timeout_js}
const client = new Client({{ authStrategy: new LocalAuth(), puppeteer: {{ args: ['--no-sandbox'] }} }});
client.on('qr', qr => {{ qrcode.generate(qr, {{ small: true }}); }});
client.on('ready', () => console.log('[BOT] Ready!'));
client.on('message', async msg => {{
  if (msg.fromMe || msg.from === 'status@broadcast') return;
  const txt = msg.body.trim(); if (!txt) return;
  try {{
    const res = await axios.post(OLLAMA_HOST + '/api/generate', {{ model: MODEL, prompt: txt, system: SYSTEM, stream: false }}, {{ timeout: 90000 }});
    let reply = (res.data.response || '').replace(/<think>[\\s\\S]*?<\/think>/g, '').trim();
    if (!reply) reply = 'Hmm, let me think about that!';
    await msg.reply(reply);
  }} catch (err) {{ await msg.reply('Sorry, AI unavailable!'); }}
}});
client.initialize();
    """
    return js


def write_node_client(system_prompt: str):
    js = build_wa_client_js(system_prompt)
    NODE_BOT_FILE.write_text(js, encoding="utf-8")
    print(f"[INFO] Written wa_client.js")


def install_node_deps():
    subprocess.run(["npm", "install", "whatsapp-web.js", "qrcode-terminal", "axios"], check=True)
    print("[INFO] Node packages installed.")


def start_bot() -> subprocess.Popen:
    env = os.environ.copy()
    env.update({"OLLAMA_HOST": OLLAMA_HOST, "OLLAMA_MODEL": MODEL_NAME, "BOT_TIMEOUT": str(BOT_TIMEOUT)})
    return subprocess.Popen(["node", str(NODE_BOT_FILE)], stdout=sys.stdout, stderr=sys.stderr, env=env)


def main():
    print("=" * 60)
    print(f"  WhatsApp Bot | {MODEL_NAME} | Timeout: {BOT_TIMEOUT}s")
    print("=" * 60)
    system = load_knowledge()
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        print(f"[OLLAMA] Models: {[m['name'] for m in r.json().get('models', [])]}")
    except Exception as e:
        print(f"[WARN] Ollama check failed: {e}")
    write_node_client(system)
    try:
        install_node_deps()
    except Exception as e:
        print(f"[WARN] npm issues: {e}")
    proc = start_bot()
    try:
        print("[INFO] Bot running. Ctrl+C to stop.")
        proc.wait()
    except KeyboardInterrupt:
        print("\n[INFO] Stopping bot...")
        proc.terminate()


if __name__ == "__main__":
    main()
