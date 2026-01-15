"""Welcome screen for Mattpad."""
import os
import customtkinter as ctk
from typing import List, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.settings import EditorSettings

from ..utils.themes import THEME
from ..utils.file_utils import get_file_icon

VERSION = "6.0"


class WelcomeScreen(ctk.CTkFrame):
    """Welcome screen shown on startup."""
    
    def __init__(self, master, settings: 'EditorSettings',
                 on_new: Callable, on_open: Callable, on_recent: Callable,
                 recent_files: List[str], **kwargs):
        super().__init__(master, fg_color=THEME.bg_darkest, **kwargs)
        self.settings = settings
        self.on_new = on_new
        self.on_open = on_open
        self.on_recent = on_recent
        self._create(recent_files)
    
    def _create(self, recent_files: List[str]):
        """Create the welcome screen UI."""
        s = self.settings.ui_scale
        
        # Center container
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.45, anchor="center")
        
        # Logo and title
        ctk.CTkLabel(
            center, text="📝",
            font=ctk.CTkFont(size=int(64*s))
        ).pack(pady=(0, int(10*s)))
        
        ctk.CTkLabel(
            center, text="Mattpad",
            font=ctk.CTkFont(size=int(36*s), weight="bold"),
            text_color=THEME.accent_primary
        ).pack()
        
        ctk.CTkLabel(
            center, text=f"v{VERSION} - Professional Text Editor",
            font=ctk.CTkFont(size=int(12*s)),
            text_color=THEME.text_secondary
        ).pack(pady=(0, int(30*s)))
        
        # Action buttons
        btn_frame = ctk.CTkFrame(center, fg_color="transparent")
        btn_frame.pack(pady=int(20*s))
        
        btn_cfg = {
            "width": int(180*s),
            "height": int(40*s),
            "corner_radius": int(8*s),
            "font": ctk.CTkFont(size=int(12*s))
        }
        
        ctk.CTkButton(
            btn_frame, text="📄  New File",
            fg_color=THEME.accent_primary,
            command=self.on_new, **btn_cfg
        ).pack(pady=int(5*s))
        
        ctk.CTkButton(
            btn_frame, text="📂  Open File",
            fg_color=THEME.bg_medium,
            hover_color=THEME.bg_hover,
            command=self.on_open, **btn_cfg
        ).pack(pady=int(5*s))
        
        # Recent files
        if recent_files:
            ctk.CTkLabel(
                center, text="Recent Files",
                font=ctk.CTkFont(size=int(14*s), weight="bold"),
                text_color=THEME.text_secondary
            ).pack(pady=(int(30*s), int(10*s)))
            
            recent_frame = ctk.CTkFrame(
                center, fg_color=THEME.bg_dark,
                corner_radius=int(8*s)
            )
            recent_frame.pack()
            
            for filepath in recent_files[:8]:
                if os.path.exists(filepath):
                    icon = get_file_icon(filepath)
                    name = os.path.basename(filepath)
                    folder = os.path.dirname(filepath)
                    
                    # Truncate folder path
                    if len(folder) > 40:
                        folder = "..." + folder[-37:]
                    
                    btn = ctk.CTkButton(
                        recent_frame,
                        text=f"{icon}  {name}",
                        fg_color="transparent",
                        hover_color=THEME.bg_hover,
                        anchor="w",
                        font=ctk.CTkFont(size=int(11*s)),
                        height=int(32*s),
                        command=lambda fp=filepath: self.on_recent(fp)
                    )
                    btn.pack(fill="x", padx=int(4*s), pady=int(2*s))
        
        # Keyboard shortcuts hint
        shortcuts_frame = ctk.CTkFrame(center, fg_color="transparent")
        shortcuts_frame.pack(pady=(int(30*s), 0))
        
        shortcuts = [
            ("Ctrl+N", "New File"),
            ("Ctrl+O", "Open File"),
            ("Ctrl+Shift+P", "Command Palette"),
        ]
        
        for key, desc in shortcuts:
            row = ctk.CTkFrame(shortcuts_frame, fg_color="transparent")
            row.pack(fill="x", pady=int(2*s))
            
            ctk.CTkLabel(
                row, text=key,
                font=ctk.CTkFont(size=int(10*s)),
                text_color=THEME.text_muted,
                width=int(100*s), anchor="e"
            ).pack(side="left")
            
            ctk.CTkLabel(
                row, text=desc,
                font=ctk.CTkFont(size=int(10*s)),
                text_color=THEME.text_secondary,
                anchor="w"
            ).pack(side="left", padx=int(10*s))
