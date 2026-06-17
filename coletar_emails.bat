@echo off
REM Roda o coletor de emails e, em seguida, sincroniza o banco SQLite com o GitHub
REM (que faz o Streamlit Cloud atualizar automaticamente).

cd /d "%~dp0"

REM 1. Coleta emails
"%USERPROFILE%\.auralab_venv\Scripts\python.exe" -m app.collector %*
if errorlevel 1 (
    echo Coletor terminou com erro. Pulando sync.
    exit /b 1
)

REM 2. Verifica se houve mudanca no banco e faz push automatico (silencioso)
git diff --quiet --exit-code database/auralab.db
if errorlevel 1 (
    echo.
    echo === Sincronizando banco com GitHub ===
    git add database/auralab.db
    git commit -m "Auto-sync banco: coleta %DATE% %TIME%" --no-verify
    git push origin main 2>&1
    if errorlevel 1 (
        echo AVISO: push falhou. Cloud nao foi atualizado.
        echo Rode sync_inicial.bat se for a primeira vez.
    ) else (
        echo OK - Streamlit Cloud sera atualizado em ~1 minuto.
    )
) else (
    echo Banco sem mudancas - nada para sincronizar.
)
