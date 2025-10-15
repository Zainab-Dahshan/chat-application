import React, { useState } from 'react';
import { connectToWebSocket } from './websocket';

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
    const [, setSocket] = useState(null);

    const handleLoginAndConnect = async () => {
        try {
            setStatus('Logging in...');
            const access = await login(username, password);
            setToken(access);
            setStatus('Login successful. Connecting to WebSocket...');
            const newSocket = connectToWebSocket(roomName, access, (msg) => {
                console.log('Message from server:', msg);
            });
            setSocket(newSocket);
            setStatus('Connected.');
        } catch (err) {
            console.error(err);
            setStatus('Login failed. Check credentials.');
        }
    };

    return (
        <div style={{ padding: '1rem' }}>
            <h1>Chat Application</h1>
            <div style={{ marginBottom: '0.5rem' }}>
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
            {status && <p>{status}</p>}
            {token && <p>Token acquired.</p>}
        </div>
    );
}

export default App;
