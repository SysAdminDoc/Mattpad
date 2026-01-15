"""File tree sidebar for Mattpad."""
import os
import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.settings import EditorSettings

from ..utils.themes import THEME
from ..utils.file_utils import get_file_icon, get_folder_icon


class FileTreeView(ctk.CTkFrame):
    """File explorer sidebar."""
    
    def __init__(self, master, on_file_select: Callable, settings: 'EditorSettings', **kwargs):
        super().__init__(master, fg_color=THEME.bg_dark, corner_radius=0, **kwargs)
        self.on_file_select = on_file_select
        self.settings = settings
        self.current_folder: Optional[str] = None
        self._create()
    
    def _create(self):
        """Create the file tree UI."""
        s = self.settings.ui_scale
        
        # Header
        header = ctk.CTkFrame(self, fg_color=THEME.ribbon_group_bg, height=int(36*s), corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header, text="  EXPLORER",
            font=ctk.CTkFont(size=int(11*s), weight="bold"),
            text_color=THEME.text_secondary
        ).pack(side="left", padx=int(4*s))
        
        # Refresh button
        ctk.CTkButton(
            header, text="↻", width=int(28*s), height=int(24*s),
            fg_color="transparent", hover_color=THEME.bg_hover,
            text_color=THEME.text_muted,
            command=self.refresh
        ).pack(side="right", padx=int(4*s))
        
        # Open folder button
        ctk.CTkButton(
            header, text="📂", width=int(28*s), height=int(24*s),
            fg_color="transparent", hover_color=THEME.bg_hover,
            text_color=THEME.text_muted,
            command=self._open_folder
        ).pack(side="right")
        
        # Tree view with custom style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=THEME.bg_dark,
            foreground=THEME.text_primary,
            fieldbackground=THEME.bg_dark,
            borderwidth=0,
            font=("Segoe UI", int(10*s))
        )
        style.configure(
            "Treeview.Heading",
            background=THEME.bg_medium,
            foreground=THEME.text_primary
        )
        style.map(
            "Treeview",
            background=[("selected", THEME.selection_bg)],
            foreground=[("selected", THEME.text_primary)]
        )
        
        # Tree container
        tree_frame = ctk.CTkFrame(self, fg_color=THEME.bg_dark)
        tree_frame.pack(fill="both", expand=True)
        
        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        self.tree.pack(fill="both", expand=True, padx=int(2*s), pady=int(2*s))
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(tree_frame, command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Bindings
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Return>", self._on_double_click)
        self.tree.bind("<<TreeviewOpen>>", self._on_expand)
    
    def _open_folder(self):
        """Open folder dialog."""
        from tkinter import filedialog
        folder = filedialog.askdirectory()
        if folder:
            self.load_folder(folder)
    
    def load_folder(self, folder: str):
        """Load a folder into the tree."""
        if not os.path.isdir(folder):
            return
        
        self.current_folder = folder
        self.settings.last_folder = folder
        
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add root folder
        folder_name = os.path.basename(folder) or folder
        root_id = self.tree.insert("", "end", text=f"📁 {folder_name}", values=(folder,), open=True)
        
        # Load contents
        self._load_directory(root_id, folder)
    
    def _load_directory(self, parent: str, path: str, depth: int = 0):
        """Load directory contents into tree."""
        if depth > 10:  # Prevent infinite recursion
            return
        
        try:
            items = sorted(os.listdir(path), key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
        except PermissionError:
            return
        
        for item in items:
            # Skip hidden files and common ignore patterns
            if item.startswith('.') or item in ('__pycache__', 'node_modules', '.git', 'venv', '.venv'):
                continue
            
            item_path = os.path.join(path, item)
            
            if os.path.isdir(item_path):
                icon = get_folder_icon(item)
                node = self.tree.insert(parent, "end", text=f"{icon} {item}", values=(item_path,))
                # Add dummy child to make expandable
                self.tree.insert(node, "end", text="Loading...")
            else:
                icon = get_file_icon(item_path)
                self.tree.insert(parent, "end", text=f"{icon} {item}", values=(item_path,))
    
    def _on_expand(self, event):
        """Handle tree node expansion."""
        node = self.tree.focus()
        children = self.tree.get_children(node)
        
        # If first child is "Loading...", replace with actual contents
        if children and self.tree.item(children[0])["text"] == "Loading...":
            self.tree.delete(children[0])
            values = self.tree.item(node)["values"]
            if values:
                self._load_directory(node, values[0])
    
    def _on_double_click(self, event):
        """Handle double-click on item."""
        node = self.tree.focus()
        if not node:
            return
        
        values = self.tree.item(node)["values"]
        if not values:
            return
        
        path = values[0]
        
        if os.path.isfile(path):
            self.on_file_select(path)
        elif os.path.isdir(path):
            # Toggle expansion
            if self.tree.item(node, "open"):
                self.tree.item(node, open=False)
            else:
                self.tree.item(node, open=True)
    
    def refresh(self):
        """Refresh the current folder."""
        if self.current_folder:
            self.load_folder(self.current_folder)
    
    def reveal_file(self, filepath: str):
        """Reveal a file in the tree."""
        # Would need to implement tree traversal to find and select the file
        pass
