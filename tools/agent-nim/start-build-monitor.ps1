param(
    [ValidateRange(30,3600)][int]$Interval = 45,
    [string]$Binary = '',
    [string]$RepositoryRoot = (Join-Path $PSScriptRoot '../..')
)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path -LiteralPath $RepositoryRoot).Path
if (-not $Binary) { $Binary = Join-Path $taskRoot '../nim-portable-tools/build_monitor.exe' }
$taskBinary = (Resolve-Path -LiteralPath $Binary).Path
$taskState = Join-Path $taskRoot '.codex'
New-Item -ItemType Directory -Path $taskState -Force | Out-Null
if (Test-Path -LiteralPath (Join-Path $taskState 'build-monitor.lock')) {
    throw 'Monitor lock already exists. Check its PID before starting another instance.'
}
$taskOldToken = $env:GITHUB_TOKEN
$taskOldPath = $env:PATH
$taskOldCa = $env:SSL_CERT_FILE
try {
    if (-not $env:GITHUB_TOKEN -and (Get-Command gh -ErrorAction SilentlyContinue)) {
        $taskToken = & gh auth token 2>$null
        if ($LASTEXITCODE -eq 0) { $env:GITHUB_TOKEN = $taskToken }
    }
    if (Test-Path -LiteralPath 'C:/nim/bin') { $env:PATH = 'C:/nim/bin;' + $env:PATH }
    if (-not $env:SSL_CERT_FILE -and (Test-Path -LiteralPath 'C:/Program Files/Git/mingw64/etc/ssl/cert.pem')) {
        $env:SSL_CERT_FILE = 'C:/Program Files/Git/mingw64/etc/ssl/cert.pem'
    }
    $taskArguments = @("--interval:$Interval", ('--state-dir="' + $taskState + '"'))
    $taskStart = @{
        FilePath = $taskBinary
        WorkingDirectory = $taskRoot
        WindowStyle = 'Hidden'
        PassThru = $true
        ArgumentList = $taskArguments
        RedirectStandardOutput = (Join-Path $taskState 'build-monitor.stdout.log')
        RedirectStandardError = (Join-Path $taskState 'build-monitor.stderr.log')
    }
    $taskProcess = Start-Process @taskStart
    if ($taskProcess.WaitForExit(1500)) { throw 'Monitor exited during startup; inspect .codex/build-monitor.stderr.log.' }
    Write-Output "Build monitor started: PID $($taskProcess.Id); shared state: $taskState"
} finally {
    $env:GITHUB_TOKEN = $taskOldToken
    $env:PATH = $taskOldPath
    $env:SSL_CERT_FILE = $taskOldCa
    $taskToken = $null
}
