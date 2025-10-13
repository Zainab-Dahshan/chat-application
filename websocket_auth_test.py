import asyncio
import json
import websockets
import requests

# First, get a JWT token
response = requests.post('http://localhost:8000/api/auth/register/', json={
    'username': 'websocketuser',
    'password': 'testpass123',
    'password2': 'testpass123',
    'email': 'websocket@example.com'
})

if response.status_code == 201:
    token = response.json()['access']
    print(f"Got token: {token[:20]}...")
else:
    print(f"Registration failed: {response.status_code} - {response.text}")
    # Try login instead
    response = requests.post('http://localhost:8000/api/token/', json={
        'username': 'websocketuser',
        'password': 'testpass123'
    })
    if response.status_code == 200:
        token = response.json()['access']
        print(f"Got token from login: {token[:20]}...")
    else:
        print("Failed to get token")
        exit(1)

async def test_websocket():
    # Try with token in Authorization header
    uri = "ws://localhost:8000/ws/chat/testroom/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        async with websockets.connect(uri, additional_headers=headers) as websocket:
            print("Connected to WebSocket")
            
            # Send a test message
            message = {
                "message": "Hello from authenticated WebSocket test!"
            }
            await websocket.send(json.dumps(message))
            print(f"Sent: {message}")
            
            # Receive response
            response = await websocket.recv()
            print(f"Received: {response}")
            
            # Wait for a bit to see if we get any more messages
            await asyncio.sleep(2)
            
            try:
                # Try to receive any additional messages
                additional_response = await asyncio.wait_for(websocket.recv(), timeout=1)
                print(f"Additional response: {additional_response}")
            except asyncio.TimeoutError:
                print("No additional messages received")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())