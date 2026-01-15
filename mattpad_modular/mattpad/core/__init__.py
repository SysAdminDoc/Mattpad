"""Core modules for Mattpad."""
from .settings import EditorSettings
from .tabs import TabData
from .managers import (
    CacheManager, BackupManager, SessionManager, HotExitManager,
    ClosedTabsManager, ClipboardItem, SecretStorage
)

__all__ = [
    'EditorSettings', 'TabData',
    'CacheManager', 'BackupManager', 'SessionManager', 'HotExitManager',
    'ClosedTabsManager', 'ClipboardItem', 'SecretStorage',
]
