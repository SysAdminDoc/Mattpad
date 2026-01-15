"""Feature modules for Mattpad."""
from .syntax import SyntaxHighlighter
from .spellcheck import SpellCheckManager
from .ai import AIManager
from .cloud import CloudSyncManager
from .snippets import SnippetsManager, MacroManager, Snippet, Macro
from .clipboard import SystemClipboardManager

__all__ = [
    'SyntaxHighlighter',
    'SpellCheckManager',
    'AIManager',
    'CloudSyncManager',
    'SnippetsManager', 'MacroManager', 'Snippet', 'Macro',
    'SystemClipboardManager',
]
