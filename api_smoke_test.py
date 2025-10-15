import requests
import json

BASE_URL = "http://127.0.0.1:8000"

username = "testuser3"
password = "testpass123"
email = "test3@example.com"

print("API smoke test starting...")

# Try register, fallback to login
register_data = {
    "username": username,
    "password": password,
    "password2": password,
    "email": email,
}

resp = requests.post(f"{BASE_URL}/api/auth/register/", json=register_data)
print(f"Register status: {resp.status_code}")

access = None
if resp.status_code == 201:
    data = resp.json()
    access = data.get("access")
    print("Registered and obtained access token")
else:
    print("Registration failed, attempting login...")
    login_resp = requests.post(
        f"{BASE_URL}/api/token/", json={"username": username, "password": password}
    )
    print(f"Login status: {login_resp.status_code}")
    if login_resp.status_code == 200:
        access = login_resp.json().get("access")
        print("Logged in and obtained access token")
    else:
        print(f"Login failed: {login_resp.text}")
        exit(1)

headers = {"Authorization": f"Bearer {access}"}

# Create room
room_data = {"name": "Smoke Test Room"}
room_resp = requests.post(f"{BASE_URL}/api/auth/rooms/", json=room_data, headers=headers)
print(f"Create room status: {room_resp.status_code}")
print(room_resp.text)

if room_resp.status_code not in (200, 201):
    print("Room creation failed; trying to list rooms...")
    rooms_list = requests.get(f"{BASE_URL}/api/auth/rooms/", headers=headers)
    print(f"List rooms status: {rooms_list.status_code}")
    print(rooms_list.text)
    # Attempt to use first room if available
    try:
        rooms = rooms_list.json()
        if rooms and isinstance(rooms, list):
            room_id = rooms[0]["id"] if isinstance(rooms[0], dict) else None
        else:
            room_id = None
    except Exception:
        room_id = None
else:
    room_id = room_resp.json().get("id")

if not room_id:
    print("No room_id available, exiting.")
    exit(1)

# Send message
msg_resp = requests.post(
    f"{BASE_URL}/api/auth/rooms/{room_id}/send-message/",
    json={"message": "Hello from smoke test!"},
    headers=headers,
)
print(f"Send message status: {msg_resp.status_code}")
print(msg_resp.text)

# Get messages
messages_resp = requests.get(
    f"{BASE_URL}/api/auth/rooms/{room_id}/messages/",
    headers=headers,
)
print(f"Get messages status: {messages_resp.status_code}")
print(messages_resp.text)

print("API smoke test completed.")