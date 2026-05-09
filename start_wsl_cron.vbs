Set objShell = CreateObject("WScript.Shell")
objShell.Run "wsl sudo service cron start", 0, False
