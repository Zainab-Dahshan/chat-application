import React, { useState } from 'react';
import { connectToWebSocket, sendWebSocketMessage } from './websocket';

async function login(username, password) {
    const apiBase = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';
    const res = await fetch(`${apiBase}/token/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    if (!res.ok) {
        throw new Error(`Login failed: ${res.status}`);
    }
    const data = await res.json();
    return data.access;
}

function App() {
    const [roomName, setRoomName] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [token, setToken] = useState('');
    const [status, setStatus] = useState('');
    const [socket, setSocket] = useState(null);
    const [messageText, setMessageText] = useState('');
    const [messages, setMessages] = useState([]);

    const handleLoginAndConnect = async () => {
        try {
            setStatus('Logging in...');
            const access = await login(username, password);
            setToken(access);
            setStatus('Login successful. Connecting to WebSocket...');
            const newSocket = connectToWebSocket(roomName, access, (msg) => {
                // msg expected shape: { type: 'message', ... }
                setMessages((prev) => [...prev, msg]);
            });
            setSocket(newSocket);
            setStatus('Connected.');
        } catch (err) {
            console.error(err);
            setStatus('Login failed. Check credentials.');
        }
    };

    const handleSendMessage = () => {
        if (!socket) {
            setStatus('Not connected.');
            return;
        }
        if (!messageText.trim()) {
            return;
        }
        const ok = sendWebSocketMessage(socket, messageText.trim());
        if (ok) {
            setMessageText('');
        }
    };

    return (
        <div style={{ padding: '1rem', maxWidth: 640 }}>
            <h1>Chat Application</h1>
            <div style={{ marginBottom: '0.75rem' }}>
                <input
                    type="text"
                    placeholder="Room name"
                    value={roomName}
                    onChange={(e) => setRoomName(e.target.value)}
                    style={{ marginRight: '0.5rem' }}
                />
                <input
                    type="text"
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    style={{ marginRight: '0.5rem' }}
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    style={{ marginRight: '0.5rem' }}
                />
                <button onClick={handleLoginAndConnect}>Login & Connect</button>
            </div>
            {status && <p style={{ marginTop: 0 }}>{status}</p>}
            {token && <p>Token acquired.</p>}

            <div style={{ marginTop: '1rem' }}>
                <input
                    type="text"
                    placeholder="Type a message"
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    style={{ marginRight: '0.5rem', width: '70%' }}
                />
                <button onClick={handleSendMessage}>Send</button>
            </div>

            <div style={{ marginTop: '1rem' }}>
                <h2>Messages</h2>
                <ul style={{ listStyle: 'none', padding: 0 }}>
                    {messages.map((m, idx) => (
                        <li key={idx} style={{ padding: '0.25rem 0', borderBottom: '1px solid #eee' }}>
                            <code>{JSON.stringify(m)}</code>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}

export default App;
