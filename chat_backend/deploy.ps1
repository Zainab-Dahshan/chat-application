# Backend deployment script for Django Chat Application (Windows PowerShell)

param(
    [string]$PythonPath = "g:\Freelance\PortofolioProjects\.venv\Scripts\python.exe",
    [string]$PipPath = "g:\Freelance\PortofolioProjects\.venv\Scripts\pip.exe"
)

Write-Host "🚀 Starting Chat Application Backend Deployment..." -ForegroundColor Cyan

# Ensure we're in the chat_backend directory
if (-not (Test-Path "manage.py")) {
    Write-Host "❌ Error: Please run this script from the chat_backend directory" -ForegroundColor Red
    exit 1
}

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
& $PipPath install -r requirements.txt

Write-Host "🔧 Setting up production settings..." -ForegroundColor Yellow
$env:DJANGO_SETTINGS_MODULE = "chat_backend.settings_production"

Write-Host "🗄️ Running database migrations..." -ForegroundColor Yellow
& $PythonPath manage.py migrate

Write-Host "📁 Collecting static files..." -ForegroundColor Yellow
& $PythonPath manage.py collectstatic --noinput

Write-Host "✅ Backend deployment preparation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor White
Write-Host "1. Set up your environment variables (.env file)"
Write-Host "2. Configure your database (PostgreSQL recommended)"
Write-Host "3. Set up Redis for production channel layer"
Write-Host "4. Run the server with: daphne -b 0.0.0.0 -p 8000 chat_backend.asgi:application"
Write-Host "5. Or use a process manager like NSSM or a Windows service"
Write-Host ""
Write-Host "🔍 For detailed deployment instructions, see DEPLOYMENT_GUIDE.md"