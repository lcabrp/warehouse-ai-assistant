@echo off
REM Windows Batch Script to Launch Warehouse AI Assistant Web Interface

echo.
echo ================================================================================
echo WAREHOUSE AI ASSISTANT - WEB INTERFACE
echo ================================================================================
echo.
echo Starting Streamlit web server...
echo.
echo Once started, open your browser to: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.
echo ================================================================================
echo.

cd /d "%~dp0"
uv run streamlit run web_app.py
