@echo off
rem Read-only tick recorder for WIN and WDO (b3/data/tick_recorder.py; owner 2026-11-16 "rode o projeto no maximo",
rem lever 2 of docs/plano-busca-padroes-b3.md). Saves every tick of the active and next contract of each root to
rem user_data\data\b3\clear\ticks\. Started on weekdays at 19:05 by the Windows task "TradeInitial-TickRecorder".
rem Needs the Clear terminal open and logged in to ClearInvestimentos-DEMO; sends no order.
cd /d D:\Trade-Initial
if not exist live\logs mkdir live\logs
echo ==== %DATE% %TIME% start >> live\logs\tick-recorder.log
live\.venv\Scripts\python.exe -m b3.data.tick_recorder >> live\logs\tick-recorder.log 2>&1
echo ==== %DATE% %TIME% exit %ERRORLEVEL% >> live\logs\tick-recorder.log
