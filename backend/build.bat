@echo off
echo Building AI Assistant...

cd /d "%~dp0\.."

if exist backend\build rmdir /s /q backend\build
if exist backend\dist rmdir /s /q backend\dist

.venv\Scripts\pyinstaller.exe --distpath backend\dist --workpath backend\build backend\main.spec

echo Build finished!
pause
