@echo off
echo 🔨 Building AI Assistant...

call .venv\Scripts\activate

rmdir /s /q build
rmdir /s /q dist

pyinstaller main.spec

echo ✅ Build finished!
pause
