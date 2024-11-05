from typing import Dict, List, Callable, Any
import asyncio
import json
import logging
from datetime import datetime
from fastapi import WebSocket
from collections import defaultdict

logger = logging.getLogger(__name__)

class EventService:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections[client_id].append(websocket)
        logger.info(f"Client {client_id} connected")
        
    def disconnect(self, websocket: WebSocket, client_id: str):
        """Disconnect a WebSocket client."""
        self.active_connections[client_id].remove(websocket)
        if not self.active_connections[client_id]:
            del self.active_connections[client_id]
        logger.info(f"Client {client_id} disconnected")
        
    async def broadcast(self, event_type: str, data: Dict):
        """Broadcast event to all connected clients."""
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Convert message to JSON
        json_message = json.dumps(message)
        
        # Send to all connected clients
        for client_connections in self.active_connections.values():
            for connection in client_connections:
                try:
                    await connection.send_text(json_message)
                except Exception as e:
                    logger.error(f"Error sending message: {str(e)}")
                    
    async def send_to_client(self, client_id: str, event_type: str, data: Dict):
        """Send event to a specific client."""
        if client_id not in self.active_connections:
            logger.warning(f"Client {client_id} not found")
            return
            
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        json_message = json.dumps(message)
        
        for connection in self.active_connections[client_id]:
            try:
                await connection.send_text(json_message)
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {str(e)}")
                
    def register_handler(self, event_type: str, handler: Callable):
        """Register an event handler."""
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")
        
    async def handle_event(self, event_type: str, data: Dict):
        """Handle an incoming event."""
        logger.info(f"Handling event: {event_type}")
        
        # Execute all handlers for this event type
        for handler in self.event_handlers[event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in event handler: {str(e)}")
                
        # Broadcast event to relevant clients
        await self.broadcast(event_type, data)
        
    async def start_heartbeat(self, interval: int = 30):
        """Start heartbeat to keep connections alive."""
        while True:
            await asyncio.sleep(interval)
            heartbeat_message = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            json_message = json.dumps(heartbeat_message)
            
            for client_connections in self.active_connections.values():
                for connection in client_connections:
                    try:
                        await connection.send_text(json_message)
                    except Exception as e:
                        logger.error(f"Error sending heartbeat: {str(e)}")
                        
    def get_connected_clients(self) -> List[str]:
        """Get list of connected client IDs."""
        return list(self.active_connections.keys())
        
    def get_client_count(self) -> int:
        """Get total number of connected clients."""
        return sum(len(connections) for connections in self.active_connections.values())
        
    async def close_all_connections(self):
        """Close all active WebSocket connections."""
        for client_connections in self.active_connections.values():
            for connection in client_connections:
                try:
                    await connection.close()
                except Exception as e:
                    logger.error(f"Error closing connection: {str(e)}")
        
        self.active_connections.clear()
        logger.info("All connections closed") 