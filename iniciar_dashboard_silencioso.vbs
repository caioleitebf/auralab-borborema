' AuraLab Borborema - lancador silencioso do dashboard (sem janela cmd visivel).
' Roda iniciar_dashboard.bat em segundo plano via WScript.Shell.

Set WshShell = CreateObject("WScript.Shell")
strScript = WScript.ScriptFullName
strDir = Left(strScript, InStrRev(strScript, "\"))
WshShell.Run Chr(34) & strDir & "iniciar_dashboard.bat" & Chr(34), 0, False
