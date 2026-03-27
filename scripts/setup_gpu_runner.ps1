# ================================================================
# setup_gpu_runner.ps1 — One-click GPU Runner Setup
# Repo: PranayMahendrakar/open-claw-ollama-automation
# Run in PowerShell as Administrator on your GPU Windows machine
# ================================================================

Write-Host '===============================================' -ForegroundColor Cyan
Write-Host '  OpenClaw GPU Runner Setup' -ForegroundColor Cyan
Write-Host '===============================================' -ForegroundColor Cyan

$RUNNER_DIR    = 'C:\actions-runner'
$RUNNER_ZIP    = 'actions-runner-win-x64-2.333.0.zip'
$RUNNER_URL    = 'https://github.com/actions/runner/releases/download/v2.333.0/' + $RUNNER_ZIP
$REPO_URL      = 'https://github.com/PranayMahendrakar/open-claw-ollama-automation'
$RUNNER_NAME   = 'pranay-gpu-runner'
$RUNNER_LABELS = 'self-hosted,gpu,windows,x64'

# TOKEN: Generate fresh at:
# https://github.com/PranayMahendrakar/open-claw-ollama-automation/settings/actions/runners/new
# (expires 1 hour — if expired, get a new one from the link above)
$REG_TOKEN = 'AVTFVDATAUL7MLPNPZXHN63JYZQOS'

# 1. Create folder
Write-Host '[1/5] Creating C:\actions-runner...' -ForegroundColor Yellow
if (!(Test-Path $RUNNER_DIR)) { New-Item -ItemType Directory -Path $RUNNER_DIR | Out-Null }
Set-Location $RUNNER_DIR
Write-Host '    Done.' -ForegroundColor Green

# 2. Download
Write-Host '[2/5] Downloading runner package...' -ForegroundColor Yellow
if (!(Test-Path $RUNNER_ZIP)) {
    Invoke-WebRequest -Uri $RUNNER_URL -OutFile $RUNNER_ZIP
}
Write-Host '    Done.' -ForegroundColor Green

# 3. Extract
Write-Host '[3/5] Extracting...' -ForegroundColor Yellow
if (!(Test-Path 'config.cmd')) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory("$RUNNER_DIR\$RUNNER_ZIP", $RUNNER_DIR)
}
Write-Host '    Done.' -ForegroundColor Green

# 4. Configure (unattended)
Write-Host '[4/5] Configuring runner...' -ForegroundColor Yellow
.\config.cmd --url $REPO_URL --token $REG_TOKEN --name $RUNNER_NAME --labels $RUNNER_LABELS --runnergroup Default --work _work --unattended
Write-Host '    Done.' -ForegroundColor Green

# 5. Install as Windows service + start
Write-Host '[5/5] Installing as Windows service...' -ForegroundColor Yellow
.\svc.cmd install
.\svc.cmd start
Write-Host '    Service started.' -ForegroundColor Green

# Check GPU
Write-Host ''
Write-Host 'Checking NVIDIA GPU...' -ForegroundColor Yellow
try { nvidia-smi --query-gpu=name,memory.total --format=csv,noheader } catch { Write-Host 'nvidia-smi not found - install NVIDIA drivers' -ForegroundColor Red }

Write-Host ''
Write-Host '===============================================' -ForegroundColor Cyan
Write-Host ' SUCCESS! Runner registered and running.' -ForegroundColor Green
Write-Host ' GitHub Actions GPU job will start now!' -ForegroundColor Green
Write-Host '===============================================' -ForegroundColor Cyan
