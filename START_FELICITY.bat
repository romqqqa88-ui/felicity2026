@echo off
chcp 65001 > nul
title Felicity AI Engine & Telegram Bot Launcher
cls
echo ============================================================
echo   🌸 Felicity AI Engine & Autonomous Telegram Bot
echo ============================================================
echo.
echo [1/3] Запуск Веб-Студии Felicity (http://localhost:8080)...
start /b python felicity_server.py > data\server.log 2>&1

echo [2/3] Запуск Телеграм-Бота и Автономного Разума...
start /b python start_bot.py 8982132923:AAHFukTJ-ydzvUQgecZ_lSVCzLWwU3-OlKc > data\bot.log 2>&1

echo [3/3] Открытие Веб-Студии в браузере...
timeout /t 2 /nobreak > nul
start http://localhost:8080

echo.
echo ============================================================
echo   🟢 ВСЕ СИСТЕМЫ ФЕЛИСИТИ УСПЕШНО ЗАПУЩЕНЫ!
echo   Вы можете свернуть это окно. Бот работает в фоновом режиме.
echo ============================================================
echo.
pause
