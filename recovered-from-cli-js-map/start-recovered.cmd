@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

set "PROFILE_MODE=shared"
set "BARE_MODE=0"
set "FORWARD_ARGS="

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--shared-profile" (
  set "PROFILE_MODE=shared"
) else if /I "%~1"=="--isolated-profile" (
  set "PROFILE_MODE=isolated"
) else if /I "%~1"=="--bare-mode" (
  set "BARE_MODE=1"
) else (
  set FORWARD_ARGS=!FORWARD_ARGS! "%~1"
)
shift
goto parse_args

:args_done

if /I "%PROFILE_MODE%"=="isolated" (
  set "CLAUDE_CONFIG_DIR=%~dp0.recovered-claude-home"
  if not exist "%CLAUDE_CONFIG_DIR%" mkdir "%CLAUDE_CONFIG_DIR%"
  call :sync_file "%USERPROFILE%\.claude.json" "%CLAUDE_CONFIG_DIR%\.claude.json"
  call :sync_file "%USERPROFILE%\.claude\settings.json" "%CLAUDE_CONFIG_DIR%\settings.json"
  call :sync_dir "%USERPROFILE%\.claude\projects" "%CLAUDE_CONFIG_DIR%\projects"
  call :sync_dir "%USERPROFILE%\.claude\plugins" "%CLAUDE_CONFIG_DIR%\plugins"
  call :sync_dir "%USERPROFILE%\.claude\cache" "%CLAUDE_CONFIG_DIR%\cache"
  call :sync_dir "%USERPROFILE%\.claude\sessions" "%CLAUDE_CONFIG_DIR%\sessions"
  call :sync_file "%USERPROFILE%\.claude\history.jsonl" "%CLAUDE_CONFIG_DIR%\history.jsonl"
) else (
  set "CLAUDE_CONFIG_DIR="
)

set "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"
set "DISABLE_AUTOUPDATER=1"
if defined ANTHROPIC_MODEL if not defined ANTHROPIC_SMALL_FAST_MODEL set "ANTHROPIC_SMALL_FAST_MODEL=%ANTHROPIC_MODEL%"
set "CLAUDE_EXTRA_FLAGS=--no-chrome"
if "%BARE_MODE%"=="1" set "CLAUDE_EXTRA_FLAGS=%CLAUDE_EXTRA_FLAGS% --bare"

echo [recovered-cli] Starting recovered CLI...
echo [recovered-cli] Profile mode: %PROFILE_MODE%
echo [recovered-cli] Nonessential traffic disabled.
echo [recovered-cli] Auto-updater disabled.
if defined CLAUDE_CONFIG_DIR (
  echo [recovered-cli] Config dir: %CLAUDE_CONFIG_DIR%
) else (
  echo [recovered-cli] Config dir: user default profile
)
if defined ANTHROPIC_SMALL_FAST_MODEL echo [recovered-cli] Small fast model: %ANTHROPIC_SMALL_FAST_MODEL%
if "%BARE_MODE%"=="1" echo [recovered-cli] Bare mode enabled. OAuth and keychain auth are skipped.
echo.

bun .\src\entrypoints\cli.tsx %CLAUDE_EXTRA_FLAGS% %FORWARD_ARGS%
set "EXITCODE=%ERRORLEVEL%"

echo.
echo [recovered-cli] Process exited with code %EXITCODE%.
pause
exit /b %EXITCODE%

:sync_file
if exist "%~1" copy /Y "%~1" "%~2" >nul
exit /b 0

:sync_dir
if exist "%~1" (
  if not exist "%~2" mkdir "%~2"
  robocopy "%~1" "%~2" /E /NFL /NDL /NJH /NJS /NP >nul
)
exit /b 0
