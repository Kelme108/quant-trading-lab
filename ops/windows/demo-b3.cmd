@echo off
rem Demonstration on the Clear DEMO (owner 2026-11-16: "quero apenas demonstracao de como esta se portando no demo"):
rem live/run.py with live/config/<name>.json, <name> = the first argument (default demo-b3-p004-win; also demo-b3-p004-wdo).
rem NOT evidence; the research pipeline keeps validating rules on its own. Started on weekdays at 08:40 by the
rem Windows tasks "TradeInitial-DemoB3" (WIN) and "TradeInitial-DemoB3-WDO" (it ignores a second start while running); the engine idles outside the session.
rem Needs the Clear terminal open and logged in to ClearInvestimentos-DEMO. Stop: create live\STOP (it flattens and
rem sends nothing new) or end the task. The journal is live\journal.demo-b3-p004-win.sqlite, the log live\logs\.
call "%~dp0_env.cmd"
cd /d "%ROOT%"
rem One BLAS/OpenMP thread per robot. numpy's OpenBLAS reserves ~360 MB of committed memory PER CORE at import (12 cores here)
rem while using ~13 MB of RAM; 60 robots then exhaust the Windows commit limit (2026-11-23: MemoryError at start) with the
rem RAM half empty. With one thread each robot reserves ~60 MB. The rules are single-threaded, nothing is slower.
set "OPENBLAS_NUM_THREADS=1"
set "OMP_NUM_THREADS=1"
set "MKL_NUM_THREADS=1"
set "NAME=%~1"
if "%NAME%"=="" set "NAME=demo-b3-p004-win"
if not exist live\logs mkdir live\logs
echo ==== %DATE% %TIME% start >> live\logs\%NAME%-task.log
set "LPY=%PY%"
if exist "live\.venv\Scripts\python.exe" set "LPY=live\.venv\Scripts\python.exe"
"%LPY%" -m live.run --config live\config\%NAME%.json >> live\logs\%NAME%-task.log 2>&1
echo ==== %DATE% %TIME% exit %ERRORLEVEL% >> live\logs\%NAME%-task.log
