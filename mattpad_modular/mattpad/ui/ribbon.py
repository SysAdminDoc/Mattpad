"""Ribbon UI components for Mattpad."""
import customtkinter as ctk
from typing import Dict, List, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.settings import EditorSettings

from ..utils.themes import THEME


class RibbonButton(ctk.CTkFrame):
    """Button for ribbon toolbar."""
    
    def __init__(self, master, icon: str, text: str, command: Callable,
                 settings: 'EditorSettings', large: bool = False, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        s = settings.ui_scale
        self.command = command
        
        if large:
            self.configure(width=int(58*s), height=int(66*s))
            self.btn = ctk.CTkButton(
                self, text=icon, width=int(40*s), height=int(36*s),
                fg_color="transparent", hover_color=THEME.ribbon_tab_hover,
                font=ctk.CTkFont(size=int(18*s)), command=command,
                corner_radius=int(4*s)
            )
            self.btn.pack(pady=(int(4*s), 0))
            self.lbl = ctk.CTkLabel(
                self, text=text, font=ctk.CTkFont(size=int(9*s)),
                text_color=THEME.text_secondary
            )
            self.lbl.pack()
        else:
            self.configure(height=int(26*s))
            self.btn = ctk.CTkButton(
                self, text=f"{icon} {text}", height=int(24*s),
                fg_color="transparent", hover_color=THEME.ribbon_tab_hover,
                font=ctk.CTkFont(size=int(10*s)), command=command,
                corner_radius=int(3*s), anchor="w"
            )
            self.btn.pack(fill="x", padx=int(2*s))


class RibbonGroup(ctk.CTkFrame):
    """Group of controls in a ribbon tab."""
    
    def __init__(self, master, title: str, settings: 'EditorSettings', **kwargs):
        super().__init__(master, fg_color=THEME.ribbon_group_bg,
                        corner_radius=int(4*settings.ui_scale), **kwargs)
        s = settings.ui_scale
        
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=int(6*s), pady=(int(4*s), 0))
        
        ctk.CTkLabel(
            self, text=title, font=ctk.CTkFont(size=int(9*s)),
            text_color=THEME.text_muted, height=int(16*s)
        ).pack(side="bottom", pady=(0, int(2*s)))


class RibbonTab(ctk.CTkFrame):
    """Tab content in the ribbon."""
    
    def __init__(self, master, settings: 'EditorSettings', **kwargs):
        super().__init__(master, fg_color=THEME.ribbon_bg,
                        height=int(90*settings.ui_scale), corner_radius=0, **kwargs)
        self.settings = settings
        self.pack_propagate(False)
        self.groups: List[RibbonGroup] = []
    
    def add_group(self, title: str) -> RibbonGroup:
        """Add a group to the tab."""
        s = self.settings.ui_scale
        
        # Add separator if not first group
        if self.groups:
            sep = ctk.CTkFrame(self, width=int(1*s), fg_color=THEME.ribbon_separator)
            sep.pack(side="left", fill="y", padx=int(4*s), pady=int(6*s))
        
        group = RibbonGroup(self, title, self.settings)
        group.pack(side="left", fill="y", padx=int(4*s), pady=int(4*s))
        self.groups.append(group)
        
        return group


class Ribbon(ctk.CTkFrame):
    """Main ribbon toolbar."""
    
    def __init__(self, master, settings: 'EditorSettings', **kwargs):
        super().__init__(master, fg_color=THEME.ribbon_bg, corner_radius=0, **kwargs)
        self.settings = settings
        self.tabs: Dict[str, RibbonTab] = {}
        self.tab_buttons: Dict[str, ctk.CTkButton] = {}
        self.active_tab = None
        self.pinned = settings.ribbon_pinned
        self.collapsed = not self.pinned
        self._mouse_check_id = None
        self._create()
    
    def _create(self):
        """Create the ribbon UI."""
        s = self.settings.ui_scale
        
        # Tab bar
        self.tab_bar = ctk.CTkFrame(self, fg_color=THEME.ribbon_tab_bg,
                                   height=int(30*s), corner_radius=0)
        self.tab_bar.pack(fill="x")
        self.tab_bar.pack_propagate(False)
        
        # Logo
        ctk.CTkLabel(
            self.tab_bar, text="  Mattpad",
            font=ctk.CTkFont(size=int(12*s), weight="bold"),
            text_color=THEME.accent_primary
        ).pack(side="left", padx=int(8*s))
        
        # Tab buttons container
        self.tab_btn_frame = ctk.CTkFrame(self.tab_bar, fg_color="transparent")
        self.tab_btn_frame.pack(side="left", fill="y", padx=int(10*s))
        
        # Pin button
        self.pin_btn = ctk.CTkButton(
            self.tab_bar,
            text="📌" if self.pinned else "📍",
            width=int(28*s), height=int(24*s),
            fg_color=THEME.ribbon_tab_active if self.pinned else "transparent",
            hover_color=THEME.ribbon_tab_hover,
            font=ctk.CTkFont(size=int(12*s)),
            command=self._toggle_pin
        )
        self.pin_btn.pack(side="right", padx=int(4*s))
        
        # Content frame (shows tab content)
        self.content_frame = ctk.CTkFrame(self, fg_color=THEME.ribbon_bg, corner_radius=0)
        if not self.collapsed:
            self.content_frame.pack(fill="x")
    
    def add_tab(self, name: str) -> RibbonTab:
        """Add a tab to the ribbon."""
        s = self.settings.ui_scale
        
        # Create tab button
        btn = ctk.CTkButton(
            self.tab_btn_frame, text=name,
            width=int(70*s), height=int(26*s),
            fg_color="transparent", hover_color=THEME.ribbon_tab_hover,
            font=ctk.CTkFont(size=int(11*s)), corner_radius=0,
            command=lambda n=name: self._on_tab_click(n)
        )
        btn.pack(side="left", padx=int(1*s), pady=int(2*s))
        btn.bind("<Double-1>", lambda e: self._toggle_pin())
        self.tab_buttons[name] = btn
        
        # Create tab content
        tab = RibbonTab(self.content_frame, self.settings)
        self.tabs[name] = tab
        
        # Set first tab as active
        if self.active_tab is None:
            self.active_tab = name
            if not self.collapsed:
                self.show_tab(name)
        
        return tab
    
    def _start_mouse_check(self):
        """Start checking if mouse leaves ribbon."""
        if self._mouse_check_id:
            return
        self._check_mouse_position()
    
    def _stop_mouse_check(self):
        """Stop mouse position checking."""
        if self._mouse_check_id:
            self.after_cancel(self._mouse_check_id)
            self._mouse_check_id = None
    
    def _check_mouse_position(self):
        """Check if mouse is still over ribbon."""
        if self.pinned or self.collapsed:
            self._mouse_check_id = None
            return
        
        try:
            x, y = self.winfo_pointerxy()
            rx = self.winfo_rootx()
            ry = self.winfo_rooty()
            rw = self.winfo_width()
            rh = self.winfo_height()
            
            if not (rx <= x <= rx + rw and ry <= y <= ry + rh):
                self._collapse()
                self._mouse_check_id = None
                return
        except Exception:
            pass
        
        self._mouse_check_id = self.after(100, self._check_mouse_position)
    
    def _on_tab_click(self, name: str):
        """Handle tab button click."""
        if self.collapsed:
            self._expand()
        self.show_tab(name)
        self._start_mouse_check()
    
    def show_tab(self, name: str):
        """Show a specific tab."""
        if name not in self.tabs:
            return
        
        # Hide all tabs
        for n, tab in self.tabs.items():
            tab.pack_forget()
            self.tab_buttons[n].configure(fg_color="transparent")
        
        # Show selected tab
        self.tabs[name].pack(fill="x")
        self.tab_buttons[name].configure(fg_color=THEME.ribbon_tab_active)
        self.active_tab = name
    
    def _expand(self):
        """Expand the ribbon."""
        if not self.collapsed:
            return
        
        self.collapsed = False
        self.content_frame.pack(fill="x")
        
        if self.active_tab:
            self.show_tab(self.active_tab)
        
        self._start_mouse_check()
    
    def _collapse(self):
        """Collapse the ribbon."""
        if self.collapsed or self.pinned:
            return
        
        self.collapsed = True
        self.content_frame.pack_forget()
        self._stop_mouse_check()
    
    def _toggle_pin(self):
        """Toggle ribbon pin state."""
        self.pinned = not self.pinned
        self.settings.ribbon_pinned = self.pinned
        
        if self.pinned:
            self.pin_btn.configure(text="📌", fg_color=THEME.ribbon_tab_active)
            if self.collapsed:
                self._expand()
            self._stop_mouse_check()
        else:
            self.pin_btn.configure(text="📍", fg_color="transparent")
            if not self.collapsed:
                self._start_mouse_check()
    
    def auto_hide(self):
        """Auto-hide ribbon if not pinned."""
        if not self.pinned and not self.collapsed:
            self._collapse()
