@echo off
rem One proxy research cycle (b3/proxy_pipeline.py), run by the Windows task "TradeInitial-ProxyCycle".
rem The pipeline enforces the limits itself (3 new rules per ISO week, stop after 15 rules without a
rem validation pass, project stop on 2026-12-14), refuses to start a second copy, and pauses itself after
rem two cycle errors in a row. Pause by hand: create ops\state\STOP_PROXY_CYCLES.
cd /d D:\Trade-Initial
set "PATH=%APPDATA%\npm;C:\Python314;%PATH%"
echo ==== %DATE% %TIME% >> ops\state\proxy-cycle.log
C:\Python314\python.exe -m b3.proxy_pipeline cycle --max 1 >> ops\state\proxy-cycle.log 2>&1
