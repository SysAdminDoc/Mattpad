"""Clipboard panel for Mattpad."""
import customtkinter as ctk
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.settings import EditorSettings
    from ..features.clipboard import SystemClipboardManager

from ..utils.themes import THEME


class ClipboardPanel(ctk.CTkFrame):
    """Clipboard history panel."""
    
    def __init__(self, master, clipboard_manager: 'SystemClipboardManager',
                 on_paste: Callable, settings: 'EditorSettings', **kwargs):
        super().__init__(master, fg_color=THEME.bg_dark, corner_radius=0, **kwargs)
        self.clipboard_manager = clipboard_manager
        self.on_paste = on_paste
        self.settings = settings
        self._create()
    
    def _create(self):
        """Create the clipboard panel UI."""
        s = self.settings.ui_scale
        
        # Header
        header = ctk.CTkFrame(self, fg_color=THEME.ribbon_group_bg, height=int(36*s), corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header, text="  CLIPBOARD",
            font=ctk.CTkFont(size=int(11*s), weight="bold"),
            text_color=THEME.text_secondary
        ).pack(side="left", padx=int(4*s))
        
        # Clear button
        ctk.CTkButton(
            header, text="🗑", width=int(28*s), height=int(24*s),
            fg_color="transparent", hover_color=THEME.bg_hover,
            text_color=THEME.text_muted,
            command=self._clear_history
        ).pack(side="right", padx=int(4*s))
        
        # Refresh button
        ctk.CTkButton(
            header, text="↻", width=int(28*s), height=int(24*s),
            fg_color="transparent", hover_color=THEME.bg_hover,
            text_color=THEME.text_muted,
            command=self.refresh
        ).pack(side="right")
        
        # Scrollable frame for clipboard items
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color=THEME.bg_dark,
            scrollbar_button_color=THEME.scrollbar_thumb,
            scrollbar_button_hover_color=THEME.scrollbar_thumb_hover
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=int(4*s), pady=int(4*s))
        
        self.refresh()
    
    def refresh(self):
        """Refresh the clipboard display."""
        # Clear existing items
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        s = self.settings.ui_scale
        items = self.clipboard_manager.get_all()
        
        if not items:
            ctk.CTkLabel(
                self.scroll_frame,
                text="No clipboard history",
                text_color=THEME.text_muted,
                font=ctk.CTkFont(size=int(11*s))
            ).pack(pady=int(20*s))
            return
        
        for i, item in enumerate(items):
            self._create_item(i, item)
    
    def _create_item(self, index: int, item):
        """Create a clipboard item widget."""
        s = self.settings.ui_scale
        
        # Truncate text for display
        text = item.text[:100].replace('\n', ' ')
        if len(item.text) > 100:
            text += "..."
        
        frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=THEME.bg_medium,
            corner_radius=int(4*s)
        )
        frame.pack(fill="x", pady=int(2*s))
        
        # Pin indicator
        pin_text = "📌" if item.pinned else ""
        if pin_text:
            ctk.CTkLabel(
                frame, text=pin_text,
                font=ctk.CTkFont(size=int(10*s)),
                width=int(20*s)
            ).pack(side="left", padx=int(2*s))
        
        # Text button (clickable to paste)
        btn = ctk.CTkButton(
            frame, text=text,
            fg_color="transparent",
            hover_color=THEME.bg_hover,
            anchor="w",
            font=ctk.CTkFont(size=int(10*s)),
            height=int(28*s),
            command=lambda t=item.text: self.on_paste(t)
        )
        btn.pack(side="left", fill="x", expand=True, padx=int(4*s))
        
        # Action buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        # Pin/unpin button
        ctk.CTkButton(
            btn_frame, text="📌" if not item.pinned else "📍",
            width=int(24*s), height=int(24*s),
            fg_color="transparent",
            hover_color=THEME.bg_hover,
            text_color=THEME.text_muted,
            font=ctk.CTkFont(size=int(10*s)),
            command=lambda i=index: self._toggle_pin(i)
        ).pack(side="left")
        
        # Delete button
        ctk.CTkButton(
            btn_frame, text="×",
            width=int(24*s), height=int(24*s),
            fg_color="transparent",
            hover_color=THEME.tab_close_hover,
            text_color=THEME.text_muted,
            font=ctk.CTkFont(size=int(12*s)),
            command=lambda i=index: self._delete_item(i)
        ).pack(side="left")
    
    def _toggle_pin(self, index: int):
        """Toggle pin status of an item."""
        self.clipboard_manager.pin(index)
        self.refresh()
    
    def _delete_item(self, index: int):
        """Delete a clipboard item."""
        self.clipboard_manager.delete(index)
        self.refresh()
    
    def _clear_history(self):
        """Clear clipboard history (keep pinned)."""
        self.clipboard_manager.clear(keep_pinned=True)
        self.refresh()
