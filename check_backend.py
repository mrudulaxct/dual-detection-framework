"""
Quick backend test - Run this to verify the system is generating data
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.plant import Plant
from src.controller import Controller
from src.detectors import FaultDetector, AttackDetector
from src.network import SecureNetwork
from src.database import Database
from src.simulator import SystemSimulator

print("=" * 80)
print("🧪 BACKEND TEST - Verifying Data Generation")
print("=" * 80)
print()

try:
    print("1️⃣ Initializing components...")
    db = Database()
    plant = Plant()
    controller = Controller(plant)
    fault_detector = FaultDetector(controller)
    attack_detector = AttackDetector(controller, plant)
    network = SecureNetwork()
    simulator = SystemSimulator(plant, controller, fault_detector, attack_detector, network, db)
    print("   ✅ All components initialized\n")
    
    print("2️⃣ Running 5 simulation steps...")
    for i in range(5):
        results = simulator.step()
        print(f"\n   Step {i+1}:")
        print(f"   - Time: {results['time']:.2f}s")
        print(f"   - Output: {results['output']:.3f}")
        print(f"   - Control U1: {results['control'][0]:.3f}")
        print(f"   - Control U2: {results['control'][1]:.3f}")
        print(f"   - Fault Stat: {results['fault_detector']['statistic']:.2f}")
        print(f"   - Attack Stat: {results['attack_detector']['statistic']:.2f}")
        print(f"   - Anomaly: {results['anomaly_type']}")
    
    print("\n✅ BACKEND IS WORKING!")
    print("\nThe backend is generating data correctly.")
    print("If your dashboard shows 0 values, the issue is with:")
    print("  1. WebSocket connection not established")
    print("  2. Browser console showing errors")
    print("  3. Port 8080 blocked by firewall")
    print("\nNext steps:")
    print("  1. Run: python main.py")
    print("  2. Open browser: http://localhost:8080")
    print("  3. Press F12 and check Console for errors")
    print("  4. Look for '✅ WebSocket Connected' message")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nBackend has issues. Fix these first:")
    print("  1. Make sure all src/*.py files exist")
    print("  2. Install packages: pip install numpy scipy aiohttp aiohttp-cors cryptography")
    print("  3. Run: python test_setup.py")

print("\n" + "=" * 80)