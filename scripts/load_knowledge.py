#!/usr/bin/env python3
# load_knowledge.py — loads memory/knowledge.md as system prompt for Ollama
import os, sys, json, requests, argparse
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
MODEL_NAME  = os.getenv('OLLAMA_MODEL', 'deepseek-r1:1.5b')
REPO_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_FILE = os.path.join(REPO_ROOT, 'memory', 'knowledge.md')

def load_knowledge():
    if not os.path.exists(KNOWLEDGE_FILE):
        print(f'[WARN] Not found: {KNOWLEDGE_FILE}')
        return ''
    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f'[INFO] Loaded {len(content)} chars from knowledge.md')
    return content

def chat(user_msg, system, device='cpu'):
    payload = {
        'model': MODEL_NAME, 'prompt': user_msg, 'system': system,
        'stream': False, 'options': {'num_gpu': 1 if device=='gpu' else 0,
        'temperature': 0.7}
    }
    r = requests.post(f'{OLLAMA_HOST}/api/generate', json=payload, timeout=120)
    r.raise_for_status()
    return r.json().get('response','').strip()

def run_identity_test(system, device):
    questions = [
        'Who are you?',
        'Who created you?',
        'Are you ChatGPT?',
        'What does Pranay do?'
    ]
    print('\n' + '='*60)
    print('  Identity & Memory Test')
    print('='*60)
    for q in questions:
        print(f'\nQ: {q}')
        ans = chat(q, system, device)
        print(f'A: {ans[:400]}')
    print('='*60)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--device', choices=['cpu','gpu'], default='cpu')
    p.add_argument('--test', action='store_true')
    p.add_argument('--prompt', type=str, default=None)
    args = p.parse_args()
    print(f'[INFO] Device={args.device} Model={MODEL_NAME} Host={OLLAMA_HOST}')
    system = load_knowledge()
    if not system:
        sys.exit(1)
    if args.prompt:
        print(f'\n[RESPONSE]\n{chat(args.prompt, system, args.device)}')
    else:
        run_identity_test(system, args.device)
    with open('knowledge_config.json','w') as f:
        json.dump({'system_prompt': system,'model': MODEL_NAME,'device': args.device}, f, indent=2)
    print('[INFO] Saved knowledge_config.json')

if __name__ == '__main__':
    main()
