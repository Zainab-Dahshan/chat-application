// WebSocket helper with optional auto-reconnect and exponential backoff
// Usage:
// connectToWebSocket(room, token, onMessage, onOpen, onClose, onError, {
//   autoReconnect: true,
//   maxAttempts: Infinity,
//   initialDelay: 500,
//   maxDelay: 10000,
//   backoffFactor: 1.7,
//   jitter: 0.3, // 30% jitter
//   onSocketChange: (newSocket) => {},
//   onReconnectAttempt: ({ attempt, delayMs }) => {},
//   onReconnectStop: (reason) => {},
//   shouldReconnect: (event) => boolean // optional filter
// })
export function connectToWebSocket(
  roomName,
  token,
  onMessage,
  onOpen,
  onClose,
  onError,
  options = {}
) {
  const wsBase = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

  const {
    autoReconnect = false,
    maxAttempts = Infinity,
    initialDelay = 500,
    maxDelay = 10000,
    backoffFactor = 1.7,
    jitter = 0.3,
    onSocketChange,
    onReconnectAttempt,
    onReconnectStop,
    shouldReconnect,
  } = options || {};

  let attempt = 0;
  let forcedClose = false;
  // (removed unused variable)

  function applyJitter(baseMs) {
    const spread = baseMs * jitter;
    // Random between [-spread, +spread]
    return Math.max(0, baseMs + (Math.random() * 2 - 1) * spread);
  }

  function nextDelayMs() {
    const exp = initialDelay * Math.pow(backoffFactor, Math.max(0, attempt - 1));
    return Math.min(maxDelay, exp);
  }

  function openSocket() {
    const socket = new WebSocket(`${wsBase}/chat/${roomName}/`);
// (variable removed – was unused)
    if (typeof onSocketChange === 'function') {
      onSocketChange(socket);
    }

    socket.onopen = (event) => {
      console.log('WebSocket connection established');
      attempt = 0; // reset attempts on successful connect
      // Send authentication token if provided
      if (token) {
        try {
          socket.send(JSON.stringify({ type: 'auth', token }));
        } catch (e) {
          console.error('Error sending auth token:', e);
        }
      }
      if (typeof onOpen === 'function') {
        onOpen(event);
      }
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        if (typeof onMessage === 'function') {
          onMessage(data);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    socket.onclose = (event) => {
      console.log('WebSocket connection closed:', event);
      if (typeof onClose === 'function') {
        onClose(event);
      }

      // Decide whether to reconnect
      const normalClosure = event && event.code === 1000;
      const allowedByFilter = typeof shouldReconnect === 'function' ? !!shouldReconnect(event) : true;
      const mayReconnect = autoReconnect && !forcedClose && !normalClosure && allowedByFilter;

      if (mayReconnect && attempt < maxAttempts) {
        attempt += 1;
        const delay = applyJitter(nextDelayMs());
        if (typeof onReconnectAttempt === 'function') {
          onReconnectAttempt({ attempt, delayMs: Math.round(delay) });
        }
        setTimeout(() => {
          // re-open connection
          openSocket();
        }, delay);
      } else if (!normalClosure && !forcedClose && autoReconnect) {
        // Ran out of attempts or filter disallowed
        if (typeof onReconnectStop === 'function') {
          onReconnectStop(attempt >= maxAttempts ? 'max_attempts' : 'filtered');
        }
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (typeof onError === 'function') {
        onError(error);
      }
    };

    // attach a disconnect helper to the socket instance to mark forcedClose
    socket._disconnect = () => {
      try {
        forcedClose = true;
        if (socket.readyState !== WebSocket.CLOSED && socket.readyState !== WebSocket.CLOSING) {
          socket.close(1000, 'Client disconnect');
        }
      } catch (e) {
        console.error('Error closing WebSocket:', e);
      }
    };

    return socket;
  }

  return openSocket();
}

export function sendWebSocketMessage(socket, message) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ message }));
    return true;
  } else {
    console.error('WebSocket is not connected');
    return false;
  }
}

export function disconnectWebSocket(socket) {
  if (!socket) return;
  try {
    if (typeof socket._disconnect === 'function') {
      socket._disconnect();
      return;
    }
    // Fallback normal closure code 1000
    if (socket.readyState !== WebSocket.CLOSED && socket.readyState !== WebSocket.CLOSING) {
      socket.close(1000, 'Client disconnect');
    }
  } catch (e) {
    console.error('Error closing WebSocket:', e);
  }
}