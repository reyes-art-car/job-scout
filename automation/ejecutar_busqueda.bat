@echo off
:: Busqueda diaria de ofertas — Maria Reyes Artacho Carrero
:: Ejecutado automaticamente por el Programador de Tareas de Windows

cd /d "%~dp0.."

:: Crear carpeta de logs si no existe
if not exist "logs" mkdir logs

:: Nombre del log con la fecha de hoy
:: NOTA: automation\busqueda_diaria.py escribe su propio resumen final en logs\busqueda_YYYYMMDD.txt
:: Por eso la consola de este .bat se redirige a un archivo distinto (consola_YYYYMMDD.txt),
:: para evitar que dos procesos abran el mismo archivo a la vez (causaba PermissionError).
set CONSOLE_LOG=logs\consola_%date:~-4,4%%date:~3,2%%date:~0,2%.txt

:: Ejecutar el script Python (usa Claude Code CLI con tu suscripcion actual)
:: 1) Busqueda general (LinkedIn, Indeed, Infojobs, Tecnoempleo, Computrabajo, Jobandtalent)
echo Iniciando busqueda diaria general %date% %time% >> "%CONSOLE_LOG%"
C:\Python313\python.exe automation\busqueda_diaria.py >> "%CONSOLE_LOG%" 2>&1
echo Finalizada busqueda general %time% >> "%CONSOLE_LOG%"

:: 2) Busqueda exhaustiva solo en LinkedIn (complementa a la general)
echo Iniciando busqueda LinkedIn %date% %time% >> "%CONSOLE_LOG%"
C:\Python313\python.exe automation\busqueda_diaria.py --portal linkedin >> "%CONSOLE_LOG%" 2>&1
echo Finalizada busqueda LinkedIn %time% >> "%CONSOLE_LOG%"

:: 3) Busqueda en empresas internacionales (fuera de Espana, 100% remoto, ES/EN)
echo Iniciando busqueda Europa/Internacional %date% %time% >> "%CONSOLE_LOG%"
C:\Python313\python.exe automation\busqueda_diaria.py --portal europa >> "%CONSOLE_LOG%" 2>&1
echo Finalizada busqueda Europa/Internacional %time% >> "%CONSOLE_LOG%"
