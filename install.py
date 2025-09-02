#!/usr/bin/env python3
"""
Smart installer for contract_splitter with WPS native support
Automatically detects platform and installs appropriate dependencies
"""

import os
import sys
import platform
import subprocess
import json
from pathlib import Path


def load_config():
    """Load installation configuration"""
    config_path = Path(__file__).parent / "install_config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def detect_platform():
    """Detect current platform"""
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    elif system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Python 3.8+ is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def run_command(cmd, description="", check=True):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} successful")
            return True
        else:
            if check:
                print(f"❌ {description} failed: {result.stderr}")
                return False
            else:
                print(f"⚠️  {description} failed (non-critical): {result.stderr}")
                return False
    except Exception as e:
        if check:
            print(f"❌ {description} error: {e}")
            return False
        else:
            print(f"⚠️  {description} error (non-critical): {e}")
            return False


def install_core_dependencies(config):
    """Install core Python dependencies"""
    deps = " ".join(config["core_dependencies"])
    return run_command(f"pip install {deps}", "Installing core dependencies")


def install_platform_dependencies(config, platform_name, feature="wps_support"):
    """Install platform-specific dependencies"""
    platform_config = config["platform_dependencies"].get(platform_name, {})
    
    if feature in platform_config:
        deps = " ".join(platform_config[feature])
        return run_command(f"pip install {deps}", f"Installing {feature} for {platform_name}", check=False)
    
    return True


def install_optional_features(config, features):
    """Install optional features"""
    for feature in features:
        if feature in config["optional_features"]:
            deps = " ".join(config["optional_features"][feature])
            run_command(f"pip install {deps}", f"Installing {feature} features", check=False)


def check_system_dependencies(config, platform_name):
    """Check and suggest system dependencies"""
    platform_config = config["platform_dependencies"].get(platform_name, {})
    requirements = platform_config.get("system_requirements", [])
    
    if requirements:
        print(f"\n📋 System dependencies for {platform_name}:")
        for req in requirements:
            print(f"  - {req}")
        
        print("\n💡 To install system dependencies automatically, run:")
        script = platform_config.get("installation_script")
        if script:
            if platform_name == "windows":
                print(f"  {script}")
            else:
                print(f"  bash {script}")


def verify_installation(config):
    """Verify the installation"""
    print("\n🔍 Verifying installation...")
    
    # Basic verification
    if run_command(config["verification_commands"]["basic"], "Basic functionality test", check=False):
        print("✅ Basic installation verified")
    
    # WPS support verification
    if run_command(config["verification_commands"]["wps_support"], "WPS support test", check=False):
        print("✅ WPS support verified")
    
    # Full test
    if run_command(config["verification_commands"]["full_test"], "Full functionality test", check=False):
        print("✅ Full functionality verified")


def show_wps_methods(config):
    """Show available WPS processing methods"""
    print("\n📄 Available WPS Processing Methods:")
    methods = config["wps_processing_methods"]["method_descriptions"]
    
    for method_id, method_info in methods.items():
        print(f"\n🔧 {method_info['name']}:")
        print(f"   Quality: {method_info['quality']}")
        print(f"   Platforms: {', '.join(method_info['platforms'])}")
        print(f"   Requirements: {', '.join(method_info['requirements'])}")
        print(f"   Description: {method_info['description']}")


def main():
    """Main installation function"""
    print("🚀 Contract Splitter Smart Installer")
    print("=====================================")
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return 1
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Detect platform
    platform_name = detect_platform()
    print(f"🖥️  Platform detected: {platform_name}")
    
    if platform_name == "unknown":
        print("⚠️  Unknown platform, using generic installation")
        platform_name = "linux"  # Use Linux as fallback
    
    # Install core dependencies
    print(f"\n📦 Installing Contract Splitter v{config['package_info']['version']}")
    if not install_core_dependencies(config):
        print("❌ Core installation failed")
        return 1
    
    # Install platform-specific dependencies
    print(f"\n🔧 Installing platform-specific dependencies for {platform_name}")
    
    if platform_name == "windows":
        install_platform_dependencies(config, platform_name, "wps_native")
    elif platform_name == "darwin":
        install_platform_dependencies(config, platform_name, "wps_support")
    elif platform_name == "linux":
        install_platform_dependencies(config, platform_name, "wps_native")
    
    # Install enhanced features
    print(f"\n✨ Installing enhanced features")
    install_optional_features(config, ["enhanced", "wps_api"])
    
    # Check system dependencies
    check_system_dependencies(config, platform_name)
    
    # Verify installation
    verify_installation(config)
    
    # Show WPS methods
    show_wps_methods(config)
    
    print(f"\n🎉 Installation completed!")
    print(f"\n📚 Next steps:")
    print(f"  1. Install system dependencies (see above)")
    print(f"  2. Test with: python -c \"from contract_splitter import split_document; print('Ready!')\"")
    print(f"  3. For WPS API support, get API key from WPS Open Platform")
    print(f"  4. Read documentation for usage examples")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
