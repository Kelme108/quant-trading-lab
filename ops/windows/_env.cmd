@echo off
rem Shared by the ops\windows launchers (clone-ready: nothing here depends on where the repository lives).
rem   ROOT = the repository, two folders above this file.
rem   PY   = the Python to use: ROOT\.venv (made by bootstrap.py), else C:\Python314 (the owner's machine), else python on PATH.
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
set "PY=python"
if exist "C:\Python314\python.exe" set "PY=C:\Python314\python.exe"
if exist "%ROOT%\.venv\Scripts\python.exe" set "PY=%ROOT%\.venv\Scripts\python.exe"
