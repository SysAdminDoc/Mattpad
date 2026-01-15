"""Find and replace bar for Mattpad."""
import customtkinter as ctk
import tkinter as tk
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.settings import EditorSettings

from ..utils.themes import THEME


class FindReplaceBar(ctk.CTkFrame):
    """Find and replace bar."""
    
    def __init__(self, master, on_find: Callable, on_replace: Callable,
                 on_replace_all: Callable, on_close: Callable, on_find_in_files: Callable,
                 settings: 'EditorSettings', **kwargs):
        super().__init__(master, fg_color=THEME.ribbon_group_bg, height=int(40*settings.ui_scale), corner_radius=0, **kwargs)
        self.settings = settings
        self.on_find = on_find
        self.on_replace = on_replace
        self.on_replace_all = on_replace_all
        self.on_close = on_close
        self.on_find_in_files = on_find_in_files
        
        self.pack_propagate(False)
        self._create()
    
    def _create(self):
        """Create the find/replace UI."""
        s = self.settings.ui_scale
        
        # Find row
        find_row = ctk.CTkFrame(self, fg_color="transparent")
        find_row.pack(fill="x", padx=int(8*s), pady=(int(6*s), int(2*s)))
        
        ctk.CTkLabel(
            find_row, text="Find:",
            font=ctk.CTkFont(size=int(11*s)),
            width=int(60*s), anchor="e"
        ).pack(side="left")
        
        self.find_entry = ctk.CTkEntry(
            find_row, width=int(250*s),
            fg_color=THEME.bg_darkest,
            border_color=THEME.bg_light,
            font=ctk.CTkFont(size=int(11*s))
        )
        self.find_entry.pack(side="left", padx=int(8*s))
        self.find_entry.bind("<Return>", lambda e: self._do_find())
        self.find_entry.bind("<Escape>", lambda e: self.on_close())
        
        # Options
        self.case_var = tk.BooleanVar(value=False)
        self.regex_var = tk.BooleanVar(value=False)
        self.word_var = tk.BooleanVar(value=False)
        
        ctk.CTkCheckBox(
            find_row, text="Aa",
            variable=self.case_var,
            width=int(50*s), height=int(24*s),
            font=ctk.CTkFont(size=int(10*s)),
            fg_color=THEME.accent_primary,
            checkbox_width=int(18*s),
            checkbox_height=int(18*s)
        ).pack(side="left", padx=int(2*s))
        
        ctk.CTkCheckBox(
            find_row, text=".*",
            variable=self.regex_var,
            width=int(50*s), height=int(24*s),
            font=ctk.CTkFont(size=int(10*s)),
            fg_color=THEME.accent_primary,
            checkbox_width=int(18*s),
            checkbox_height=int(18*s)
        ).pack(side="left", padx=int(2*s))
        
        ctk.CTkCheckBox(
            find_row, text="\\b",
            variable=self.word_var,
            width=int(50*s), height=int(24*s),
            font=ctk.CTkFont(size=int(10*s)),
            fg_color=THEME.accent_primary,
            checkbox_width=int(18*s),
            checkbox_height=int(18*s)
        ).pack(side="left", padx=int(2*s))
        
        # Find buttons
        btn_cfg = {
            "width": int(70*s),
            "height": int(26*s),
            "font": ctk.CTkFont(size=int(10*s)),
            "fg_color": THEME.bg_medium,
            "hover_color": THEME.bg_hover
        }
        
        ctk.CTkButton(
            find_row, text="Find",
            command=self._do_find, **btn_cfg
        ).pack(side="left", padx=int(2*s))
        
        ctk.CTkButton(
            find_row, text="Find All",
            command=self._do_find_all, **btn_cfg
        ).pack(side="left", padx=int(2*s))
        
        # Match count label
        self.match_label = ctk.CTkLabel(
            find_row, text="",
            font=ctk.CTkFont(size=int(10*s)),
            text_color=THEME.text_secondary
        )
        self.match_label.pack(side="left", padx=int(8*s))
        
        # Close button
        ctk.CTkButton(
            find_row, text="×",
            width=int(28*s), height=int(26*s),
            fg_color="transparent",
            hover_color=THEME.tab_close_hover,
            text_color=THEME.text_muted,
            font=ctk.CTkFont(size=int(14*s)),
            command=self.on_close
        ).pack(side="right")
        
        # Replace row
        replace_row = ctk.CTkFrame(self, fg_color="transparent")
        replace_row.pack(fill="x", padx=int(8*s), pady=(int(2*s), int(6*s)))
        
        ctk.CTkLabel(
            replace_row, text="Replace:",
            font=ctk.CTkFont(size=int(11*s)),
            width=int(60*s), anchor="e"
        ).pack(side="left")
        
        self.replace_entry = ctk.CTkEntry(
            replace_row, width=int(250*s),
            fg_color=THEME.bg_darkest,
            border_color=THEME.bg_light,
            font=ctk.CTkFont(size=int(11*s))
        )
        self.replace_entry.pack(side="left", padx=int(8*s))
        self.replace_entry.bind("<Return>", lambda e: self._do_replace())
        self.replace_entry.bind("<Escape>", lambda e: self.on_close())
        
        ctk.CTkButton(
            replace_row, text="Replace",
            command=self._do_replace, **btn_cfg
        ).pack(side="left", padx=int(2*s))
        
        ctk.CTkButton(
            replace_row, text="Replace All",
            command=self._do_replace_all, **btn_cfg
        ).pack(side="left", padx=int(2*s))
        
        # Update height for replace row
        self.configure(height=int(80*s))
    
    def _do_find(self):
        """Execute find."""
        query = self.find_entry.get()
        if query:
            self.on_find(query, self.case_var.get(), self.regex_var.get(), self.word_var.get())
    
    def _do_find_all(self):
        """Execute find all."""
        query = self.find_entry.get()
        if query:
            self.on_find(query, self.case_var.get(), self.regex_var.get(), self.word_var.get(), find_all=True)
    
    def _do_replace(self):
        """Execute replace."""
        find_text = self.find_entry.get()
        replace_text = self.replace_entry.get()
        if find_text:
            self.on_replace(find_text, replace_text, self.case_var.get(), self.regex_var.get())
    
    def _do_replace_all(self):
        """Execute replace all."""
        find_text = self.find_entry.get()
        replace_text = self.replace_entry.get()
        if find_text:
            self.on_replace_all(find_text, replace_text, self.case_var.get(), self.regex_var.get())
    
    def set_match_count(self, current: int, total: int):
        """Update match count display."""
        if total > 0:
            self.match_label.configure(text=f"{current}/{total} matches")
        else:
            self.match_label.configure(text="No matches")
    
    def focus_find(self):
        """Focus the find entry."""
        self.find_entry.focus_set()
        self.find_entry.select_range(0, tk.END)
    
    def set_find_text(self, text: str):
        """Set the find entry text."""
        self.find_entry.delete(0, tk.END)
        self.find_entry.insert(0, text)
