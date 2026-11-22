@echo off
rem One agent research cycle (b3/proxy_pipeline.py) on the ACTIVE lane: WIN/WDO since 2026-11-16
rem (b3/config/b3_program.json), run every hour (owner 2026-11-16: 'maximo possivel') by the Windows task "TradeInitial-ProxyCycle" (until 2026-12-16).
rem The pipeline enforces the limits itself (168 new rules per ISO week, i.e. the hourly cadence, stop after 15 rules without a
rem validation pass, program stop 30 days after the start), refuses to start a second copy, and pauses itself after
rem two cycle errors in a row. Pause by hand: create ops\state\STOP_PROXY_CYCLES.
call "%~dp0_env.cmd"
cd /d "%ROOT%"
set "PATH=%APPDATA%\npm;%PATH%"
if exist "C:\Python314" set "PATH=C:\Python314;%PATH%"
if not exist ops\state mkdir ops\state
echo ==== %DATE% %TIME% >> ops\state\proxy-cycle.log
"%PY%" -m b3.proxy_pipeline cycle --max 1 >> ops\state\proxy-cycle.log 2>&1
