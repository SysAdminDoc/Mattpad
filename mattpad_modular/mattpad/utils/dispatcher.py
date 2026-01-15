"""Thread-safe dispatcher for UI updates."""
import queue
import threading
from typing import Callable, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk

# Global dispatcher instance
_dispatcher: Optional['ThreadSafeDispatcher'] = None


class ThreadSafeDispatcher:
    """Thread-safe dispatcher for scheduling UI updates from background threads."""
    
    def __init__(self, root: 'tk.Tk'):
        self.root = root
        self._queue: queue.Queue = queue.Queue()
        self._poll()
    
    def _poll(self):
        """Poll the queue for pending callbacks."""
        try:
            while True:
                callback, args, kwargs = self._queue.get_nowait()
                try:
                    callback(*args, **kwargs)
                except Exception:
                    pass
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self._poll)
    
    def dispatch(self, callback: Callable, *args, **kwargs):
        """Schedule a callback to run on the main thread."""
        self._queue.put((callback, args, kwargs))
    
    def call_soon(self, callback: Callable, *args, **kwargs):
        """Alias for dispatch."""
        self.dispatch(callback, *args, **kwargs)


def get_dispatcher() -> Optional[ThreadSafeDispatcher]:
    """Get the global dispatcher instance."""
    return _dispatcher


def set_dispatcher(dispatcher: ThreadSafeDispatcher):
    """Set the global dispatcher instance."""
    global _dispatcher
    _dispatcher = dispatcher
