#!/usr/bin/env python3
"""
Mattpad Launcher - Auto-installing launcher script
Place this file alongside the 'mattpad' folder and run it.

Usage:
    python run_mattpad.py
"""

import sys
import os
import subprocess
import importlib.util

# =============================================================================
# DPI AWARENESS (must be before any GUI imports)
# =============================================================================

def enable_dpi_awareness():
    """Enable DPI awareness on Windows for crisp rendering."""
    if sys.platform == "win32":
        try:
            import ctypes
            # Windows 10 1703+ Per-Monitor DPI Awareness v2
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                # Windows 8.1+ Per-Monitor DPI Awareness
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                try:
                    # Windows Vista+ System DPI Awareness
                    import ctypes
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass

enable_dpi_awareness()

# =============================================================================
# DEPENDENCY CHECK AND INSTALL
# =============================================================================

def check_and_install_dependencies():
    """Check for required packages and install if missing."""
    packages = {
        "customtkinter": "customtkinter",
        "requests": "requests",
    }
    
    optional_packages = {
        "chardet": "chardet",
        "pyspellchecker": "spellchecker",
        "keyring": "keyring",
        "openai": "openai",
        "anthropic": "anthropic",
        "Pillow": "PIL",
    }
    
    # Windows-only packages
    if sys.platform == "win32":
        optional_packages["pywin32"] = "win32clipboard"
    
    # Check required packages
    missing_required = []
    for pkg, import_name in packages.items():
        if importlib.util.find_spec(import_name.split(".")[0]) is None:
            missing_required.append(pkg)
    
    # Check optional packages
    missing_optional = []
    for pkg, import_name in optional_packages.items():
        if importlib.util.find_spec(import_name.split(".")[0]) is None:
            missing_optional.append(pkg)
    
    # Install missing packages
    all_missing = missing_required + missing_optional
    
    if all_missing:
        print(f"Installing dependencies: {', '.join(all_missing)}...")
        for pkg in all_missing:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pkg,
                     "--quiet", "--disable-pip-version-check"],
                    stderr=subprocess.DEVNULL
                )
                print(f"  ✓ Installed {pkg}")
            except subprocess.CalledProcessError:
                if pkg in missing_required:
                    print(f"  ✗ Failed to install required package: {pkg}")
                    sys.exit(1)
                else:
                    print(f"  ⚠ Optional package not installed: {pkg}")
    
    if missing_required:
        print("Dependencies installed. Starting Mattpad...")

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    # Check dependencies first
    check_and_install_dependencies()
    
    # Add current directory to path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    # Import and run
    try:
        from mattpad import main as mattpad_main
        mattpad_main()
    except ImportError as e:
        print(f"Error importing mattpad: {e}")
        print("\nMake sure the 'mattpad' folder is in the same directory as this script.")
        print("Directory structure should be:")
        print("  YourFolder/")
        print("  ├── run_mattpad.py  (this file)")
        print("  └── mattpad/")
        print("      ├── __init__.py")
        print("      ├── app.py")
        print("      └── ...")
        sys.exit(1)


if __name__ == "__main__":
    main()
