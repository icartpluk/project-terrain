@echo off
setlocal
where py >nul 2>&1
if not errorlevel 1 (
  py -3 "%~dp0simulation\start.py" %*
) else (
  where python >nul 2>&1
  if errorlevel 1 (
    echo Python 3.11 or newer is needed. Install it from python.org and try again.
    pause
    exit /b 1
  )
  python "%~dp0simulation\start.py" %*
)
if errorlevel 1 (
  echo The demo could not start. See the message above.
  pause
  exit /b 1
)
endlocal
