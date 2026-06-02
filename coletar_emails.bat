@echo off
REM Roda o coletor de emails uma vez.
REM   - sem argumentos: ultimas 24h
REM   - --since-days N: ultimos N dias
REM   - --backlog: tudo desde 01/01/2026

cd /d "%~dp0"
"%USERPROFILE%\.auralab_venv\Scripts\python.exe" -m app.collector %*
