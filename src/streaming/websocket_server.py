"""WebSocket server for real-time updates."""

import asyncio
import json
from typing import Dict, Set

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    websockets = None
    WebSocketServerProtocol = None

from src.config import settings
from src.utils.logger import logger


class WebSocketServer:
    """WebSocket server for broadcasting real-time updates."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        """
        Initialize WebSocket server.

        Args:
            host: Host to bind to
            port: Port to listen on
        """
        if websockets is None:
            raise ImportError("websockets not installed. Install with: pip install websockets")

        self.host = host
        self.port = port

        # Active connections per meeting
        self.connections: Dict[str, Set[WebSocketServerProtocol]] = {}

        logger.info(f"WebSocket server initialized on {host}:{port}")

    async def register_client(self, websocket: WebSocketServerProtocol, meeting_id: str):
        """
        Register a client connection.

        Args:
            websocket: WebSocket connection
            meeting_id: Meeting ID to subscribe to
        """
        if meeting_id not in self.connections:
            self.connections[meeting_id] = set()

        self.connections[meeting_id].add(websocket)
        logger.info(f"Client connected to meeting {meeting_id} (total: {len(self.connections[meeting_id])})")

    async def unregister_client(self, websocket: WebSocketServerProtocol, meeting_id: str):
        """
        Unregister a client connection.

        Args:
            websocket: WebSocket connection
            meeting_id: Meeting ID
        """
        if meeting_id in self.connections:
            self.connections[meeting_id].discard(websocket)
            logger.info(f"Client disconnected from meeting {meeting_id}")

            # Clean up empty meeting rooms
            if not self.connections[meeting_id]:
                del self.connections[meeting_id]

    async def broadcast_to_meeting(self, meeting_id: str, message: Dict):
        """
        Broadcast message to all clients watching a meeting.

        Args:
            meeting_id: Meeting ID
            message: Message dictionary to broadcast
        """
        if meeting_id not in self.connections:
            logger.warning(f"No clients connected to meeting {meeting_id}")
            return

        if not self.connections[meeting_id]:
            return

        # Convert message to JSON
        message_json = json.dumps(message)

        # Broadcast to all connected clients
        disconnected = set()

        for websocket in self.connections[meeting_id]:
            try:
                await websocket.send(message_json)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(websocket)

        # Remove disconnected clients
        for websocket in disconnected:
            await self.unregister_client(websocket, meeting_id)

        logger.debug(f"Broadcasted to {len(self.connections[meeting_id])} clients")

    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """
        Handle incoming WebSocket connection.

        Args:
            websocket: WebSocket connection
            path: Connection path (e.g., /meeting/meeting_001)
        """
        # Extract meeting ID from path
        parts = path.strip("/").split("/")
        if len(parts) < 2 or parts[0] != "meeting":
            logger.warning(f"Invalid WebSocket path: {path}")
            await websocket.close()
            return

        meeting_id = parts[1]

        # Register client
        await self.register_client(websocket, meeting_id)

        try:
            # Send welcome message
            await websocket.send(
                json.dumps(
                    {
                        "type": "connected",
                        "meeting_id": meeting_id,
                        "message": "Connected to real-time updates",
                    }
                )
            )

            # Keep connection alive and handle incoming messages
            async for message in websocket:
                # Handle heartbeat or control messages
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON message: {message}")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client connection closed for meeting {meeting_id}")
        finally:
            await self.unregister_client(websocket, meeting_id)

    async def start(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on ws://{self.host}:{self.port}")

        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info("WebSocket server started")
            await asyncio.Future()  # Run forever

    def get_stats(self) -> Dict:
        """
        Get server statistics.

        Returns:
            Dictionary with connection stats
        """
        return {
            "active_meetings": len(self.connections),
            "total_connections": sum(len(conns) for conns in self.connections.values()),
            "meetings": {
                meeting_id: len(conns) for meeting_id, conns in self.connections.items()
            },
        }
