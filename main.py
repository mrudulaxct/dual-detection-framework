"""
Dual Detection Framework for Cyber-Physical Systems
Main application entry point
"""

import asyncio
import json
from aiohttp import web
import aiohttp_cors
from pathlib import Path
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.plant import Plant
from src.controller import Controller
from src.detectors import FaultDetector, AttackDetector
from src.network import SecureNetwork
from src.database import Database
from src.simulator import SystemSimulator

class DualDetectionSystem:
    def __init__(self):
        logger.info("Initializing Dual Detection System...")
        self.db = Database()
        self.plant = Plant()
        self.controller = Controller(self.plant)
        self.fault_detector = FaultDetector(self.controller)
        self.attack_detector = AttackDetector(self.controller, self.plant)
        self.network = SecureNetwork()
        self.simulator = SystemSimulator(
            self.plant, 
            self.controller, 
            self.fault_detector, 
            self.attack_detector,
            self.network,
            self.db
        )
        self.websockets = set()
        logger.info("System initialized successfully")
        
    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websockets.add(ws)
        logger.info(f"WebSocket client connected. Total clients: {len(self.websockets)}")
        
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self.handle_command(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {e}")
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
        finally:
            self.websockets.discard(ws)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.websockets)}")
        
        return ws
    
    async def handle_command(self, data):
        """Handle commands from frontend"""
        cmd = data.get('command')
        logger.info(f"Received command: {cmd}")
        
        try:
            if cmd == 'inject_fault':
                self.simulator.inject_fault(data.get('fault_type'), data.get('magnitude'))
            elif cmd == 'inject_attack':
                self.simulator.inject_attack(data.get('attack_type'), data.get('magnitude'))
            elif cmd == 'clear_anomalies':
                self.simulator.clear_anomalies()
            elif cmd == 'set_reference':
                self.simulator.set_reference(data.get('value'))
            elif cmd == 'get_history':
                history = self.db.get_recent_data(limit=data.get('limit', 100))
                await self.broadcast({'type': 'history', 'data': history})
        except Exception as e:
            logger.error(f"Command handling error: {e}")
    
    async def broadcast(self, message):
        """Broadcast message to all connected websockets"""
        if self.websockets:
            disconnected = set()
            for ws in self.websockets:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")
                    disconnected.add(ws)
            
            # Remove disconnected clients
            self.websockets -= disconnected
    
    async def simulation_loop(self):
        """Main simulation loop"""
        logger.info("Starting simulation loop...")
        while True:
            try:
                # Run one simulation step
                results = self.simulator.step()
                
                # Broadcast results to all clients
                await self.broadcast({
                    'type': 'update',
                    'data': results
                })
                
            except Exception as e:
                logger.error(f"Simulation error: {e}")
            
            await asyncio.sleep(0.1)  # 10Hz update rate

async def init_app():
    """Initialize web application"""
    app = web.Application()
    system = DualDetectionSystem()
    
    # Setup CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*"
        )
    })
    
    # Get paths
    base_path = Path(__file__).parent
    static_path = base_path / 'static'
    
    logger.info(f"Base path: {base_path}")
    logger.info(f"Static path: {static_path}")
    
    # Ensure static directory exists
    if not static_path.exists():
        logger.error(f"Static directory not found: {static_path}")
        raise FileNotFoundError(f"Static directory not found: {static_path}")
    
    # Routes
    app.router.add_get('/ws', system.websocket_handler)
    
    # Serve static files
    app.router.add_static('/static', static_path, name='static')
    
    # Index route
    async def index(request):
        index_file = static_path / 'index.html'
        if not index_file.exists():
            logger.error(f"Index file not found: {index_file}")
            raise web.HTTPNotFound(text="index.html not found")
        return web.FileResponse(index_file)
    
    app.router.add_get('/', index)
    
    # Configure CORS
    for route in list(app.router.routes()):
        if not isinstance(route.resource, web.StaticResource):
            cors.add(route)
    
    # Start simulation loop
    app['simulation_task'] = asyncio.create_task(system.simulation_loop())
    
    logger.info("Application initialized successfully")
    return app

if __name__ == '__main__':
    print("=" * 80)
    print("🚀 DUAL DETECTION FRAMEWORK - CYBER-PHYSICAL SECURITY MONITOR")
    print("=" * 80)
    print("\n📊 Starting system...")
    print("🌐 Dashboard will be available at: http://localhost:8080")
    print("🔒 Secure communication enabled")
    print("📡 Real-time monitoring active\n")
    print("=" * 80)
    
    try:
        web.run_app(init_app(), host='0.0.0.0', port=8080, print=lambda x: None)
    except KeyboardInterrupt:
        print("\n\n⚠️  Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise