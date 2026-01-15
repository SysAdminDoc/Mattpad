"""Line number display component for Mattpad."""
import tkinter as tk
from tkinter import font as tkfont
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.settings import EditorSettings

from ..utils.themes import THEME


class LineNumberCanvas(tk.Canvas):
    """Line number display for text editor."""
    
    def __init__(self, master, settings: 'EditorSettings', **kwargs):
        s = settings.ui_scale
        super().__init__(
            master, width=int(50*s), bg=THEME.bg_dark,
            highlightthickness=0, borderwidth=0, **kwargs
        )
        self.settings = settings
        self.text_widget: Optional[tk.Text] = None
        self.text_font: Optional[tkfont.Font] = None
        self._last_line_count = 0
    
    def redraw(self):
        """Redraw line numbers."""
        if not self.text_widget:
            return
        
        self.delete("all")
        s = self.settings.ui_scale
        
        try:
            # Get visible range
            first_visible = self.text_widget.index("@0,0")
            last_visible = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}")
            first_line = int(first_visible.split(".")[0])
            last_line = int(last_visible.split(".")[0])
            
            # Get total lines
            total_lines = int(self.text_widget.index("end-1c").split(".")[0])
            
            # Adjust canvas width based on line count
            digits = len(str(total_lines))
            new_width = int((digits + 2) * 8 * s)
            if self.winfo_width() != new_width:
                self.configure(width=new_width)
            
            # Get font metrics
            if self.text_font:
                line_height = self.text_font.metrics("linespace")
            else:
                line_height = int(14 * s)
            
            # Draw line numbers
            for line_num in range(first_line, last_line + 1):
                # Get y coordinate from text widget
                try:
                    bbox = self.text_widget.bbox(f"{line_num}.0")
                    if bbox:
                        y = bbox[1] + bbox[3] // 2
                        self.create_text(
                            new_width - int(8*s), y,
                            text=str(line_num),
                            anchor="e",
                            fill=THEME.text_muted,
                            font=(self.settings.font_family, int(self.settings.font_size * s * 0.9))
                        )
                except Exception:
                    pass
            
            self._last_line_count = total_lines
            
        except Exception:
            pass
    
    def highlight_line(self, line_num: int):
        """Highlight a specific line number."""
        # This could be extended to show current line highlight
        pass
    
    def update_font(self, font_family: str, font_size: int):
        """Update the font used for line numbers."""
        s = self.settings.ui_scale
        self.text_font = tkfont.Font(family=font_family, size=int(font_size * s))
