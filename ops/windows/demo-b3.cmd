@echo off
rem Demonstration on the Clear DEMO (owner 2026-11-16: "quero apenas demonstracao de como esta se portando no demo"):
rem live/run.py with live/config/<name>.json, <name> = the first argument (default demo-b3-p004-win; also demo-b3-p004-wdo).
rem NOT evidence; the research pipeline keeps validating rules on its own. Started on weekdays at 08:40 by the
rem Windows tasks "TradeInitial-DemoB3" (WIN) and "TradeInitial-DemoB3-WDO" (it ignores a second start while running); the engine idles outside the session.
rem Needs the Clear terminal open and logged in to ClearInvestimentos-DEMO. Stop: create live\STOP (it flattens and
rem sends nothing new) or end the task. The journal is live\journal.demo-b3-p004-win.sqlite, the log live\logs\.
cd /d D:\Trade-Initial
set "NAME=%~1"
if "%NAME%"=="" set "NAME=demo-b3-p004-win"
if not exist live\logs mkdir live\logs
echo ==== %DATE% %TIME% start >> live\logs\%NAME%-task.log
live\.venv\Scripts\python.exe -m live.run --config live\config\%NAME%.json >> live\logs\%NAME%-task.log 2>&1
echo ==== %DATE% %TIME% exit %ERRORLEVEL% >> live\logs\%NAME%-task.log
