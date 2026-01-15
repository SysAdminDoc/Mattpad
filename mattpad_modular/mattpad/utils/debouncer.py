"""Debouncer utility for rate-limiting function calls."""
from typing import Callable, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk


class Debouncer:
    """Debounce function calls to prevent rapid repeated execution."""
    
    def __init__(self, root: 'tk.Tk', delay_ms: int = 200):
        self.root = root
        self.delay_ms = delay_ms
        self._pending: dict[str, str] = {}  # key -> after_id
    
    def debounce(self, key: str, callback: Callable, *args, **kwargs):
        """
        Schedule a callback after delay, canceling any pending call with same key.
        
        Args:
            key: Unique identifier for this debounced operation
            callback: Function to call
            *args, **kwargs: Arguments to pass to callback
        """
        # Cancel pending call if exists
        if key in self._pending:
            self.root.after_cancel(self._pending[key])
        
        # Schedule new call
        def execute():
            self._pending.pop(key, None)
            callback(*args, **kwargs)
        
        self._pending[key] = self.root.after(self.delay_ms, execute)
    
    def cancel(self, key: str):
        """Cancel a pending debounced call."""
        if key in self._pending:
            self.root.after_cancel(self._pending[key])
            del self._pending[key]
    
    def cancel_all(self):
        """Cancel all pending debounced calls."""
        for after_id in self._pending.values():
            self.root.after_cancel(after_id)
        self._pending.clear()


class Throttler:
    """Throttle function calls to limit execution frequency."""
    
    def __init__(self, root: 'tk.Tk', interval_ms: int = 100):
        self.root = root
        self.interval_ms = interval_ms
        self._last_call: dict[str, float] = {}
        self._pending: dict[str, str] = {}
    
    def throttle(self, key: str, callback: Callable, *args, **kwargs):
        """
        Execute callback at most once per interval.
        
        Args:
            key: Unique identifier for this throttled operation
            callback: Function to call
            *args, **kwargs: Arguments to pass to callback
        """
        import time
        now = time.time() * 1000  # ms
        
        if key not in self._last_call or (now - self._last_call[key]) >= self.interval_ms:
            # Execute immediately
            self._last_call[key] = now
            callback(*args, **kwargs)
        elif key not in self._pending:
            # Schedule trailing call
            remaining = self.interval_ms - (now - self._last_call[key])
            
            def execute():
                self._pending.pop(key, None)
                self._last_call[key] = time.time() * 1000
                callback(*args, **kwargs)
            
            self._pending[key] = self.root.after(int(remaining), execute)
