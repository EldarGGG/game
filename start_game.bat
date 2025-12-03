@echo off
chcp 65001 >nul
echo ============================================
echo    ECO RANGER - Экологическая игра
echo ============================================
echo.
echo Запуск игры...
echo.

python main.py

if errorlevel 1 (
    echo.
    echo ОШИБКА! Убедитесь, что Python и Pygame установлены.
    echo Установите зависимости: pip install -r requirements.txt
    echo.
    pause
)
