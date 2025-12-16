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
    
    # Check file sizes (to ensure they're not empty)
    print("📏 File Size Check:")
    critical_files = [
        (base_path / 'static' / 'style.css', 'CSS file', 10000),  # Should be at least 10KB
        (base_path / 'static' / 'app.js', 'JavaScript file', 5000),  # Should be at least 5KB
    ]
    
    for filepath, description, min_size in critical_files:
        if filepath.exists():
            size = filepath.stat().st_size
            if size >= min_size:
                print(f"✅ {description}: {size} bytes")
            else:
                print(f"⚠️  {description}: {size} bytes (expected at least {min_size})")
                print(f"   File might be incomplete or corrupted")
                all_good = False
        else:
            print(f"❌ {description} not found")
            all_good = False
    print()
    
    # Final verdict
    print("=" * 80)
    if all_good:
        print("✅ ALL CHECKS PASSED!")
        print("\n🚀 You can now run: python main.py")
        print("📊 Dashboard will be at: http://localhost:8080")
    else:
        print("❌ SETUP INCOMPLETE!")
        print("\n📝 Fix the issues above, then:")
        print("   1. Make sure all files are created")
        print("   2. Install missing packages: pip install numpy scipy aiohttp aiohttp-cors cryptography")
        print("   3. Run this test again: python test_setup.py")
    print("=" * 80)
    
    return 0 if all_good else 1

if __name__ == '__main__':
    sys.exit(main())