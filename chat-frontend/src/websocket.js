export function connectToWebSocket(roomName, token, onMessage) {
    const socket = new WebSocket(`ws://localhost:8000/ws/chat/${roomName}/`);

    socket.onopen = () => {
        console.log('WebSocket connection established');
        // Send authentication token
        if (token) {
            socket.send(JSON.stringify({
                type: 'auth',
                token: token
            }));
        }
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data);
            
            if (data.type === 'message' && onMessage) {
                onMessage(data);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };

    socket.onclose = (event) => {
        console.log('WebSocket connection closed:', event);
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    return socket;
}

export function sendWebSocketMessage(socket, message) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            message: message
        }));
        return true;
    } else {
        console.error('WebSocket is not connected');
        return false;
    }
}