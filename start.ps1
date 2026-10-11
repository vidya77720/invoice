# AI Invoice Intelligence System - Windows PowerShell Start Script
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting AI Invoice Intelligence System" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# Start FastAPI in background
Write-Host "Starting FastAPI Backend on http://localhost:8000..." -ForegroundColor Green
$backendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload" -PassThru

Start-Sleep -Seconds 2

# Start Streamlit Frontend
Write-Host "Starting Streamlit Dashboard on http://localhost:8501..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "streamlit run frontend/app.py"

Write-Host "Both Backend and Frontend are starting in separate windows!" -ForegroundColor Yellow
Write-Host "API Swagger Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Streamlit Dashboard: http://localhost:8501" -ForegroundColor Cyan
