# DFMEA server startup script
# Run from project root: .\Startup\run_server.ps1

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "DFMEA Server"

function Stop-WithPause {
    param([string]$Message)
    Write-Host ""
    Write-Host $Message -ForegroundColor Red
    Read-Host "`nPress Enter to exit"
    exit 1
}

function Find-PostgresTool {
    param([string]$ToolName)

    $cmd = Get-Command $ToolName -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $roots = @()
    if ($env:ProgramFiles) { $roots += (Join-Path $env:ProgramFiles "PostgreSQL") }
    if (${env:ProgramFiles(x86)}) { $roots += (Join-Path ${env:ProgramFiles(x86)} "PostgreSQL") }

    foreach ($root in $roots) {
        if (-not (Test-Path $root)) { continue }
        $matches = Get-ChildItem -Path $root -Filter "$ToolName.exe" -Recurse -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending
        if ($matches -and $matches.Count -gt 0) { return $matches[0].FullName }
    }
    return $null
}

function Test-PythonImport {
    param(
        [string]$PythonCmd,
        [string]$ImportName
    )
    $null = & $PythonCmd -c "import $ImportName" 2>&1
    return ($LASTEXITCODE -eq 0)
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\.."
Set-Location $ProjectRoot

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  DFMEA Server Startup" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# ----------------------------------------------------------------
# 1. Python
# ----------------------------------------------------------------
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow

$pythonCmd = $null
try {
    $pyVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "python command unavailable" }
    $pythonCmd = "python"
    Write-Host "  $pyVersion" -ForegroundColor Green
} catch {
    try {
        $pyVersion = python3 --version 2>&1
        if ($LASTEXITCODE -ne 0) { throw "python3 command unavailable" }
        $pythonCmd = "python3"
        Write-Host "  $pyVersion" -ForegroundColor Green
    } catch {
        Stop-WithPause "  [ERROR] Python 3.10+ was not found. Install it from https://www.python.org/downloads/"
    }
}

$major = & $pythonCmd -c "import sys; print(sys.version_info.major)" 2>&1
$minor = & $pythonCmd -c "import sys; print(sys.version_info.minor)" 2>&1
Write-Host "  Python $major.$minor detected" -ForegroundColor Green
if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 10)) {
    Stop-WithPause "  [ERROR] Python 3.10+ is required. Current version: $major.$minor"
}

# ----------------------------------------------------------------
# 2. Python dependencies
# ----------------------------------------------------------------
Write-Host "[2/5] Checking Python dependencies..." -ForegroundColor Yellow

$deps = @(
    @{ Name = "fastapi"; Package = "fastapi" },
    @{ Name = "uvicorn"; Package = "uvicorn" },
    @{ Name = "multipart"; Package = "python-multipart" },
    @{ Name = "aiofiles"; Package = "aiofiles" },
    @{ Name = "jinja2"; Package = "Jinja2" },
    @{ Name = "openpyxl"; Package = "openpyxl" },
    @{ Name = "psycopg2"; Package = "psycopg2-binary" }
)

$missing = @()
foreach ($dep in $deps) {
    if (-not (Test-PythonImport -PythonCmd $pythonCmd -ImportName $dep.Name)) {
        $missing += $dep.Package
    }
}

if ($missing.Count -gt 0) {
    Write-Host "  Missing: $($missing -join ', ')" -ForegroundColor Magenta
    Write-Host "  Installing requirements.txt..." -ForegroundColor Yellow
    & $pythonCmd -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Stop-WithPause "  [ERROR] Dependency installation failed. Try: pip install -r requirements.txt"
    }
    Write-Host "  Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  All dependencies are available" -ForegroundColor Green
}

# ----------------------------------------------------------------
# 3. Data directory
# ----------------------------------------------------------------
Write-Host "[3/5] Checking data directory..." -ForegroundColor Yellow

$DataDir = if ($env:DFMEA_DB_DIR) { $env:DFMEA_DB_DIR } else { Join-Path $env:USERPROFILE "dfmea_db" }
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
    Write-Host "  Created: $DataDir" -ForegroundColor Green
} else {
    Write-Host "  Found: $DataDir" -ForegroundColor Green
}
Write-Host "  Upload directory: $(Join-Path $DataDir 'uploads')" -ForegroundColor Gray

# ----------------------------------------------------------------
# 4. Database
# ----------------------------------------------------------------
Write-Host "[4/5] Checking database..." -ForegroundColor Yellow

if (-not $env:DFMEA_DB_BACKEND) { $env:DFMEA_DB_BACKEND = "postgres" }

if ($env:DFMEA_DB_BACKEND -eq "postgres") {
    if (-not $env:DFMEA_POSTGRES_DB) { $env:DFMEA_POSTGRES_DB = "dfmea" }
    if (-not $env:DFMEA_POSTGRES_USER) { $env:DFMEA_POSTGRES_USER = "postgres" }
    if (-not $env:DFMEA_POSTGRES_HOST) { $env:DFMEA_POSTGRES_HOST = "localhost" }
    if (-not $env:DFMEA_POSTGRES_PORT) { $env:DFMEA_POSTGRES_PORT = "5432" }
    if (-not $env:DFMEA_POSTGRES_PASSWORD -and $env:PGPASSWORD) {
        $env:DFMEA_POSTGRES_PASSWORD = $env:PGPASSWORD
    }
    if (-not $env:DFMEA_DATABASE_URL -and -not $env:DFMEA_POSTGRES_PASSWORD) {
        $env:DFMEA_POSTGRES_PASSWORD = Read-Host "  Enter PostgreSQL password for user $($env:DFMEA_POSTGRES_USER)"
    }

    if ($env:DFMEA_POSTGRES_DB -notmatch '^[A-Za-z0-9_]+$') {
        Stop-WithPause "  [ERROR] Database name may only contain letters, numbers, and underscores. Current: $($env:DFMEA_POSTGRES_DB)"
    }

    $psql = Find-PostgresTool "psql"
    $pgReady = Find-PostgresTool "pg_isready"
    if (-not $psql) { Stop-WithPause "  [ERROR] psql.exe was not found. Install PostgreSQL or add its bin directory to PATH." }
    if (-not $pgReady) { Stop-WithPause "  [ERROR] pg_isready.exe was not found. Check your PostgreSQL installation." }

    Write-Host "  psql: $psql" -ForegroundColor Gray

    $pgServices = Get-Service | Where-Object { $_.Name -like "*postgres*" -or $_.DisplayName -like "*postgres*" }
    if ($pgServices) {
        foreach ($svc in $pgServices) {
            Write-Host "  Service: $($svc.Name) [$($svc.Status)]" -ForegroundColor Gray
            if ($svc.Status -ne "Running") {
                Write-Host "  Starting PostgreSQL service $($svc.Name)..." -ForegroundColor Yellow
                Start-Service $svc.Name
                Start-Sleep -Seconds 2
            }
        }
    } else {
        Write-Host "  No Windows PostgreSQL service found; testing host/port directly." -ForegroundColor DarkYellow
    }

    & $pgReady -h $env:DFMEA_POSTGRES_HOST -p $env:DFMEA_POSTGRES_PORT | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Stop-WithPause "  [ERROR] PostgreSQL is not accepting connections at $($env:DFMEA_POSTGRES_HOST):$($env:DFMEA_POSTGRES_PORT)."
    }

    if (-not $env:DFMEA_DATABASE_URL) {
        $oldPgPassword = $env:PGPASSWORD
        $env:PGPASSWORD = $env:DFMEA_POSTGRES_PASSWORD
        try {
            $testSql = "select current_user;"
            $null = & $psql -U $env:DFMEA_POSTGRES_USER -h $env:DFMEA_POSTGRES_HOST -p $env:DFMEA_POSTGRES_PORT -d postgres -tAc $testSql 2>&1
            if ($LASTEXITCODE -ne 0) {
                Stop-WithPause "  [ERROR] PostgreSQL password or connection settings are invalid."
            }

            $dbName = $env:DFMEA_POSTGRES_DB
            $existsSql = "select 1 from pg_database where datname = '$dbName';"
            $exists = & $psql -U $env:DFMEA_POSTGRES_USER -h $env:DFMEA_POSTGRES_HOST -p $env:DFMEA_POSTGRES_PORT -d postgres -tAc $existsSql
            if ($LASTEXITCODE -ne 0) {
                Stop-WithPause "  [ERROR] Could not check whether database exists."
            }
            if (-not ($exists -match "1")) {
                Write-Host "  Database $dbName does not exist. Creating..." -ForegroundColor Yellow
                $createSql = "create database ""$dbName"";"
                & $psql -U $env:DFMEA_POSTGRES_USER -h $env:DFMEA_POSTGRES_HOST -p $env:DFMEA_POSTGRES_PORT -d postgres -c $createSql
                if ($LASTEXITCODE -ne 0) {
                    Stop-WithPause "  [ERROR] Database creation failed. Confirm the PostgreSQL user has CREATEDB permission."
                }
            }
        } finally {
            $env:PGPASSWORD = $oldPgPassword
        }
    } else {
        Write-Host "  DFMEA_DATABASE_URL is set; skipping psql database creation step." -ForegroundColor Gray
    }

    Write-Host "  Running application database initialization..." -ForegroundColor Yellow
    & $pythonCmd -c "from db.database import init_db; init_db(); print('db init ok')"
    if ($LASTEXITCODE -ne 0) {
        Stop-WithPause "  [ERROR] Application database initialization failed. Check PostgreSQL connection, permissions, and schema."
    }

    Write-Host "  Database: PostgreSQL/$($env:DFMEA_POSTGRES_DB)" -ForegroundColor Green
} else {
    Write-Host "  Database: SQLite ($DataDir)" -ForegroundColor Green
    & $pythonCmd -c "from db.database import init_db; init_db(); print('db init ok')"
    if ($LASTEXITCODE -ne 0) {
        Stop-WithPause "  [ERROR] SQLite database initialization failed."
    }
}

# ----------------------------------------------------------------
# 5. Start server
# ----------------------------------------------------------------
Write-Host ""
Write-Host "[5/5] Starting server" -ForegroundColor Yellow
Write-Host "  LAN URL: http://0.0.0.0:10197" -ForegroundColor White
Write-Host "  Local URL: http://127.0.0.1:10197" -ForegroundColor White
Write-Host "  Initial admin account for an empty database: admin / admin123456" -ForegroundColor Gray
Write-Host "  Change the admin password immediately after first login." -ForegroundColor Gray
Write-Host "  Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""
Write-Host "  Keep this window open while using DFMEA." -ForegroundColor DarkYellow
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

try {
    & $pythonCmd -m uvicorn app:app --host 0.0.0.0 --port 10197
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
        Write-Host ""
        Write-Host "uvicorn exit code: $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host ""
    Write-Host "Server exited with error: $_" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "Server stopped." -ForegroundColor Cyan
    Read-Host "Press Enter to exit"
}
