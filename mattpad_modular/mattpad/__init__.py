"""
Mattpad v6.0 - Professional Text Editor
A modular, feature-rich text editor built with Python and CustomTkinter.
"""

__version__ = "6.0"
__author__ = "Matt"
__app_name__ = "Mattpad"

from .app import Mattpad, main

__all__ = ['Mattpad', 'main', '__version__']
