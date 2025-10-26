import React, { useState } from 'react';
import { connectToWebSocket, sendWebSocketMessage, disconnectWebSocket } from './websocket';

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
    const [connected, setConnected] = useState(false);
    const [autoReconnect, setAutoReconnect] = useState(true);
    const [reconnectInfo, setReconnectInfo] = useState('');
    const [messageText, setMessageText] = useState('');
    const [messages, setMessages] = useState([]);

    const handleLoginAndConnect = async () => {
        try {
            setStatus('Logging in...');
            setReconnectInfo('');
            const access = await login(username, password);
            setToken(access);
            setStatus('Login successful. Connecting to WebSocket...');
            const newSocket = connectToWebSocket(
                roomName,
                access,
                // onMessage
                (msg) => {
                    setMessages((prev) => [...prev, msg]);
                },
                // onOpen
                () => {
                    setConnected(true);
                    setStatus('Connected.');
                    setReconnectInfo('');
                },
                // onClose
                (event) => {
                    setConnected(false);
                    setStatus(`Disconnected${event && event.code ? ` (code ${event.code})` : '.'}`);
                },
                // onError
                (error) => {
                    console.error('WebSocket error:', error);
                    setStatus('WebSocket error. Check console.');
                },
                // options
                {
                    autoReconnect,
                    maxAttempts: Infinity,
                    initialDelay: 500,
                    maxDelay: 10000,
                    backoffFactor: 1.7,
                    jitter: 0.3,
                    onSocketChange: (s) => setSocket(s),
                    onReconnectAttempt: ({ attempt, delayMs }) => {
                        setReconnectInfo(`Reconnecting (attempt ${attempt}) in ${(delayMs / 1000).toFixed(1)}s...`);
                    },
                    onReconnectStop: (reason) => {
                        setReconnectInfo(`Reconnect stopped: ${reason}`);
                    },
                    shouldReconnect: (event) => {
                        // do not auto-reconnect on normal closure 1000; helper already checks this
                        return true;
                    }
                }
            );
            setSocket(newSocket);
        } catch (err) {
            console.error(err);
            setStatus('Login failed. Check credentials.');
        }
    };

    const handleSendMessage = () => {
        if (!socket || !connected) {
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

    const handleDisconnect = () => {
        if (!socket) return;
        disconnectWebSocket(socket);
        setConnected(false);
        setSocket(null);
        setReconnectInfo('');
        setStatus('Disconnected.');
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
                <label style={{ marginRight: '0.5rem' }}>
                    <input
                        type="checkbox"
                        checked={autoReconnect}
                        onChange={(e) => setAutoReconnect(e.target.checked)}
                        style={{ marginRight: '0.25rem' }}
                    />
                    Auto-reconnect
                </label>
                <button onClick={handleLoginAndConnect}>Login & Connect</button>
                <button onClick={handleDisconnect} style={{ marginLeft: '0.5rem' }} disabled={!connected && !socket}>Disconnect</button>
            </div>

            {status && <p style={{ marginTop: 0 }}>{status}</p>}
            {reconnectInfo && <p style={{ marginTop: 0, color: '#555' }}>{reconnectInfo}</p>}
            <p>
                Connection: <strong style={{ color: connected ? 'green' : 'red' }}>{connected ? 'Connected' : 'Disconnected'}</strong>
            </p>
            {token && <p>Token acquired.</p>}

            <div style={{ marginTop: '1rem' }}>
                <input
                    type="text"
                    placeholder="Type a message"
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    style={{ marginRight: '0.5rem', width: '70%' }}
                    disabled={!connected}
                />
                <button onClick={handleSendMessage} disabled={!connected}>Send</button>
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
