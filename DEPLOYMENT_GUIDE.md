# Chat Application Deployment Guide

This guide provides step-by-step instructions for deploying the chat application to production.

## Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+ (for production)
- Git

## Backend Deployment

### 1. Environment Setup

Create a `.env` file in the `chat_backend` directory:

```bash
# Security
SECRET_KEY=your-very-secret-key-here
DEBUG=False

# Database
DB_NAME=chat_production_db
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Redis (for production)
REDIS_URL=redis://localhost:6379

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# CORS
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
```

### 2. Database Setup

```bash
# Create PostgreSQL database
createdb chat_production_db

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 3. Static Files

```bash
# Collect static files
python manage.py collectstatic --noinput
```

### 4. Production Settings

Use the production settings:

```bash
# Set environment variable
export DJANGO_SETTINGS_MODULE=chat_backend.settings_production

# Or run with specific settings
python manage.py runserver --settings=chat_backend.settings_production
```

### 5. Running the Server

For production, use Daphne (ASGI server):

```bash
# Install production dependencies
pip install -r requirements.txt

# Run with Daphne
daphne -b 0.0.0.0 -p 8000 chat_backend.asgi:application
```

### 6. Using Gunicorn (Alternative)

For WSGI deployment (HTTP only, no WebSockets):

```bash
pip install gunicorn
gunicorn chat_backend.wsgi:application --bind 0.0.0.0:8000
```

## Frontend Deployment

### 1. Build the Frontend

```bash
cd chat-frontend
npm install
npm run build
```

### 2. Serve the Build

Option 1: Using the deployment script
```bash
bash deploy_frontend.sh
node chat-frontend/server.js
```

Option 2: Using a web server (nginx, Apache)
- Copy the `build` folder to your web server's document root
- Configure your web server to serve the files

### 3. Update API URLs

Update the API base URL in your React app to point to your backend:

```javascript
// In your API service files
const API_BASE_URL = 'https://your-backend-domain.com/api';
const WS_URL = 'wss://your-backend-domain.com/ws';
```

## Platform-Specific Deployment

### Heroku Deployment

1. **Backend Setup:**
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create Heroku app
heroku create your-chat-app

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis (optional)
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False

# Deploy
git push heroku main
```

2. **Frontend Setup:**
- Build the frontend locally
- Deploy to a static hosting service (Netlify, Vercel, GitHub Pages)
- Update the API URLs

### DigitalOcean Deployment

1. **Create Droplet:**
- Ubuntu 20.04 LTS
- At least 2GB RAM
- Install PostgreSQL, Redis, Nginx

2. **Setup:**
```bash
# Clone repository
git clone your-repo.git
cd chat-application

# Setup backend (follow general instructions above)
cd chat_backend
pip install -r requirements.txt

# Setup frontend
cd ../chat-frontend
npm install
npm run build

# Configure Nginx (see nginx configuration below)
```

## Nginx Configuration

Create `/etc/nginx/sites-available/chat-app`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /path/to/chat-frontend/build;
        try_files $uri /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Media files
    location /media/ {
        alias /path/to/chat_backend/media/;
    }

    # Static files
    location /static/ {
        alias /path/to/chat_backend/staticfiles/;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/chat-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Systemd Service

Create `/etc/systemd/system/chat-backend.service`:

```ini
[Unit]
Description=Chat Backend
After=network.target

[Service]
User=your-user
Group=your-group
WorkingDirectory=/path/to/chat-application/chat_backend
Environment="PATH=/path/to/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=chat_backend.settings_production"
ExecStart=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 chat_backend.asgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable chat-backend
sudo systemctl start chat-backend
```

## Monitoring and Maintenance

### Logs
```bash
# Backend logs
tail -f /path/to/chat_backend/logs/django.log

# System logs
sudo journalctl -u chat-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Database Backup
```bash
# Create backup
pg_dump chat_production_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql chat_production_db < backup_file.sql
```

### Updates
```bash
# Update code
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Restart service
sudo systemctl restart chat-backend
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed:**
   - Check if Daphne is running
   - Verify Nginx WebSocket configuration
   - Check firewall settings

2. **Static Files Not Loading:**
   - Run `python manage.py collectstatic`
   - Check STATIC_ROOT and STATIC_URL settings
   - Verify Nginx static files configuration

3. **Database Connection Issues:**
   - Check PostgreSQL is running
   - Verify database credentials
   - Check firewall settings

4. **CORS Errors:**
   - Update CORS_ALLOWED_ORIGINS in settings
   - Check frontend API URLs

### Performance Optimization

- Use Redis for caching
- Enable Gzip compression in Nginx
- Use CDN for static files
- Optimize database queries
- Monitor with tools like New Relic or DataDog

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Use HTTPS
- [ ] Configure proper CORS settings
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Backup data regularly
- [ ] Use strong passwords
- [ ] Enable rate limiting

## Support

For issues or questions:
- Check the logs first
- Verify all services are running
- Test connectivity between services
- Review configuration files