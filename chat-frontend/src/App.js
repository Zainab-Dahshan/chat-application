import React, { useState } from 'react';
import { connectToWebSocket } from './websocket';

function App() {
    const [roomName, setRoomName] = useState('');
    const [, setSocket] = useState(null);

    const handleConnect = () => {
        const newSocket = connectToWebSocket(roomName);
        setSocket(newSocket);
    };

    return (
        <div>
            <h1>Chat Application</h1>
            <input
                type="text"
                placeholder="Enter room name"
                value={roomName}
                onChange={(e) => setRoomName(e.target.value)}
            />
            <button onClick={handleConnect}>Connect</button>
        </div>
    );
}

export default App;
