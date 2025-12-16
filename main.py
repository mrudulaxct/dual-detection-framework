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
        
    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websockets.add(ws)
        
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    await self.handle_command(data)
        finally:
            self.websockets.discard(ws)
        
        return ws
    
    async def handle_command(self, data):
        """Handle commands from frontend"""
        cmd = data.get('command')
        
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
    
    async def broadcast(self, message):
        """Broadcast message to all connected websockets"""
        if self.websockets:
            await asyncio.gather(
                *[ws.send_json(message) for ws in self.websockets],
                return_exceptions=True
            )
    
    async def simulation_loop(self):
        """Main simulation loop"""
        while True:
            # Run one simulation step
            results = self.simulator.step()
            
            # Broadcast results to all clients
            await self.broadcast({
                'type': 'update',
                'data': results
            })
            
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
    
    # Routes
    app.router.add_get('/ws', system.websocket_handler)
    app.router.add_static('/static', Path(__file__).parent / 'static')
    
    async def index(request):
        return web.FileResponse(Path(__file__).parent / 'static' / 'index.html')
    
    app.router.add_get('/', index)
    
    # Configure CORS
    for route in list(app.router.routes()):
        cors.add(route)
    
    # Start simulation loop
    app['simulation_task'] = asyncio.create_task(system.simulation_loop())
    
    return app

if __name__ == '__main__':
    print("🚀 Starting Dual Detection Framework System...")
    print("📊 Dashboard available at: http://localhost:8080")
    web.run_app(init_app(), host='0.0.0.0', port=8080)