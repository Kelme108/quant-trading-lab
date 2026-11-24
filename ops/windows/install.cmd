@echo off
rem Instalação completa no Windows a partir de um clone (ver ops\windows\install.ps1). Exemplos:
rem   ops\windows\install.cmd
rem   ops\windows\install.cmd -SemTestes -SemMT5
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
