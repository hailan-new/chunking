#!/usr/bin/env python3
"""
Release preparation script for contract_splitter package.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr.strip()}")
        return False

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    # Check Python packages
    required_packages = ['setuptools', 'wheel', 'twine']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        cmd = f"pip install {' '.join(missing_packages)}"
        if not run_command(cmd, "Installing missing packages"):
            return False
    
    return True

def run_tests():
    """Run the test suite."""
    print("\n🧪 Running tests...")
    
    # Run basic tests
    if not run_command("python3 tests/test_contract_splitter.py", "Running basic tests"):
        return False
    
    # Run comprehensive tests
    if not run_command("python3 output/final_test.py", "Running comprehensive tests"):
        print("⚠️ Comprehensive tests failed, but continuing...")
    
    return True

def build_package():
    """Build the package."""
    print("\n🏗️ Building package...")
    
    # Clean previous builds
    run_command("rm -rf build/ dist/ *.egg-info/", "Cleaning previous builds")
    
    # Build source distribution
    if not run_command("python3 setup.py sdist", "Building source distribution"):
        return False
    
    # Build wheel distribution
    if not run_command("python3 setup.py bdist_wheel", "Building wheel distribution"):
        return False
    
    return True

def check_package():
    """Check the built package."""
    print("\n🔍 Checking package...")
    
    # Check with twine
    if not run_command("twine check dist/*", "Checking package with twine"):
        return False
    
    return True

def show_release_info():
    """Show release information."""
    print("\n📋 Release Information:")
    print("=" * 50)
    
    # Show package info
    try:
        with open("setup.py", "r") as f:
            content = f.read()
            for line in content.split('\n'):
                if 'version=' in line:
                    print(f"Version: {line.strip()}")
                elif 'name=' in line:
                    print(f"Package: {line.strip()}")
    except:
        pass
    
    # Show files in dist/
    print(f"\nBuilt files:")
    dist_path = Path("dist")
    if dist_path.exists():
        for file in dist_path.iterdir():
            size = file.stat().st_size / 1024  # KB
            print(f"  📦 {file.name} ({size:.1f} KB)")
    
    print(f"\n🚀 Ready for release!")
    print(f"To upload to PyPI:")
    print(f"  twine upload dist/*")
    print(f"\nTo upload to Test PyPI:")
    print(f"  twine upload --repository testpypi dist/*")

def main():
    """Main release preparation function."""
    print("🚀 Contract Splitter - Release Preparation")
    print("=" * 50)
    
    # Change to package directory
    os.chdir(Path(__file__).parent)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        return 1
    
    # Run tests
    if not run_tests():
        print("❌ Tests failed")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return 1
    
    # Build package
    if not build_package():
        print("❌ Package build failed")
        return 1
    
    # Check package
    if not check_package():
        print("❌ Package check failed")
        return 1
    
    # Show release info
    show_release_info()
    
    print("\n✅ Release preparation completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
