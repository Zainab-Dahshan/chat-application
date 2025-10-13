#!/bin/bash

# Backend deployment script for Django Chat Application

echo "🚀 Starting Chat Application Backend Deployment..."

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Please run this script from the chat_backend directory"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🔧 Setting up production settings..."
export DJANGO_SETTINGS_MODULE=chat_backend.settings_production

echo "🗄️ Running database migrations..."
python manage.py migrate

echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Backend deployment preparation complete!"
echo ""
echo "📝 Next steps:"
echo "1. Set up your environment variables (.env file)"
echo "2. Configure your database (PostgreSQL recommended)"
echo "3. Set up Redis for production channel layer"
echo "4. Run the server with: daphne -b 0.0.0.0 -p 8000 chat_backend.asgi:application"
echo "5. Or use a process manager like systemd or supervisor"
echo ""
echo "🔍 For detailed deployment instructions, see DEPLOYMENT_GUIDE.md"