"""
Setup Verification Script
Run this to check if everything is configured correctly
"""

import sys
from pathlib import Path
import importlib.util

def check_file(filepath, description):
    """Check if a file exists"""
    if filepath.exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ MISSING {description}: {filepath}")
        return False

def check_module(module_name):
    """Check if a Python module can be imported"""
    spec = importlib.util.find_spec(module_name)
    if spec is not None:
        print(f"✅ Module {module_name} installed")
        return True
    else:
        print(f"❌ Module {module_name} NOT installed")
        return False

def test_backend():
    """Test if backend can run simulation"""
    print("\n🧪 Testing Backend Simulation...")
    try:
        sys.path.append(str(Path(__file__).parent / 'src'))
        from src.plant import Plant
        from src.controller import Controller
        from src.detectors import FaultDetector, AttackDetector
        from src.network import SecureNetwork
        from src.database import Database
        from src.simulator import SystemSimulator
        
        # Initialize
        db = Database()
        plant = Plant()
        controller = Controller(plant)
        fault_detector = FaultDetector(controller)
        attack_detector = AttackDetector(controller, plant)
        network = SecureNetwork()
        simulator = SystemSimulator(plant, controller, fault_detector, attack_detector, network, db)
        
        print("   ✅ All components initialized")
        
        # Run 3 steps
        for i in range(3):
            results = simulator.step()
            print(f"   Step {i+1}: Time={results['time']:.2f}, Output={results['output']:.3f}")
        
        print("   ✅ Simulation running successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 80)
    print("🔍 DUAL DETECTION FRAMEWORK - SETUP VERIFICATION")
    print("=" * 80)
    print()
    
    base_path = Path(__file__).parent
    all_good = True
    
    # Check Python version
    print("📌 Python Version Check:")
    py_version = sys.version_info
    if py_version.major == 3 and py_version.minor >= 7:
        print(f"✅ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        print(f"❌ Python version too old: {py_version.major}.{py_version.minor}")
        all_good = False
    print()
    
    # Check required Python packages
    print("📦 Required Packages:")
    required_packages = ['numpy', 'scipy', 'aiohttp', 'aiohttp_cors', 'cryptography']
    for package in required_packages:
        if not check_module(package):
            all_good = False
    print()
    
    # Check directory structure
    print("📁 Directory Structure:")
    directories = [
        (base_path / 'src', 'Source code directory'),
        (base_path / 'static', 'Static files directory'),
        (base_path / 'data', 'Data directory')
    ]
    
    for dir_path, description in directories:
        if not check_file(dir_path, description):
            all_good = False
            if dir_path.name == 'data':
                print(f"   ℹ️  Creating data directory...")
                dir_path.mkdir(exist_ok=True)
    print()
    
    # Check Python source files
    print("🐍 Python Source Files:")
    source_files = [
        (base_path / 'main.py', 'Main application'),
        (base_path / 'src' / '__init__.py', 'Package initializer'),
        (base_path / 'src' / 'plant.py', 'Plant model'),
        (base_path / 'src' / 'controller.py', 'Controller'),
        (base_path / 'src' / 'detectors.py', 'Detectors'),
        (base_path / 'src' / 'network.py', 'Network layer'),
        (base_path / 'src' / 'database.py', 'Database'),
        (base_path / 'src' / 'simulator.py', 'Simulator')
    ]
    
    for filepath, description in source_files:
        if not check_file(filepath, description):
            all_good = False
    print()
    
    # Check frontend files
    print("🌐 Frontend Files:")
    frontend_files = [
        (base_path / 'static' / 'index.html', 'HTML file'),
        (base_path / 'static' / 'style.css', 'CSS file'),
        (base_path / 'static' / 'app.js', 'JavaScript file')
    ]
    
    for filepath, description in frontend_files:
        if not check_file(filepath, description):
            all_good = False
    print()
    
    # Check file sizes
    print("📏 File Size Check:")
    critical_files = [
        (base_path / 'static' / 'style.css', 'CSS file', 10000),
        (base_path / 'static' / 'app.js', 'JavaScript file', 5000),
    ]
    
    for filepath, description, min_size in critical_files:
        if filepath.exists():
            size = filepath.stat().st_size
            if size >= min_size:
                print(f"✅ {description}: {size} bytes")
            else:
                print(f"⚠️  {description}: {size} bytes (expected at least {min_size})")
                all_good = False
    print()
    
    # Test backend simulation
    if all_good:
        backend_ok = test_backend()
        if not backend_ok:
            all_good = False
    
    # Final verdict
    print("=" * 80)
    if all_good:
        print("✅ ALL CHECKS PASSED! BACKEND WORKS!")
        print("\n🚀 You can now run: python main.py")
        print("📊 Dashboard will be at: http://localhost:8080")
        print("\n💡 If dashboard still shows zeros:")
        print("   1. Check browser console (F12)")
        print("   2. Look for '✅ WebSocket Connected'")
        print("   3. Should see '📊 Updating dashboard' messages")
    else:
        print("❌ SETUP HAS ISSUES!")
        print("\n📝 Fix the issues above, then:")
        print("   1. Install missing packages: pip install numpy scipy aiohttp aiohttp-cors cryptography")
        print("   2. Make sure all files are created")
        print("   3. Run this test again: python test_setup.py")
    print("=" * 80)
    
    return 0 if all_good else 1

if __name__ == '__main__':
    sys.exit(main())
    