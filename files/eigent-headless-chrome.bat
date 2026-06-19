@echo off
rem ============================================================
rem  Eigent Headless CDP Chrome - runs at every login
rem  Purpose: keep a headless Chrome listening on port 9224 so
rem           Eigent's chatStore auto-launch (which spawns a
rem           VISIBLE Chrome) never fires.
rem           See chatStore.ts:234 and electron/main/index.ts:759
rem           (launch-cdp-browser).
rem  To disable: delete this .bat, or set EigHeadlessChrome=0
rem  in user environment variables.
rem ============================================================

rem Skip if user has explicitly disabled
if /i "%EigHeadlessChrome%"=="0" exit 0

rem Skip if Chrome is already listening on 9224
powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri 'http://127.0.0.1:9224/json/version' -UseBasicParsing -TimeoutSec 1).StatusCode | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL%==0 exit 0

rem Ensure profile dir exists
if not exist "%USERPROFILE%\.eigent\browser_profiles\headless_startup" mkdir "%USERPROFILE%\.eigent\browser_profiles\headless_startup"

rem Launch headless Chrome, detached
start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" ^
  --headless=new ^
  --remote-debugging-port=9224 ^
  --user-data-dir="%USERPROFILE%\.eigent\browser_profiles\headless_startup" ^
  --no-first-run ^
  --no-default-browser-check ^
  --disable-blink-features=AutomationControlled ^
  --hide-headless-extension-info ^
  about:blank

exit 0
