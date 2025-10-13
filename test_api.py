import requests
import json

# Test user registration with new username
print("Testing user registration...")
register_data = {
    "username": "testuser3",
    "password": "testpass123",
    "password2": "testpass123",
    "email": "test3@example.com"
}

try:
    response = requests.post("http://127.0.0.1:8000/api/auth/register/", 
                           json=register_data)
    print(f"Registration Status: {response.status_code}")
    print(f"Registration Response: {response.text}")
    
    if response.status_code == 201:
        data = response.json()
        access_token = data.get('access')
        refresh_token = data.get('refresh')
        
        print(f"Access Token: {access_token[:20]}..." if access_token else "No access token")
        print(f"Refresh Token: {refresh_token[:20]}..." if refresh_token else "No refresh token")
        
        # Test room creation
        print("\nTesting room creation...")
        headers = {'Authorization': f'Bearer {access_token}'}
        room_data = {"name": "Test Room 2"}
        
        room_response = requests.post("http://127.0.0.1:8000/api/auth/rooms/",
                                    json=room_data, headers=headers)
        print(f"Room Creation Status: {room_response.status_code}")
        print(f"Room Creation Response: {room_response.text}")
        
        # Test sending a message
        if room_response.status_code == 201:
            room_data = room_response.json()
            room_id = room_data.get('id')
            
            print("\nTesting sending message...")
            message_data = {"message": "Hello, world!"}
            message_response = requests.post(f"http://127.0.0.1:8000/api/auth/rooms/{room_id}/send-message/",
                                          json=message_data, headers=headers)
            print(f"Send Message Status: {message_response.status_code}")
            print(f"Send Message Response: {message_response.text}")
            
            # Test getting messages
            print("\nTesting getting messages...")
            messages_response = requests.get(f"http://127.0.0.1:8000/api/auth/rooms/{room_id}/messages/",
                                            headers=headers)
            print(f"Get Messages Status: {messages_response.status_code}")
            print(f"Get Messages Response: {messages_response.text}")
        
    else:
        print("Registration failed, cannot proceed with other tests")
        
except Exception as e:
    print(f"Error: {e}")

print("\nAPI testing completed!")