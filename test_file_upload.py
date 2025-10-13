#!/usr/bin/env python3
"""
Test script for file upload functionality
"""

import requests
import json
import os

def test_file_upload():
    # API base URL
    base_url = "http://127.0.0.1:8000"
    
    # Test user credentials
    username = "websocketuser"
    password = "testpass123"
    
    try:
        # Step 1: Login to get access token
        print("Step 1: Logging in...")
        login_data = {
            "username": username,
            "password": password
        }
        
        response = requests.post(f"{base_url}/api/token/", json=login_data)
        if response.status_code != 200:
            print(f"Login failed: {response.status_code} - {response.text}")
            return
        
        tokens = response.json()
        access_token = tokens['access']
        print(f"✓ Login successful, got access token")
        
        # Step 2: Create a test file
        print("\nStep 2: Creating test file...")
        test_filename = "test_file.txt"
        test_content = "This is a test file for upload functionality."
        
        with open(test_filename, 'w') as f:
            f.write(test_content)
        
        print(f"✓ Created test file: {test_filename}")
        
        # Step 3: Upload the file
        print("\nStep 3: Uploading file...")
        
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
            print(f"✓ File uploaded successfully!")
            print(f"  - File name: {file_info['file_name']}")
            print(f"  - File size: {file_info['file_size']} bytes")
            print(f"  - MIME type: {file_info['mime_type']}")
            print(f"  - File URL: {file_info['file_url']}")
        else:
            print(f"✗ File upload failed: {response.status_code} - {response.text}")
        
        # Step 4: Test sending a file message via WebSocket
        print("\nStep 4: Testing WebSocket file message...")
        print("Note: WebSocket test would require a WebSocket client library")
        print("For now, let's verify the file upload API is working")
        
        # Clean up test file
        os.remove(test_filename)
        print(f"✓ Cleaned up test file")
        
        print("\n✅ File upload functionality test completed!")
        
    except Exception as e:
        print(f"✗ Error during testing: {str(e)}")
        # Clean up test file if it exists
        if os.path.exists(test_filename):
            os.remove(test_filename)

if __name__ == "__main__":
    test_file_upload()