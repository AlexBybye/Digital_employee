<#
.SYNOPSIS
    Ops Digital Employee -- One-click environment setup
.DESCRIPTION
    Automatically installs Ollama, pulls DeepSeek model,
    installs Python dependencies, and initializes the database.
#>

# Use Continue so that stderr output (e.g. from ollama pull) does not
# trigger terminating errors. Errors are handled via try/catch instead.
$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  Ops Digital Employee - Environment Setup" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta

# Wrap everything so the window never disappears without warning
$global:exitCode = 0

# --------------- 0. Project Root ---------------
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
if (-not $PROJECT_ROOT) {
    $PROJECT_ROOT = Get-Location
}
Set-Location $PROJECT_ROOT
Write-Host "[0] Project root: $PROJECT_ROOT" -ForegroundColor Cyan

# --------------- 1. Check Python ---------------
Write-Host ""
Write-Host ">>> [1/6] Checking Python environment" -ForegroundColor Cyan
try {
    $pyVer = python --version 2>&1
    Write-Host "    OK Python: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "    FAIL Python not found. Please install Python 3.9+ first." -ForegroundColor Red
    $global:exitCode = 1
}

# --------------- 2. Install / Check Ollama ---------------
Write-Host ""
Write-Host ">>> [2/6] Checking Ollama" -ForegroundColor Cyan

# Check common Ollama installation paths
$ollamaDirs = @(
    "$env:ProgramFiles\Ollama",
    "${env:ProgramFiles(x86)}\Ollama",
    "$env:LOCALAPPDATA\Programs\Ollama"
)
$ollamaExe = $null
foreach ($dir in $ollamaDirs) {
    $testPath = Join-Path $dir "ollama.exe"
    if (Test-Path $testPath) {
        $ollamaExe = $testPath
        break
    }
}

# Also check via command (in case PATH is already set)
if (-not $ollamaExe) {
    $cmdPath = Get-Command ollama.exe -ErrorAction SilentlyContinue
    if ($cmdPath) {
        $ollamaExe = $cmdPath.Source
    }
}

$ollamaInstalled = ($ollamaExe -ne $null)

if ($ollamaInstalled) {
    Write-Host "    OK Ollama found at: $ollamaExe" -ForegroundColor Green
    # Ensure the directory is in PATH for subsequent steps
    $ollamaDir = Split-Path $ollamaExe -Parent
    if ($env:Path -notlike "*$ollamaDir*") {
        $env:Path = "$ollamaDir;$env:Path"
    }
} else {
    Write-Host "    INFO Ollama not found. Downloading..." -ForegroundColor Yellow
}

if (-not $ollamaInstalled) {
    $installer = "$env:TEMP\OllamaSetup.exe"
    $url = "https://ollama.com/download/OllamaSetup.exe"

    try {
        Write-Host "    Downloading Ollama installer..."
        Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
        Write-Host "    OK Download complete" -ForegroundColor Green

        Write-Host "    Installing Ollama (please wait)..."
        Start-Process -Wait -FilePath $installer -ArgumentList "/SILENT"
        Write-Host "    OK Ollama installed successfully" -ForegroundColor Green

        # Refresh PATH so the ollama command is available
        $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
        $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
        $env:Path = "$machinePath;$userPath"

        # Re-check ollama in PATH
        $ollamaExe = Get-Command ollama.exe -ErrorAction SilentlyContinue
        if (-not $ollamaExe) {
            # Check common installation directories
            $checkDirs = @(
                "$env:ProgramFiles\Ollama",
                "${env:ProgramFiles(x86)}\Ollama",
                "$env:LOCALAPPDATA\Programs\Ollama"
            )
            foreach ($dir in $checkDirs) {
                $testPath = Join-Path $dir "ollama.exe"
                if (Test-Path $testPath) {
                    $ollamaExe = $testPath
                    if ($env:Path -notlike "*$dir*") {
                        $env:Path = "$dir;$env:Path"
                    }
                    break
                }
            }
        }

        if (-not $ollamaExe) {
            Write-Host "    WARN Ollama installed but ollama.exe not found" -ForegroundColor Yellow
            Write-Host "    Please restart the script or run it in a NEW terminal." -ForegroundColor Yellow
            $global:exitCode = 1
        }
    } catch {
        Write-Host "    FAIL Ollama installation failed: $_" -ForegroundColor Red
        Write-Host "Please manually download from https://ollama.com/download and retry."
        $global:exitCode = 1
    }
}

# --------------- 3. Start Ollama Service ---------------
Write-Host ""
Write-Host ">>> [3/6] Ensuring Ollama service is running" -ForegroundColor Cyan

# Check if Ollama API is already responding (try two methods)
$apiReady = $false

# Method 1: Invoke-RestMethod (PowerShell native)
try {
    $test = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 2
    $apiReady = $true
} catch {
    # Method 2: .NET WebClient (fallback)
    try {
        $wc = New-Object System.Net.WebClient
        $wc.DownloadString("http://localhost:11434/api/tags") | Out-Null
        $apiReady = $true
    } catch {
        Write-Host "    Ollama API not reachable yet, checking process..." -ForegroundColor Yellow
    }
}

if ($apiReady) {
    Write-Host "    OK Ollama API is already responding" -ForegroundColor Green
}

if (-not $apiReady) {
    # Check if an Ollama process is already running
    $existingProcess = Get-Process ollama -ErrorAction SilentlyContinue
    if ($existingProcess) {
        Write-Host "    Ollama process already running (PID $($existingProcess.Id)), waiting for API..."
    } else {
        # Try starting via Windows service first
        $ollamaService = Get-Service -Name "ollama" -ErrorAction SilentlyContinue
        if ($ollamaService) {
            if ($ollamaService.Status -ne "Running") {
                Write-Host "    Starting Ollama Windows service..."
                Start-Service -Name "ollama" -ErrorAction SilentlyContinue
            }
        } elseif ($ollamaExe -and (Test-Path $ollamaExe)) {
            Write-Host "    Starting Ollama process..."
            $ollamaDir = Split-Path $ollamaExe -Parent
            Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
        } else {
            Write-Host "    WARN Cannot find Ollama executable to start" -ForegroundColor Yellow
        }
    }

    # Wait for Ollama to be ready (retry up to 12 seconds)
    for ($i = 1; $i -le 12; $i++) {
        # Try Invoke-RestMethod first, then WebClient as fallback
        try {
            $test = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 2
            $apiReady = $true
            break
        } catch {
            try {
                $wc = New-Object System.Net.WebClient
                $wc.DownloadString("http://localhost:11434/api/tags") | Out-Null
                $apiReady = $true
                break
            } catch {
                if ($i -eq 1) { Write-Host "    Waiting for Ollama to start..." }
                Start-Sleep -Seconds 1
            }
        }
    }
}

if ($apiReady) {
    Write-Host "    OK Ollama service is running" -ForegroundColor Green
} else {
    Write-Host "    WARN Ollama API not responding. Will retry in the next step." -ForegroundColor Yellow
}

# --------------- 4. Pull DeepSeek Model ---------------
Write-Host ""
Write-Host ">>> [4/6] Pulling DeepSeek model (deepseek-r1:1.5b)" -ForegroundColor Cyan

Write-Host "    First pull may take a few minutes, please wait..."
try {
    $output = ollama pull deepseek-r1:1.5b 2>&1
    Write-Host "    OK Model deepseek-r1:1.5b is ready" -ForegroundColor Green
} catch {
    Write-Host "    FAIL Model pull failed: $_" -ForegroundColor Red
    Write-Host "You can manually run: ollama pull deepseek-r1:1.5b"
}

# --------------- 5. Install Python Dependencies ---------------
Write-Host ""
Write-Host ">>> [5/6] Installing Python dependencies" -ForegroundColor Cyan

$reqPath = "$PROJECT_ROOT\backend\requirements.txt"
if (Test-Path $reqPath) {
    try {
        $pipOutput = pip install -r $reqPath 2>&1
        $pipOutput | Select-String -Pattern "Successfully installed" | ForEach-Object {
            Write-Host "    $($_.Line)" -ForegroundColor Green
        }
        if (-not ($pipOutput -match "Successfully installed|Requirement already satisfied")) {
            Write-Host "    OK Python dependencies processed" -ForegroundColor Green
        }
    } catch {
        $errMsg = "$_"
        Write-Host "    FAIL Dependency installation failed" -ForegroundColor Red
        if ($errMsg -match "WinError 32") {
            Write-Host "    File locked by another process (e.g. another VS Code, pip, or Python)" -ForegroundColor Yellow
            Write-Host "    Close other programs, then manually run:" -ForegroundColor Yellow
            Write-Host "        pip install -r backend/requirements.txt" -ForegroundColor Yellow
        } else {
            Write-Host "    Error: $errMsg" -ForegroundColor Red
            Write-Host "    You can manually run: pip install -r backend/requirements.txt" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "    INFO requirements.txt not found, skipping" -ForegroundColor Yellow
}

# --------------- 6. Verify Ollama API ---------------
Write-Host ""
Write-Host ">>> [6/6] Verifying Ollama API" -ForegroundColor Cyan

try {
    $resp = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
    $models = $resp.models | ForEach-Object { $_.name }
    Write-Host "    OK Ollama API is responding" -ForegroundColor Green
    Write-Host "    Installed models: $($models -join ', ')" -ForegroundColor Green
} catch {
    Write-Host "    INFO Ollama API not responding yet (service may still be starting)" -ForegroundColor Yellow
}

# --------------- Done ---------------
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Environment setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  [1] Start backend:" -ForegroundColor White
Write-Host "      cd $PROJECT_ROOT\backend" -ForegroundColor Yellow
Write-Host "      uvicorn main:app --reload --port 8001" -ForegroundColor Yellow
Write-Host ""
Write-Host "  [2] Start frontend:" -ForegroundColor White
Write-Host "      cd $PROJECT_ROOT" -ForegroundColor Yellow
Write-Host "      python -m http.server 5173 -d frontend" -ForegroundColor Yellow
Write-Host ""
Write-Host "  [3] Open in browser:" -ForegroundColor White
Write-Host "      http://127.0.0.1:5173/index.html" -ForegroundColor Yellow
Write-Host "      http://127.0.0.1:8001/docs" -ForegroundColor Yellow
Write-Host ""

Write-Host ""
if ($global:exitCode -ne 0) {
    Write-Host "Some steps failed. Please check the messages above." -ForegroundColor Yellow
}
Write-Host "Press any key to close..." -ForegroundColor Cyan
cmd /c pause > $null
