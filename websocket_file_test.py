#!/usr/bin/env python3
"""
WebSocket test script for file sharing functionality
"""

import asyncio
import websockets
import json
import requests
import os

def get_access_token():
    """Get JWT access token"""
    base_url = "http://127.0.0.1:8000"
    
    # Try to login with existing user
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
    
    # Create test file
    test_filename = "websocket_test.txt"
    test_content = "This is a test file for WebSocket file sharing."
    
    with open(test_filename, 'w') as f:
        f.write(test_content)
    
    try:
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        with open(test_filename, 'rb') as f:
            files = {'file': (test_filename, f, 'text/plain')}
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
    """Test WebSocket file sharing"""
    access_token = get_access_token()
    if not access_token:
        return
    
    file_info = upload_test_file()
    if not file_info:
        return
    
    uri = "ws://127.0.0.1:8000/ws/chat/testroom/"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"\n✓ Connected to WebSocket at {uri}")
            
            # Authenticate
            auth_message = {
                'type': 'authenticate',
                'token': access_token
            }
            
            await websocket.send(json.dumps(auth_message))
            auth_response = await websocket.recv()
            auth_data = json.loads(auth_response)
            
            if auth_data.get('type') == 'authentication_success':
                print(f"✓ Authentication successful: {auth_data.get('message')}")
                
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
                for i in range(3):  # Listen for up to 3 messages
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        response_data = json.loads(response)
                        print(f"Received: {response_data}")
                    except asyncio.TimeoutError:
                        print("Timeout waiting for response")
                        break
                
                print("\n✅ WebSocket file sharing test completed successfully!")
                
            else:
                print(f"✗ Authentication failed: {auth_data.get('message', 'Unknown error')}")
                
    except Exception as e:
        print(f"✗ WebSocket error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting WebSocket file sharing test...")
    asyncio.run(test_websocket_file_sharing())