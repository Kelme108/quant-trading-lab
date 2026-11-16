@echo off
rem Demonstration on the Clear DEMO (owner 2026-11-16: "quero apenas demonstracao de como esta se portando no demo"):
rem live/run.py with live/config/demo-b3-p004-win.json (P-004 on WINZ26, 1 contract, stop on the server).
rem NOT evidence; the research pipeline keeps validating rules on its own. Started on weekdays at 08:40 by the
rem Windows task "TradeInitial-DemoB3" (it ignores a second start while running); the engine idles outside the session.
rem Needs the Clear terminal open and logged in to ClearInvestimentos-DEMO. Stop: create live\STOP (it flattens and
rem sends nothing new) or end the task. The journal is live\journal.demo-b3-p004-win.sqlite, the log live\logs\.
cd /d D:\Trade-Initial
if not exist live\logs mkdir live\logs
echo ==== %DATE% %TIME% start >> live\logs\demo-b3-task.log
live\.venv\Scripts\python.exe -m live.run --config live\config\demo-b3-p004-win.json >> live\logs\demo-b3-task.log 2>&1
echo ==== %DATE% %TIME% exit %ERRORLEVEL% >> live\logs\demo-b3-task.log
