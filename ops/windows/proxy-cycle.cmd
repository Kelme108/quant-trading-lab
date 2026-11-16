@echo off
rem One agent research cycle (b3/proxy_pipeline.py) on the ACTIVE lane: WIN/WDO since 2026-11-16
rem (b3/config/b3_program.json), run every 3 hours by the Windows task "TradeInitial-ProxyCycle" (until 2026-12-16).
rem The pipeline enforces the limits itself (3 new rules per ISO week, stop after 15 rules without a
rem validation pass, program stop 30 days after the start), refuses to start a second copy, and pauses itself after
rem two cycle errors in a row. Pause by hand: create ops\state\STOP_PROXY_CYCLES.
cd /d D:\Trade-Initial
set "PATH=%APPDATA%\npm;C:\Python314;%PATH%"
echo ==== %DATE% %TIME% >> ops\state\proxy-cycle.log
C:\Python314\python.exe -m b3.proxy_pipeline cycle --max 1 >> ops\state\proxy-cycle.log 2>&1
