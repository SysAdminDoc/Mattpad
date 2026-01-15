"""UI components for Mattpad."""
from .ribbon import Ribbon, RibbonTab, RibbonGroup, RibbonButton
from .minimap import Minimap
from .line_numbers import LineNumberCanvas
from .toast import ToastManager
from .welcome import WelcomeScreen
from .sidebar import FileTreeView
from .clipboard_panel import ClipboardPanel
from .find_replace import FindReplaceBar
from .dialogs import create_dialog, DiffEngine

__all__ = [
    'Ribbon', 'RibbonTab', 'RibbonGroup', 'RibbonButton',
    'Minimap', 'LineNumberCanvas', 'ToastManager',
    'WelcomeScreen', 'FileTreeView', 'ClipboardPanel',
    'FindReplaceBar', 'create_dialog', 'DiffEngine',
]
