"""Minimap component for Mattpad."""
import tkinter as tk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.settings import EditorSettings

from ..utils.themes import THEME


class Minimap(tk.Canvas):
    """Code minimap with viewport indicator."""
    
    def __init__(self, master, text_widget: tk.Text, settings: 'EditorSettings', **kwargs):
        s = settings.ui_scale
        super().__init__(
            master, width=int(100*s), bg=THEME.bg_dark,
            highlightthickness=0, **kwargs
        )
        self.text_widget = text_widget
        self.settings = settings
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_click)
    
    def _on_click(self, event):
        """Handle click to navigate."""
        if not self.text_widget:
            return
        
        try:
            height = self.winfo_height()
            total = int(self.text_widget.index("end-1c").split(".")[0])
            
            if total > 0 and height > 0:
                target = max(1, int((event.y / height) * total))
                self.text_widget.see(f"{target}.0")
        except Exception:
            pass
    
    def redraw(self):
        """Redraw the minimap."""
        self.delete("all")
        
        if not self.text_widget:
            return
        
        try:
            content = self.text_widget.get("1.0", "end-1c")
        except Exception:
            return
        
        lines = content.split("\n")
        total = len(lines)
        
        if total == 0:
            return
        
        height = self.winfo_height()
        width = self.winfo_width()
        
        if height <= 0:
            return
        
        line_h = max(1, height / max(total, 1))
        
        # Draw lines
        for i, line in enumerate(lines[:3000]):  # Limit for performance
            y = i * line_h
            if y > height:
                break
            
            stripped = line.strip()
            if not stripped:
                continue
            
            length = min(len(stripped), 100)
            x2 = min(4 + length * 0.4, width - 4)
            self.create_line(4, y, x2, y, fill=THEME.text_disabled,
                           width=max(1, line_h * 0.4))
        
        # Draw viewport indicator
        try:
            first = int(self.text_widget.index("@0,0").split(".")[0])
            last = int(self.text_widget.index(
                f"@0,{self.text_widget.winfo_height()}"
            ).split(".")[0])
            
            y1 = (first - 1) * line_h
            y2 = last * line_h
            
            self.create_rectangle(
                0, y1, width, y2,
                fill=THEME.minimap_viewport,
                outline=THEME.accent_primary,
                width=1
            )
        except Exception:
            pass
