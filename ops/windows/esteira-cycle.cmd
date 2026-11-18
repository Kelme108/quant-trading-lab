@echo off
rem One conveyor cycle (b3/esteira_cycle.py): the esteira-research agent writes a batch of 5-10 rule families,
rem the checks run, the batch is committed before any read, then screened on exploration (b3/config/esteira_b3.json,
rem owner 2026-11-17 'tudo aprovado'). Started every hour by the task "TradeInitial-EsteiraCycle"; owner 2026-11-18 "sem parar": batches back to back, no new one after 50 minutes so the next hourly start takes over (the task ignores a second start while one runs).
rem The cycle enforces its own limit (agent cost per Sao Paulo day, b3/config/esteira_b3.json), refuses to start a second
rem copy and pauses itself after two errors in a row. Pause by hand: create ops\state\STOP_ESTEIRA.
cd /d D:\Trade-Initial
set "PATH=%APPDATA%\npm;C:\Python314;%PATH%"
echo ==== %DATE% %TIME% >> ops\state\esteira-cycle.log
C:\Python314\python.exe -m b3.esteira_cycle cycle --max 200 --minutes 50 >> ops\state\esteira-cycle.log 2>&1
