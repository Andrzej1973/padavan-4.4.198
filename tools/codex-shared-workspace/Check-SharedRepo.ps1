[CmdletBinding()]
param(
    [ValidateRange(1, 7)]
    [int] $NextAccount,

    [string] $TaskNotes,

    [switch] $OpenInCodex
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path

if (-not (Test-Path (Join-Path $repoRoot '.git'))) {
    throw "Expected the shared Git repository at '$repoRoot', but .git was not found."
}

$git = Get-Command git -ErrorAction Stop
$branch = (& $git.Source -C $repoRoot branch --show-current).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Could not read the current Git branch.' }

$head = (& $git.Source -C $repoRoot rev-parse --short HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Could not read the current Git commit.' }

$statusLines = @(& $git.Source -C $repoRoot status --short --branch)
if ($LASTEXITCODE -ne 0) { throw 'Could not read Git working-tree status.' }
$changedCount = [Math]::Max(0, $statusLines.Count - 1)

Write-Output 'Shared Padavan checkout (read-only status):'
Write-Output "  Folder: $repoRoot"
Write-Output "  Branch: $branch"
Write-Output "  HEAD:   $head"
Write-Output "  Changed/untracked paths: $changedCount"
Write-Output '  Git status:'
$statusLines | ForEach-Object { Write-Output "    $_" }

if ($PSBoundParameters.ContainsKey('NextAccount')) {
    Write-Output "`nHandoff target: Codex account #$NextAccount"
}
if (-not [string]::IsNullOrWhiteSpace($TaskNotes)) {
    Write-Output "Task notes: $TaskNotes"
}

Write-Output "`nBefore editing, read AGENTS.md, PROJECT_STATUS.md, CODEX_HANDOFF.md,"
Write-Output 'docs/AGENT-BOOTSTRAP.md, docs/AGENT-HANDOFF-RULES-SOL-DEEPSEEK.md, and'
Write-Output 'the current top block of docs/EXECUTION-ROLE.md.'
Write-Output 'This helper does not change files, Git settings, remotes, authentication, or credentials.'

if ($OpenInCodex) {
    $codex = Get-Command codex -ErrorAction Stop
    Write-Output "`nOpening this existing folder in Codex Desktop: $repoRoot"
    & $codex.Source app $repoRoot
    if ($LASTEXITCODE -ne 0) { throw "Codex Desktop launcher exited with code $LASTEXITCODE." }
}
