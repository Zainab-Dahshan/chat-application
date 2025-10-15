# Start both backend (Daphne) and frontend (CRA dev server) for local development

param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [string]$VenvScripts = "g:\Freelance\PortofolioProjects\.venv\Scripts"
)

$backendDir = "g:\Freelance\PortofolioProjects\chat-application\chat_backend"
$frontendDir = "g:\Freelance\PortofolioProjects\chat-application\chat-frontend"

Write-Host "Starting backend (Daphne) on port $BackendPort..." -ForegroundColor Cyan
Start-Process -FilePath (Join-Path $VenvScripts "daphne.exe") -ArgumentList "-b 0.0.0.0 -p $BackendPort chat_backend.asgi:application" -WorkingDirectory $backendDir

Write-Host "Starting frontend (CRA dev server) on port $FrontendPort..." -ForegroundColor Cyan
Start-Process -FilePath "npm" -ArgumentList "start" -WorkingDirectory $frontendDir

Write-Host "Both servers launched. Backend: http://localhost:$BackendPort, Frontend: http://localhost:$FrontendPort" -ForegroundColor Green