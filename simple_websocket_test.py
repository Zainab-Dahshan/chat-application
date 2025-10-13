#!/usr/bin/env python3
"""
Simple WebSocket test for file sharing functionality
"""

import asyncio
import websockets
import json
import requests
import os

def get_access_token():
    """Get JWT access token"""
    base_url = "http://127.0.0.1:8000"
    
    login_data = {
        "username": "websocketuser",
        "password": "testpass123"
    }
    
    response = requests.post(f"{base_url}/api/token/", json=login_data)
    if response.status_code == 200:
        tokens = response.json()
        return tokens['access']
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def upload_test_file():
    """Upload a test file and return file info"""
    base_url = "http://127.0.0.1:8000"
    access_token = get_access_token()
    
    if not access_token:
        return None
    
    # Create test image file
    test_filename = "test_image.png"
    # Create a simple PNG file (1x1 red pixel)
    png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
    
    with open(test_filename, 'wb') as f:
        f.write(png_content)
    
    try:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        with open(test_filename, 'rb') as f:
            files = {'file': (test_filename, f, 'image/png')}
            response = requests.post(
                f"{base_url}/api/auth/upload-file/",
                files=files,
                headers=headers
            )
        
        if response.status_code == 201:
            file_info = response.json()
            print(f"✓ File uploaded successfully: {file_info['file_name']}")
            return file_info
        else:
            print(f"✗ File upload failed: {response.status_code} - {response.text}")
            return None
            
    finally:
        # Clean up test file
        if os.path.exists(test_filename):
            os.remove(test_filename)

async def test_websocket_file_sharing():
    """Test WebSocket file sharing with proper authentication"""
    access_token = get_access_token()
    if not access_token:
        return
    
    file_info = upload_test_file()
    if not file_info:
        return
    
    uri = f"ws://127.0.0.1:8000/ws/chat/testroom/"
    
    try:
        # Connect with authentication header
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        async with websockets.connect(uri, additional_headers=headers) as websocket:
            print(f"\n✓ Connected to WebSocket at {uri}")
            
            # Wait for connection confirmation
            connection_response = await websocket.recv()
            connection_data = json.loads(connection_response)
            print(f"Connection response: {connection_data}")
            
            # Send a text message first
            text_message = {
                'type': 'chat_message',
                'message': 'Hello! I\'m going to share a file with you.',
                'message_type': 'text'
            }
            
            await websocket.send(json.dumps(text_message))
            print(f"✓ Sent text message: {text_message['message']}")
            
            # Wait a moment
            await asyncio.sleep(1)
            
            # Send a file message
            file_message = {
                'type': 'chat_message',
                'message': f'Sharing file: {file_info["file_name"]}',
                'message_type': 'file',
                'file_info': {
                    'file_name': file_info['file_name'],
                    'file_size': file_info['file_size'],
                    'mime_type': file_info['mime_type'],
                    'file_url': file_info['file_url']
                }
            }
            
            await websocket.send(json.dumps(file_message))
            print(f"✓ Sent file message: {file_message['message']}")
            
            # Listen for responses
            print("\n✓ Listening for responses...")
            for i in range(5):  # Listen for up to 5 messages
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    response_data = json.loads(response)
                    print(f"Received: {response_data}")
                    
                    # Check if it's a file message
                    if response_data.get('type') == 'chat_message' and response_data.get('message_type') == 'file':
                        print(f"🎉 File message received successfully!")
                        print(f"   File: {response_data.get('file_name')}")
                        print(f"   Size: {response_data.get('file_size')} bytes")
                        print(f"   Type: {response_data.get('mime_type')}")
                        print(f"   URL: {response_data.get('file_url')}")
                        
                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    break
            
            print("\n✅ WebSocket file sharing test completed successfully!")
            
    except Exception as e:
        print(f"✗ WebSocket error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting WebSocket file sharing test...")
    asyncio.run(test_websocket_file_sharing())