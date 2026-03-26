@echo off
REM Windows Batch Script to Launch Warehouse AI Assistant CLI

echo.
echo ================================================================================
echo 🏭 WAREHOUSE AI ASSISTANT - CLI INTERFACE
echo ================================================================================
echo.
echo Starting command-line interface...
echo.
echo Type 'help' for example questions
echo Type 'exit' or 'quit' to close
echo.
echo ================================================================================
echo.

cd /d "%~dp0"
uv run python main.py
