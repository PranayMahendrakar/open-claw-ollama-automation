# start_bot_windows.ps1
# ONE-CLICK script to start Pranay's WhatsApp AI bot on Windows PC
# Run this in PowerShell from the repo folder: .\scripts\start_bot_windows.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Pranay's WhatsApp AI Bot - Windows Startup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# --- Step 1: Check Ollama is installed ---
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Ollama not found. Install from https://ollama.com" -ForegroundColor Red
        exit 1
        }
        Write-Host "[OK] Ollama found." -ForegroundColor Green

        # --- Step 2: Start Ollama if not already running ---
        $ollamaRunning = $false
        try {
            $resp = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 3
                $ollamaRunning = $true
                    Write-Host "[OK] Ollama already running." -ForegroundColor Green
                    } catch {
                        Write-Host "[INFO] Starting Ollama..." -ForegroundColor Yellow
                            Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
                                Start-Sleep -Seconds 5
                                    Write-Host "[OK] Ollama started." -ForegroundColor Green
                                    }

                                    # --- Step 3: Pull model if needed ---
                                    Write-Host "[INFO] Checking model deepseek-r1:1.5b..." -ForegroundColor Yellow
                                    try {
                                        $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags"
                                            $modelNames = $tags.models | ForEach-Object { $_.name }
                                                if ($modelNames -notcontains "deepseek-r1:1.5b") {
                                                        Write-Host "[INFO] Pulling deepseek-r1:1.5b (first time only, ~1GB)..." -ForegroundColor Yellow
                                                                ollama pull deepseek-r1:1.5b
                                                                    } else {
                                                                            Write-Host "[OK] Model deepseek-r1:1.5b ready." -ForegroundColor Green
                                                                                }
                                                                                } catch {
                                                                                    Write-Host "[WARN] Could not check models: $_" -ForegroundColor Yellow
                                                                                    }

                                                                                    # --- Step 4: Check Python ---
                                                                                    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
                                                                                        Write-Host "[ERROR] Python not found. Install from https://python.org" -ForegroundColor Red
                                                                                            exit 1
                                                                                            }
                                                                                            Write-Host "[OK] Python found." -ForegroundColor Green

                                                                                            # --- Step 5: Install Python deps ---
                                                                                            Write-Host "[INFO] Installing Python dependencies..." -ForegroundColor Yellow
                                                                                            pip install requests pathlib --quiet

                                                                                            # --- Step 6: Check Node.js ---
                                                                                            if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
                                                                                                Write-Host "[ERROR] Node.js not found. Install from https://nodejs.org" -ForegroundColor Red
                                                                                                    exit 1
                                                                                                    }
                                                                                                    Write-Host "[OK] Node.js found." -ForegroundColor Green
                                                                                                    
                                                                                                    # --- Step 7: Check knowledge file ---
                                                                                                    $knowledgePath = Join-Path $PSScriptRoot "..\memory\knowledge.md"
                                                                                                    if (Test-Path $knowledgePath) {
                                                                                                        $size = (Get-Item $knowledgePath).Length
                                                                                                            Write-Host "[OK] knowledge.md found ($size bytes)." -ForegroundColor Green
                                                                                                            } else {
                                                                                                                Write-Host "[WARN] knowledge.md not found at $knowledgePath" -ForegroundColor Yellow
                                                                                                                }
                                                                                                                
                                                                                                                # --- Step 8: Launch the bot ---
                                                                                                                Write-Host "" 
                                                                                                                Write-Host "============================================================" -ForegroundColor Cyan
                                                                                                                Write-Host "  Starting WhatsApp bot... " -ForegroundColor Cyan
                                                                                                                Write-Host "  - Replies to ALL incoming WhatsApp messages" -ForegroundColor Cyan
                                                                                                                Write-Host "  - Powered by Pranay knowledge base + deepseek-r1" -ForegroundColor Cyan
                                                                                                                Write-Host "  - Press Ctrl+C to stop" -ForegroundColor Cyan
                                                                                                                Write-Host "============================================================" -ForegroundColor Cyan
                                                                                                                Write-Host ""
                                                                                                                
                                                                                                                $env:OLLAMA_HOST  = "http://localhost:11434"
                                                                                                                $env:OLLAMA_MODEL = "deepseek-r1:1.5b"
                                                                                                                $env:BOT_TIMEOUT  = "0"   # 0 = run forever on PC
                                                                                                                
                                                                                                                $botScript = Join-Path $PSScriptRoot "whatsapp_bot.py"
                                                                                                                python $botScript
