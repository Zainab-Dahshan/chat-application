export function connectToWebSocket(roomName) {
    const socket = new WebSocket(`ws://localhost:8000/ws/chat/${roomName}/`);

    socket.onopen = () => {
        console.log('WebSocket connection established');
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Message received:', data.message);
    };

    socket.onclose = (event) => {
        console.log('WebSocket connection closed:', event);
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    return socket;
}