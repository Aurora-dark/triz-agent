@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

title TRIZ 智能体启动器

set "OLLAMA_MODELS=D:\OllamaModels"
set "OLLAMA_HOST=127.0.0.1:11434"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "PYTHON=%~dp0.venv\Scripts\python.exe"
set "MODEL=qwen2.5:3b"
set "URL=http://127.0.0.1:8000"

if not exist "%PYTHON%" (
    echo [错误] 未找到 .venv\Scripts\python.exe
    echo        请在项目目录执行: python -m venv .venv
    pause
    exit /b 1
)

echo ============================================================
echo   TRIZ 智能体 · 本地启动
echo ============================================================

echo [1/3] 检查 Ollama 服务 ...
powershell -NoProfile -Command "$c=New-Object Net.Sockets.TcpClient; try { $c.Connect('127.0.0.1',11434); $c.Close(); exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo       未运行，正在启动 ollama serve ...
    start "Ollama" /min ollama serve
    powershell -NoProfile -Command "for($i=0;$i -lt 30;$i++){ $c=New-Object Net.Sockets.TcpClient; try { $c.Connect('127.0.0.1',11434); $c.Close(); exit 0 } catch { Start-Sleep -Seconds 1 } }; exit 1"
    if errorlevel 1 (
        echo [错误] Ollama 启动超时，请手动运行: ollama serve
        pause
        exit /b 1
    )
)

echo [2/3] 检查模型 %MODEL% ...
ollama list 2>nul | findstr /C:"%MODEL%" >nul
if errorlevel 1 (
    echo       本地没有 %MODEL%，开始拉取（首次需要较长时间）...
    ollama pull %MODEL%
    if errorlevel 1 (
        echo [错误] 模型拉取失败，请检查网络后重试
        pause
        exit /b 1
    )
)

echo [3/3] 启动 Web 服务 %URL% ...
if not defined NO_BROWSER (
    start "" cmd /c "timeout /t 2 >nul & start %URL%"
)
"%PYTHON%" -m uvicorn api.main:app --host 127.0.0.1 --port 8000

echo.
echo 服务已退出。
pause
