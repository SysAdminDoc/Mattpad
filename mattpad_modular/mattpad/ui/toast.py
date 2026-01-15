"""Toast notification system for Mattpad."""
import customtkinter as ctk
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.settings import EditorSettings

from ..utils.themes import THEME


class ToastManager:
    """Manages toast notifications."""
    
    ICONS = {
        "success": "✓",
        "error": "✕",
        "warning": "⚠",
        "info": "ℹ",
    }
    
    COLORS = {
        "success": "#22c55e",
        "error": "#ef4444",
        "warning": "#f59e0b",
        "info": "#3b82f6",
    }
    
    def __init__(self, master, settings: 'EditorSettings'):
        self.master = master
        self.settings = settings
        self.current_toast: Optional[ctk.CTkFrame] = None
        self._hide_job = None
    
    def show(self, message: str, toast_type: str = "info", duration: int = 3000):
        """Show a toast notification."""
        # Hide existing toast
        self.hide()
        
        s = self.settings.ui_scale
        icon = self.ICONS.get(toast_type, "ℹ")
        color = self.COLORS.get(toast_type, "#3b82f6")
        
        # Create toast frame
        self.current_toast = ctk.CTkFrame(
            self.master,
            fg_color=THEME.bg_medium,
            corner_radius=int(8*s),
            border_width=int(2*s),
            border_color=color
        )
        
        # Icon
        ctk.CTkLabel(
            self.current_toast, text=icon,
            font=ctk.CTkFont(size=int(16*s)),
            text_color=color,
            width=int(30*s)
        ).pack(side="left", padx=(int(12*s), int(4*s)))
        
        # Message
        ctk.CTkLabel(
            self.current_toast, text=message,
            font=ctk.CTkFont(size=int(12*s)),
            text_color=THEME.text_primary
        ).pack(side="left", padx=(0, int(12*s)), pady=int(10*s))
        
        # Close button
        close_btn = ctk.CTkButton(
            self.current_toast, text="×",
            width=int(24*s), height=int(24*s),
            fg_color="transparent",
            hover_color=THEME.bg_hover,
            text_color=THEME.text_muted,
            font=ctk.CTkFont(size=int(14*s)),
            command=self.hide
        )
        close_btn.pack(side="right", padx=int(4*s))
        
        # Position at bottom center
        self.current_toast.place(
            relx=0.5, rely=0.95, anchor="s"
        )
        
        # Auto-hide after duration
        if duration > 0:
            self._hide_job = self.master.after(duration, self.hide)
    
    def hide(self):
        """Hide the current toast."""
        if self._hide_job:
            self.master.after_cancel(self._hide_job)
            self._hide_job = None
        
        if self.current_toast:
            self.current_toast.destroy()
            self.current_toast = None
    
    def success(self, message: str, duration: int = 3000):
        """Show a success toast."""
        self.show(message, "success", duration)
    
    def error(self, message: str, duration: int = 5000):
        """Show an error toast."""
        self.show(message, "error", duration)
    
    def warning(self, message: str, duration: int = 4000):
        """Show a warning toast."""
        self.show(message, "warning", duration)
    
    def info(self, message: str, duration: int = 3000):
        """Show an info toast."""
        self.show(message, "info", duration)
