$ErrorActionPreference = 'Stop'

Set-Location $PSScriptRoot

function Sync-File {
  param(
    [string]$Source,
    [string]$Destination
  )

  if (Test-Path $Source) {
    New-Item -ItemType Directory -Force (Split-Path $Destination) | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
  }
}

function Sync-Directory {
  param(
    [string]$Source,
    [string]$Destination
  )

  if (Test-Path $Source) {
    New-Item -ItemType Directory -Force $Destination | Out-Null
    Copy-Item -Path (Join-Path $Source '*') -Destination $Destination -Recurse -Force
  }
}

$profileMode = 'shared'
$bareMode = $false
$forwardArgs = [System.Collections.Generic.List[string]]::new()
foreach ($arg in $args) {
  switch ($arg) {
    '--shared-profile' { $profileMode = 'shared' }
    '--isolated-profile' { $profileMode = 'isolated' }
    '--bare-mode' { $bareMode = $true }
    default { $forwardArgs.Add($arg) }
  }
}

if ($profileMode -eq 'isolated') {
  $env:CLAUDE_CONFIG_DIR = Join-Path $PSScriptRoot '.recovered-claude-home'
  New-Item -ItemType Directory -Force $env:CLAUDE_CONFIG_DIR | Out-Null
  Sync-File (Join-Path $env:USERPROFILE '.claude.json') (Join-Path $env:CLAUDE_CONFIG_DIR '.claude.json')
  Sync-File (Join-Path $env:USERPROFILE '.claude\settings.json') (Join-Path $env:CLAUDE_CONFIG_DIR 'settings.json')
  Sync-Directory (Join-Path $env:USERPROFILE '.claude\projects') (Join-Path $env:CLAUDE_CONFIG_DIR 'projects')
  Sync-Directory (Join-Path $env:USERPROFILE '.claude\plugins') (Join-Path $env:CLAUDE_CONFIG_DIR 'plugins')
  Sync-Directory (Join-Path $env:USERPROFILE '.claude\cache') (Join-Path $env:CLAUDE_CONFIG_DIR 'cache')
  Sync-Directory (Join-Path $env:USERPROFILE '.claude\sessions') (Join-Path $env:CLAUDE_CONFIG_DIR 'sessions')
  Sync-File (Join-Path $env:USERPROFILE '.claude\history.jsonl') (Join-Path $env:CLAUDE_CONFIG_DIR 'history.jsonl')
} else {
  Remove-Item Env:CLAUDE_CONFIG_DIR -ErrorAction SilentlyContinue
}

$env:CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC = '1'
$env:DISABLE_AUTOUPDATER = '1'
if (-not $env:ANTHROPIC_SMALL_FAST_MODEL -and $env:ANTHROPIC_MODEL) {
  $env:ANTHROPIC_SMALL_FAST_MODEL = $env:ANTHROPIC_MODEL
}

Write-Host '[recovered-cli] Starting recovered CLI...'
Write-Host "[recovered-cli] Profile mode: $profileMode"
Write-Host '[recovered-cli] Nonessential traffic disabled.'
Write-Host '[recovered-cli] Auto-updater disabled.'
if ($env:CLAUDE_CONFIG_DIR) {
  Write-Host "[recovered-cli] Config dir: $env:CLAUDE_CONFIG_DIR"
} else {
  Write-Host '[recovered-cli] Config dir: user default profile'
}
if ($env:ANTHROPIC_SMALL_FAST_MODEL) {
  Write-Host "[recovered-cli] Small fast model: $env:ANTHROPIC_SMALL_FAST_MODEL"
}
if ($bareMode) {
  Write-Host '[recovered-cli] Bare mode enabled. OAuth and keychain auth are skipped.'
}
Write-Host ''

$cliArgs = [System.Collections.Generic.List[string]]::new()
$cliArgs.Add('.\src\entrypoints\cli.tsx')
$cliArgs.Add('--no-chrome')
if ($bareMode) {
  $cliArgs.Add('--bare')
}
$cliArgs.AddRange($forwardArgs)

& bun @cliArgs
$exitCode = $LASTEXITCODE

Write-Host ''
Write-Host "[recovered-cli] Process exited with code $exitCode."
Read-Host 'Press Enter to close'
exit $exitCode
