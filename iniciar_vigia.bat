@echo off
REM Lancador do vigia em background (sem janela visivel).
REM Roda em loop infinito vigiando o Streamlit.

cd /d "%~dp0"
start "" /B powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0vigia_dashboard.ps1"
