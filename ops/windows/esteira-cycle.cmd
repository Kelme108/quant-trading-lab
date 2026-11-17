@echo off
rem One conveyor cycle (b3/esteira_cycle.py): the esteira-research agent writes a batch of 5-10 rule families,
rem the checks run, the batch is committed before any read, then screened on exploration (b3/config/esteira_b3.json,
rem owner 2026-11-17 'tudo aprovado'). Run every hour by the Windows task "TradeInitial-EsteiraCycle".
rem The cycle enforces its own limits (40 families and US$15 of agent cost per UTC day), refuses to start a second
rem copy and pauses itself after two errors in a row. Pause by hand: create ops\state\STOP_ESTEIRA.
cd /d D:\Trade-Initial
set "PATH=%APPDATA%\npm;C:\Python314;%PATH%"
echo ==== %DATE% %TIME% >> ops\state\esteira-cycle.log
C:\Python314\python.exe -m b3.esteira_cycle cycle --max 1 >> ops\state\esteira-cycle.log 2>&1
