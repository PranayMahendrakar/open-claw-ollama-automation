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
      authStrategy: new LocalAuth({{ dataPath: '.wwebjs_auth' }}),
        puppeteer: {{ args: ['--no-sandbox', '--disable-setuid-sandbox'] }}
        }});

        client.on('qr', qr => {{
          console.log('[QR] Scan this code with WhatsApp:');
            qrcode.generate(qr, {{ small: true }});
            }});

            client.on('ready', () => {{
              console.log('[INFO] WhatsApp client is ready!');
                if (BOT_TIMEOUT > 0) {{
                    console.log(`[INFO] Bot will auto-exit in ${{BOT_TIMEOUT}}s`);
                        setTimeout(() => {{
                              console.log('[INFO] Timeout reached — exiting cleanly.');
                                    process.exit(0);
                                        }}, BOT_TIMEOUT * 1000);
                                          }}
                                          }});

                                          client.on('message', async msg => {{
                                            // Skip group messages, status broadcasts, and messages from self
                                              if (msg.from === 'status@broadcast') return;
                                                if (msg.fromMe) return;

                                                  const userText = msg.body.trim();
                                                    if (!userText) return;

                                                      console.log(`[MSG] From: ${{msg.from}} — ${{userText.substring(0, 80)}}`);

                                                        try {{
                                                            const res = await axios.post(OLLAMA_HOST + '/api/generate', {{
                                                                  model: OLLAMA_MODEL,
                                                                        prompt: userText,
                                                                              system: SYSTEM_PROMPT,
                                                                                    stream: false,
                                                                                          options: {{ temperature: 0.7 }}
                                                                                              }}, {{ timeout: 90000 }});

                                                                                                  let reply = (res.data.response || 'No response from model.').trim();
                                                                                                      // Strip <think> blocks
                                                                                                          reply = reply.replace(/<think>[\\s\\S]*?<\\/think>/g, '').trim();
                                                                                                              if (!reply) reply = 'Hmm, let me think about that more!';
                                                                                                              
                                                                                                                  await msg.reply(reply);
                                                                                                                      console.log(`[REPLY] ${{reply.substring(0, 80)}}`);
                                                                                                                        }} catch (err) {{
                                                                                                                            console.error('[ERROR]', err.message);
                                                                                                                                await msg.reply('Sorry, the AI is unavailable right now. Please try again!');
                                                                                                                                  }}
                                                                                                                                  }});
                                                                                                                                  
                                                                                                                                  client.initialize();
                                                                                                                                  '''


def write_node_client(system_prompt: str):
        js_content = build_wa_client_js(system_prompt)
    NODE_BOT_FILE.write_text(js_content, encoding='utf-8')
    print(f'[INFO] Node.js client written to {NODE_BOT_FILE}')


def install_node_deps():
        packages = ['whatsapp-web.js', 'qrcode-terminal', 'axios']
    subprocess.run(['npm', 'install'] + packages, check=True)
    print('[INFO] Node packages installed.')


def start_whatsapp_bot() -> subprocess.Popen:
        env = os.environ.copy()
    env['OLLAMA_HOST']  = OLLAMA_HOST
    env['OLLAMA_MODEL'] = MODEL_NAME
    env['BOT_TIMEOUT']  = str(BOT_TIMEOUT)
    proc = subprocess.Popen(
                ['node', str(NODE_BOT_FILE)],
                stdout=sys.stdout,
                stderr=sys.stderr,
                env=env
    )
    return proc


def main():
        print('=' * 60)
    print(' WhatsApp Bot | OpenClaw + Ollama')
    print(f' Ollama  : {OLLAMA_HOST}')
    print(f' Model   : {MODEL_NAME}')
    print(f' Timeout : {BOT_TIMEOUT}s (0 = no timeout)')
    print('=' * 60)

    system = load_knowledge()

    # Quick Ollama health check
    try:
                r = requests.get(f'{OLLAMA_HOST}/api/tags', timeout=10)
                models = [m['name'] for m in r.json().get('models', [])]
                print(f'[OLLAMA] Available models: {models}')
except Exception as e:
        print(f'[WARN] Ollama health check failed: {e}')

    write_node_client(system)

    try:
                install_node_deps()
except Exception as e:
        print(f'[WARN] npm install had issues: {e}')

    proc = start_whatsapp_bot()
    try:
                print('[INFO] Bot running. Ctrl+C to stop.')
                proc.wait()
except KeyboardInterrupt:
        print('\n[INFO] Stopping bot...')
        proc.terminate()


if __name__ == '__main__':
        main()
