#!/usr/bin/env python3
"""Internal launcher for Mattpad - run from inside the mattpad folder."""
import sys
import os

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mattpad.app import main

if __name__ == "__main__":
    main()
