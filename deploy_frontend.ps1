# Frontend deployment script for React chat application (Windows PowerShell)

Write-Host "Building React frontend for production..." -ForegroundColor Cyan

Push-Location "chat-frontend"

try {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install

    Write-Host "Building production bundle..." -ForegroundColor Yellow
    npm run build

    $serverJs = @'
const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;

// Serve static files from the React app
app.use(express.static(path.join(__dirname, 'build')));

// Handle React routing, return all requests to React app
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Frontend server running on port ${PORT}`);
});
'@

    Set-Content -Path server.js -Value $serverJs -Encoding UTF8

    Write-Host "Installing express for serving the built files..." -ForegroundColor Yellow
    npm install express

    Write-Host "Frontend build complete!" -ForegroundColor Green
    Write-Host "To deploy:" -ForegroundColor White
    Write-Host "1. Upload the chat-frontend directory to your hosting service"
    Write-Host "2. Run 'node server.js' to start the frontend server"
    Write-Host "3. Update API URLs in .env to point to your backend"
}
finally {
    Pop-Location
}