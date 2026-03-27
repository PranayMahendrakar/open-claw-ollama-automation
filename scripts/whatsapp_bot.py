#!/usr/bin/env python3
"""
whatsapp_bot.py - WhatsApp automation bot powered by OpenClaw + Ollama
Uses whatsapp-web.js via Node.js child process.
"""

import json
import os
import subprocess
import sys
import requests

OLLAMA_HOST    = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
MODEL_NAME     = os.getenv('OLLAMA_MODEL', 'deepseek-r1:1.5b')
NODE_BOT_FILE  = os.path.join(os.path.dirname(__file__), 'wa_client.js')


def ask_ollama(prompt: str) -> str:
    payload = {'model': MODEL_NAME, 'prompt': prompt, 'stream': False}
    try:
        r = requests.post(f'{OLLAMA_HOST}/api/generate', json=payload, timeout=60)
        r.raise_for_status()
        return r.json().get('response', '').strip()
    except Exception as e:
        return f'[ERROR] Ollama unavailable: {e}'


WA_CLIENT_JS = '''
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios  = require('axios');

const OLLAMA_HOST  = process.env.OLLAMA_HOST  || 'http://localhost:11434';
const OLLAMA_MODEL = process.env.OLLAMA_MODEL || 'deepseek-r1:1.5b';

const client = new Client({
  authStrategy: new LocalAuth({ dataPath: '.wwebjs_auth' }),
  puppeteer: { args: ['--no-sandbox', '--disable-setuid-sandbox'] }
});

client.on('qr', qr => {
  console.log('[QR] Scan this code with WhatsApp:');
  qrcode.generate(qr, { small: true });
});

client.on('ready', () => console.log('[INFO] WhatsApp client is ready!'));

client.on('message', async msg => {
  if (!msg.body.startsWith('!ai ')) return;
  const prompt = msg.body.slice(4).trim();
  try {
    const res = await axios.post(OLLAMA_HOST + '/api/generate', {
      model: OLLAMA_MODEL, prompt, stream: false
    }, { timeout: 60000 });
    const reply = res.data.response || 'No response from model.';
    await msg.reply(reply);
  } catch (err) {
    await msg.reply('Sorry, the AI is unavailable right now.');
  }
});

client.initialize();
'''


def write_node_client():
    with open(NODE_BOT_FILE, 'w') as f:
        f.write(WA_CLIENT_JS)
    print(f'[INFO] Node.js client written to {NODE_BOT_FILE}')


def install_node_deps():
    packages = ['whatsapp-web.js', 'qrcode-terminal', 'axios']
    subprocess.run(['npm', 'install'] + packages, check=True)
    print('[INFO] Node packages installed.')


def start_whatsapp_bot():
    proc = subprocess.Popen(
        ['node', NODE_BOT_FILE],
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=os.environ.copy()
    )
    return proc


def main():
    print('=' * 60)
    print('  WhatsApp Bot | OpenClaw + Ollama')
    print(f'  Ollama  : {OLLAMA_HOST}')
    print(f'  Model   : {MODEL_NAME}')
    print('=' * 60)
    test_reply = ask_ollama("Say 'OK' if you are working.")
    print(f'[OLLAMA TEST] {test_reply}')
    write_node_client()
    try:
        install_node_deps()
    except Exception as e:
        print(f'[WARN] npm install failed: {e}')
    proc = start_whatsapp_bot()
    try:
        print('[INFO] Bot running. Press Ctrl+C to stop.')
        proc.wait()
    except KeyboardInterrupt:
        print('\n[INFO] Stopping bot...')
        proc.terminate()


if __name__ == '__main__':
    main()
