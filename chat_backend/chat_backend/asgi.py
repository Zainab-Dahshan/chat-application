"""
ASGI config for chat_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_backend.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # Add WebSocket protocol routing here
    "websocket": URLRouter([
        # WebSocket routes will be added here
    ]),
})
