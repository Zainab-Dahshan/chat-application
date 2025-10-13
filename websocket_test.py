import asyncio
import json
import websockets

async def test_websocket():
    uri = "ws://localhost:8000/ws/chat/testroom/"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            
            # Send a test message
            message = {
                "message": "Hello from WebSocket test!"
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