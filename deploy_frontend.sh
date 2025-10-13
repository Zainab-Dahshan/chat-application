#!/bin/bash

# Frontend deployment script for React chat application

echo "Building React frontend for production..."

# Navigate to frontend directory
cd chat-frontend

# Install dependencies
echo "Installing dependencies..."
npm install

# Build the application
echo "Building production bundle..."
npm run build

# Create a simple server script for serving the built files
cat > server.js << 'EOF'
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
EOF

# Install express for serving the built files
npm install express

echo "Frontend build complete!"
echo "To deploy:"
echo "1. Upload the chat-frontend directory to your hosting service"
echo "2. Run 'node server.js' to start the frontend server"
echo "3. Make sure to update the API URLs in your React app to point to your backend"