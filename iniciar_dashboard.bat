@echo off
REM Inicia o dashboard AuraLab Borborema na porta 8501.
REM Acessivel em http://localhost:8501 e http://<seu-ip>:8501
REM
REM Inclui verificacao para EVITAR duplicidade (multiplas instancias na mesma porta)

cd /d "%~dp0"

REM 1. Verifica se ja existe alguem ouvindo na porta 8501
netstat -ano | findstr ":8501 " | findstr "LISTENING" >nul
if %ERRORLEVEL% EQU 0 (
    echo Streamlit ja esta rodando na porta 8501. Nao vou iniciar de novo.
    exit /b 0
)

REM 2. Mata qualquer Python orfao que esteja tentando rodar Streamlit
for /f "tokens=2" %%P in ('wmic process where "name='python.exe' and CommandLine like '%%streamlit%%'" get ProcessId /VALUE 2^>nul ^| findstr "="') do (
    taskkill /F /PID %%P >nul 2>nul
)

REM 3. Sobe o Streamlit usando EXCLUSIVAMENTE o Python do venv
"%USERPROFILE%\.auralab_venv\Scripts\python.exe" -m streamlit run app\dashboard\streamlit_app.py --server.port 8501 --browser.gatherUsageStats false
