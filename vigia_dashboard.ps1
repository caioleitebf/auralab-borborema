# VIGIA do AuraLab Borborema
# Verifica a cada 60s se o dashboard responde em http://localhost:8501
# Se NAO responder: mata processos orfaos e relanca o Streamlit.
# Roda em loop infinito. Registrado como tarefa agendada permanente.

$ErrorActionPreference = "SilentlyContinue"
$proj = "C:\Users\caio.ferreira\OneDrive - Aura Minerals\Documentos\AuraLab_Borborema"
$venv = "$env:USERPROFILE\.auralab_venv\Scripts\python.exe"
$logFile = "$proj\logs\vigia_$(Get-Date -Format 'yyyyMMdd').log"
$intervaloSeg = 60

function Log($msg) {
    $linha = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | $msg"
    Add-Content -Path $logFile -Value $linha -Encoding UTF8
}

function StreamlitVivo {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing -TimeoutSec 5
        return ($r.StatusCode -eq 200)
    } catch {
        return $false
    }
}

function ReiniciarStreamlit {
    Log "Streamlit nao responde. Reiniciando..."
    # Mata qualquer Python tentando rodar Streamlit
    Get-WmiObject Win32_Process -Filter "name='python.exe'" |
        Where-Object { $_.CommandLine -like "*streamlit*" } |
        ForEach-Object {
            Log "  Matando PID $($_.ProcessId)"
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
    Start-Sleep -Seconds 2
    # Sobe Streamlit em background detached
    Set-Location -Path $proj
    $args = "-m streamlit run app/dashboard/streamlit_app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false"
    Start-Process -FilePath $venv -ArgumentList $args -WindowStyle Hidden -WorkingDirectory $proj
    Log "  Streamlit relancado (aguardando ficar pronto)"
    Start-Sleep -Seconds 8
    if (StreamlitVivo) {
        Log "  OK: Streamlit respondendo de novo"
    } else {
        Log "  AVISO: Streamlit ainda nao respondeu"
    }
}

Log "=== Vigia iniciado (intervalo $intervaloSeg s) ==="

while ($true) {
    if (StreamlitVivo) {
        # Quiet - apenas marca de tempo no log a cada hora
        $minuto = (Get-Date).Minute
        if ($minuto -eq 0) {
            Log "Streamlit OK (heartbeat horario)"
        }
    } else {
        ReiniciarStreamlit
    }
    Start-Sleep -Seconds $intervaloSeg
}
