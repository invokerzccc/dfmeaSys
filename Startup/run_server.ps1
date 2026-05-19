# DFMEA 记录系统 — 服务器启动脚本
# 用法: 在项目根目录下，右键此文件 -> "使用 PowerShell 运行"
#       或在终端中: .\Startup\run_server.ps1

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "DFMEA Server"

function Stop-WithPause {
    param([string]$Message)
    Write-Host ""
    Write-Host $Message -ForegroundColor Red
    Read-Host "`n按 Enter 退出"
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
Write-Host "  DFMEA 记录系统 — 服务器启动"             -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# ----------------------------------------------------------------
# 1. 检查 Python 环境
# ----------------------------------------------------------------
Write-Host "[1/5] 检查 Python 环境..." -ForegroundColor Yellow

$pythonCmd = $null
try {
    $pyVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "python 命令不可用" }
    $pythonCmd = "python"
    Write-Host "  $pyVersion" -ForegroundColor Green
} catch {
    try {
        $pyVersion = python3 --version 2>&1
        if ($LASTEXITCODE -ne 0) { throw }
        $pythonCmd = "python3"
        Write-Host "  $pyVersion" -ForegroundColor Green
    } catch {
        Stop-WithPause "  [错误] 未检测到 Python。请先安装 Python 3.10+。下载地址: https://www.python.org/downloads/"
    }
}

$major = & $pythonCmd -c "import sys; print(sys.version_info.major)" 2>&1
$minor = & $pythonCmd -c "import sys; print(sys.version_info.minor)" 2>&1
Write-Host "  Python $major.$minor 检测完成" -ForegroundColor Green
if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 10)) {
    Stop-WithPause "  [错误] 需要 Python 3.10+，当前为 $major.$minor"
}

# ----------------------------------------------------------------
# 2. 检查 & 安装依赖
# ----------------------------------------------------------------
Write-Host "[2/5] 检查 Python 依赖..." -ForegroundColor Yellow

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
    Write-Host "  [警告] 缺失: $($missing -join ', ')" -ForegroundColor Magenta
    Write-Host "  正在安装 requirements.txt..." -ForegroundColor Yellow
    & $pythonCmd -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Stop-WithPause "  [错误] 依赖安装失败。请手动执行: pip install -r requirements.txt"
    }
    Write-Host "  [完成] 依赖安装成功" -ForegroundColor Green
} else {
    Write-Host "  [检查] 所有依赖完整" -ForegroundColor Green
}

# ----------------------------------------------------------------
# 3. 数据目录
# ----------------------------------------------------------------
Write-Host "[3/5] 检查数据目录..." -ForegroundColor Yellow

$DataDir = if ($env:DFMEA_DB_DIR) { $env:DFMEA_DB_DIR } else { Join-Path $env:USERPROFILE "dfmea_db" }
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
    Write-Host "  [创建] $DataDir" -ForegroundColor Green
} else {
    Write-Host "  [检查] $DataDir" -ForegroundColor Green
}
Write-Host "  上传文件目录: $(Join-Path $DataDir 'uploads')" -ForegroundColor Gray

# ----------------------------------------------------------------
# 4. PostgreSQL 环境、连接和建库
# ----------------------------------------------------------------
Write-Host "[4/5] 检查数据库..." -ForegroundColor Yellow

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
        $env:DFMEA_POSTGRES_PASSWORD = Read-Host "  请输入 PostgreSQL 用户 $($env:DFMEA_POSTGRES_USER) 的密码"
    }

    if ($env:DFMEA_POSTGRES_DB -notmatch '^[A-Za-z0-9_]+$') {
        Stop-WithPause "  [错误] 数据库名只能包含字母、数字和下划线。当前: $($env:DFMEA_POSTGRES_DB)"
    }

    $psql = Find-PostgresTool "psql"
    $pgReady = Find-PostgresTool "pg_isready"
    if (-not $psql) { Stop-WithPause "  [错误] 未找到 psql.exe。请安装 PostgreSQL，或将 PostgreSQL bin 目录加入 PATH。" }
    if (-not $pgReady) { Stop-WithPause "  [错误] 未找到 pg_isready.exe。请确认 PostgreSQL 安装完整。" }

    Write-Host "  psql: $psql" -ForegroundColor Gray

    $pgServices = Get-Service | Where-Object { $_.Name -like "*postgres*" -or $_.DisplayName -like "*postgres*" }
    if ($pgServices) {
        foreach ($svc in $pgServices) {
            Write-Host "  服务: $($svc.Name) [$($svc.Status)]" -ForegroundColor Gray
            if ($svc.Status -ne "Running") {
                Write-Host "  正在启动 PostgreSQL 服务 $($svc.Name)..." -ForegroundColor Yellow
                Start-Service $svc.Name
                Start-Sleep -Seconds 2
            }
        }
    } else {
        Write-Host "  [提示] 未发现 Windows PostgreSQL 服务；将直接测试端口连接。" -ForegroundColor DarkYellow
    }

    & $pgReady -h $env:DFMEA_POSTGRES_HOST -p $env:DFMEA_POSTGRES_PORT | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Stop-WithPause "  [错误] PostgreSQL 未在 $($env:DFMEA_POSTGRES_HOST):$($env:DFMEA_POSTGRES_PORT) 接受连接。"
    }

    if (-not $env:DFMEA_DATABASE_URL) {
        $oldPgPassword = $env:PGPASSWORD
        $env:PGPASSWORD = $env:DFMEA_POSTGRES_PASSWORD
        try {
            $testSql = "select current_user;"
            $null = & $psql -U $env:DFMEA_POSTGRES_USER -h $env:DFMEA_POSTGRES_HOST -p $env:DFMEA_POSTGRES_PORT -d postgres -tAc $testSql 2>&1
            if ($LASTEXITCODE -ne 0) {
                Stop-WithPause "  [错误] PostgreSQL 密码或连接参数不正确，无法连接到 postgres 管理库。"
            }

            $existsSql = "select 1 from pg_database where datname = '$($env:DFMEA_POSTGRES_DB)';"
            $exists = & $psql -U $env:DFMEA_POSTGRES_USER -h $env:DFMEA_POSTGRES_HOST -p $env:DFMEA_POSTGRES_PORT -d postgres -tAc $existsSql
            if ($LASTEXITCODE -ne 0) {
                Stop-WithPause "  [错误] 无法检查数据库是否存在。"
            }
            if (-not ($exists -match "1")) {
                Write-Host "  数据库 $($env:DFMEA_POSTGRES_DB) 不存在，正在创建..." -ForegroundColor Yellow
                $createSql = "create database ""$($env:DFMEA_POSTGRES_DB)"";"
                & $psql -U $env:DFMEA_POSTGRES_USER -h $env:DFMEA_POSTGRES_HOST -p $env:DFMEA_POSTGRES_PORT -d postgres -c $createSql
                if ($LASTEXITCODE -ne 0) {
                    Stop-WithPause "  [错误] 创建数据库失败。请确认当前 PostgreSQL 用户有 CREATEDB 权限。"
                }
            }
        } finally {
            $env:PGPASSWORD = $oldPgPassword
        }
    } else {
        Write-Host "  使用 DFMEA_DATABASE_URL，跳过 psql 自动建库步骤。" -ForegroundColor Gray
    }

    Write-Host "  正在执行应用数据库初始化测试..." -ForegroundColor Yellow
    & $pythonCmd -c "from db.database import init_db; init_db(); print('db init ok')"
    if ($LASTEXITCODE -ne 0) {
        Stop-WithPause "  [错误] 应用数据库初始化失败。请检查 PostgreSQL 连接、权限和表结构。"
    }

    Write-Host "  数据库: PostgreSQL/$($env:DFMEA_POSTGRES_DB)" -ForegroundColor Green
} else {
    Write-Host "  数据库: SQLite ($DataDir)" -ForegroundColor Green
    & $pythonCmd -c "from db.database import init_db; init_db(); print('db init ok')"
    if ($LASTEXITCODE -ne 0) {
        Stop-WithPause "  [错误] SQLite 数据库初始化失败。"
    }
}

# ----------------------------------------------------------------
# 5. 启动
# ----------------------------------------------------------------
Write-Host ""
Write-Host "[5/5] 启动服务" -ForegroundColor Yellow
Write-Host "  地址: http://0.0.0.0:10197" -ForegroundColor White
Write-Host "  本机访问: http://127.0.0.1:10197" -ForegroundColor White
Write-Host "  初始管理员: admin / admin123456（仅首次初始化空数据库时创建）" -ForegroundColor Gray
Write-Host "  首次登录后请立即在账号管理中修改管理员密码。" -ForegroundColor Gray
Write-Host "  按 Ctrl+C 停止服务" -ForegroundColor Gray
Write-Host ""
Write-Host "  *** 请勿关闭此窗口 ***" -ForegroundColor DarkYellow
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

try {
    & $pythonCmd -m uvicorn app:app --host 0.0.0.0 --port 10197
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
        Write-Host ""
        Write-Host "uvicorn 退出码: $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host ""
    Write-Host "服务器异常退出: $_" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "服务器已停止。" -ForegroundColor Cyan
    Read-Host "按 Enter 退出"
}
