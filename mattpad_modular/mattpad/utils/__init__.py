"""Utility modules for Mattpad."""
from .themes import Theme, THEMES, get_theme, THEME
from .dispatcher import ThreadSafeDispatcher, get_dispatcher, set_dispatcher
from .debouncer import Debouncer
from .file_utils import (
    FILE_EXTENSIONS, get_file_icon, detect_line_ending, 
    detect_encoding, normalize_line_endings
)

__all__ = [
    'Theme', 'THEMES', 'get_theme', 'THEME',
    'ThreadSafeDispatcher', 'get_dispatcher', 'set_dispatcher',
    'Debouncer',
    'FILE_EXTENSIONS', 'get_file_icon', 'detect_line_ending',
    'detect_encoding', 'normalize_line_endings',
]
