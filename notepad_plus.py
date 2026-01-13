#!/usr/bin/env python3
"""
Notepad Plus - A Notepad++ inspired text editor
Custom dark theme with syntax highlighting, tabs, and professional features
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, font as tkfont
import tkinter as tk
from tkinter import ttk
import os
import re
import json
from pathlib import Path
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
import hashlib

# ═══════════════════════════════════════════════════════════════════════════════
# THEME CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ThemeColors:
    """Color scheme configuration"""
    # Main colors
    bg_darkest: str = "#020617"      # Main background
    bg_dark: str = "#0f172a"          # Panel backgrounds
    bg_medium: str = "#1e293b"        # Elevated surfaces
    bg_light: str = "#334155"         # Borders, separators
    
    # Accent colors
    accent_green: str = "#22c55e"     # Primary accent
    accent_blue: str = "#60a5fa"      # Secondary accent
    accent_purple: str = "#a78bfa"    # Tertiary accent
    accent_orange: str = "#fb923c"    # Warning/highlight
    accent_red: str = "#ef4444"       # Error/danger
    accent_cyan: str = "#22d3ee"      # Info
    
    # Text colors
    text_primary: str = "#f8fafc"     # Main text
    text_secondary: str = "#94a3b8"   # Dimmed text
    text_muted: str = "#64748b"       # Very dimmed text
    
    # Syntax highlighting colors
    syntax_keyword: str = "#c084fc"   # Keywords (purple)
    syntax_string: str = "#4ade80"    # Strings (green)
    syntax_comment: str = "#64748b"   # Comments (gray)
    syntax_number: str = "#fb923c"    # Numbers (orange)
    syntax_function: str = "#60a5fa"  # Functions (blue)
    syntax_class: str = "#22d3ee"     # Classes (cyan)
    syntax_operator: str = "#f472b6"  # Operators (pink)
    syntax_decorator: str = "#fbbf24" # Decorators (yellow)
    syntax_builtin: str = "#38bdf8"   # Builtins (sky blue)
    syntax_constant: str = "#f97316"  # Constants (deep orange)
    
    # Selection colors
    selection_bg: str = "#3b82f6"     # Selection background
    current_line: str = "#1e293b"     # Current line highlight
    
    # Tab colors
    tab_active: str = "#1e293b"
    tab_inactive: str = "#0f172a"
    tab_hover: str = "#334155"
    tab_modified: str = "#fbbf24"     # Modified indicator

THEME = ThemeColors()

# ═══════════════════════════════════════════════════════════════════════════════
# SYNTAX HIGHLIGHTING PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

SYNTAX_PATTERNS = {
    ".py": {
        "keywords": r'\b(and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield|True|False|None)\b',
        "strings": r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
        "comments": r'(#.*$)',
        "numbers": r'\b(\d+\.?\d*(?:e[+-]?\d+)?|0x[0-9a-fA-F]+|0b[01]+|0o[0-7]+)\b',
        "functions": r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()',
        "classes": r'\bclass\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        "decorators": r'(@[a-zA-Z_][a-zA-Z0-9_\.]*)',
        "builtins": r'\b(print|len|range|str|int|float|list|dict|set|tuple|bool|type|isinstance|hasattr|getattr|setattr|open|file|input|super|property|staticmethod|classmethod|abs|all|any|bin|hex|oct|ord|chr|enumerate|filter|map|zip|sorted|reversed|min|max|sum|round)\b',
    },
    ".js": {
        "keywords": r'\b(break|case|catch|continue|debugger|default|delete|do|else|finally|for|function|if|in|instanceof|new|return|switch|this|throw|try|typeof|var|void|while|with|class|const|enum|export|extends|import|super|implements|interface|let|package|private|protected|public|static|yield|await|async|of)\b',
        "strings": r'(`[\s\S]*?`|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
        "comments": r'(\/\/.*$|\/\*[\s\S]*?\*\/)',
        "numbers": r'\b(\d+\.?\d*(?:e[+-]?\d+)?|0x[0-9a-fA-F]+|0b[01]+|0o[0-7]+)\b',
        "functions": r'\b([a-zA-Z_$][a-zA-Z0-9_$]*)\s*(?=\()',
        "classes": r'\bclass\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
        "operators": r'(===|!==|==|!=|<=|>=|&&|\|\||[+\-*/%=<>!&|^~])',
    },
    ".html": {
        "tags": r'(<\/?[a-zA-Z][a-zA-Z0-9]*)',
        "attributes": r'\s([a-zA-Z\-]+)(?==)',
        "strings": r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
        "comments": r'(<!--[\s\S]*?-->)',
        "entities": r'(&[a-zA-Z]+;|&#\d+;)',
    },
    ".css": {
        "selectors": r'^([.#]?[a-zA-Z][a-zA-Z0-9_\-]*)',
        "properties": r'\b([a-zA-Z\-]+)\s*:',
        "values": r':\s*([^;{]+)',
        "strings": r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
        "comments": r'(\/\*[\s\S]*?\*\/)',
        "numbers": r'\b(\d+\.?\d*(?:px|em|rem|%|vh|vw|deg|s|ms)?)\b',
        "colors": r'(#[0-9a-fA-F]{3,8})',
    },
    ".json": {
        "keys": r'"([^"]+)"\s*:',
        "strings": r':\s*"([^"]*)"',
        "numbers": r'\b(-?\d+\.?\d*(?:e[+-]?\d+)?)\b',
        "constants": r'\b(true|false|null)\b',
    },
    ".md": {
        "headers": r'^(#{1,6}\s+.+)$',
        "bold": r'(\*\*[^*]+\*\*|__[^_]+__)',
        "italic": r'(\*[^*]+\*|_[^_]+_)',
        "code": r'(`[^`]+`|```[\s\S]*?```)',
        "links": r'(\[[^\]]+\]\([^)]+\))',
        "lists": r'^(\s*[\-*+]\s|\s*\d+\.\s)',
    },
    ".xml": {
        "tags": r'(<\/?[a-zA-Z][a-zA-Z0-9:\-]*)',
        "attributes": r'\s([a-zA-Z:\-]+)(?==)',
        "strings": r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
        "comments": r'(<!--[\s\S]*?-->)',
        "cdata": r'(<!\[CDATA\[[\s\S]*?\]\]>)',
    },
    ".sql": {
        "keywords": r'\b(SELECT|FROM|WHERE|AND|OR|NOT|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|TABLE|ALTER|DROP|INDEX|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AS|ORDER|BY|GROUP|HAVING|LIMIT|OFFSET|UNION|ALL|DISTINCT|NULL|IS|IN|LIKE|BETWEEN|EXISTS|CASE|WHEN|THEN|ELSE|END|COUNT|SUM|AVG|MIN|MAX|PRIMARY|KEY|FOREIGN|REFERENCES|CONSTRAINT|DEFAULT|CHECK|UNIQUE)\b',
        "strings": r'(\'(?:[^\'\\]|\\.)*\')',
        "comments": r'(--.*$|\/\*[\s\S]*?\*\/)',
        "numbers": r'\b(\d+\.?\d*)\b',
    },
    ".sh": {
        "keywords": r'\b(if|then|else|elif|fi|for|while|do|done|case|esac|in|function|return|exit|break|continue|export|local|readonly|shift|source|alias|unalias|set|unset|echo|printf|read|cd|pwd|ls|cp|mv|rm|mkdir|rmdir|cat|grep|sed|awk|cut|sort|uniq|wc|head|tail|find|xargs|chmod|chown|sudo|su)\b',
        "strings": r'("(?:[^"\\]|\\.)*"|\'[^\']*\')',
        "comments": r'(#.*$)',
        "variables": r'(\$[a-zA-Z_][a-zA-Z0-9_]*|\$\{[^}]+\})',
        "numbers": r'\b(\d+)\b',
    },
    ".ps1": {
        "keywords": r'\b(if|else|elseif|switch|while|for|foreach|do|until|break|continue|return|exit|throw|try|catch|finally|function|filter|param|begin|process|end|class|enum|using|import|export|module|workflow|parallel|sequence|inlinescript)\b',
        "cmdlets": r'\b([A-Z][a-z]+\-[A-Z][a-zA-Z]+)\b',
        "strings": r'("(?:[^"\\]|\\.)*"|\'[^\']*\')',
        "comments": r'(#.*$|<#[\s\S]*?#>)',
        "variables": r'(\$[a-zA-Z_][a-zA-Z0-9_]*)',
        "numbers": r'\b(\d+\.?\d*)\b',
    },
    ".c": {
        "keywords": r'\b(auto|break|case|char|const|continue|default|do|double|else|enum|extern|float|for|goto|if|int|long|register|return|short|signed|sizeof|static|struct|switch|typedef|union|unsigned|void|volatile|while|inline|restrict|_Bool|_Complex|_Imaginary)\b',
        "strings": r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
        "comments": r'(\/\/.*$|\/\*[\s\S]*?\*\/)',
        "numbers": r'\b(\d+\.?\d*[fFlLuU]*|0x[0-9a-fA-F]+[lLuU]*)\b',
        "preprocessor": r'^(\s*#\s*\w+)',
        "functions": r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()',
    },
    ".cpp": {
        "keywords": r'\b(alignas|alignof|and|and_eq|asm|auto|bitand|bitor|bool|break|case|catch|char|char8_t|char16_t|char32_t|class|compl|concept|const|consteval|constexpr|constinit|const_cast|continue|co_await|co_return|co_yield|decltype|default|delete|do|double|dynamic_cast|else|enum|explicit|export|extern|false|float|for|friend|goto|if|inline|int|long|mutable|namespace|new|noexcept|not|not_eq|nullptr|operator|or|or_eq|private|protected|public|register|reinterpret_cast|requires|return|short|signed|sizeof|static|static_assert|static_cast|struct|switch|template|this|thread_local|throw|true|try|typedef|typeid|typename|union|unsigned|using|virtual|void|volatile|wchar_t|while|xor|xor_eq)\b',
        "strings": r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
        "comments": r'(\/\/.*$|\/\*[\s\S]*?\*\/)',
        "numbers": r'\b(\d+\.?\d*[fFlLuU]*|0x[0-9a-fA-F]+[lLuU]*)\b',
        "preprocessor": r'^(\s*#\s*\w+)',
        "functions": r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()',
    },
    ".java": {
        "keywords": r'\b(abstract|assert|boolean|break|byte|case|catch|char|class|const|continue|default|do|double|else|enum|extends|final|finally|float|for|goto|if|implements|import|instanceof|int|interface|long|native|new|package|private|protected|public|return|short|static|strictfp|super|switch|synchronized|this|throw|throws|transient|try|void|volatile|while|true|false|null)\b',
        "strings": r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
        "comments": r'(\/\/.*$|\/\*[\s\S]*?\*\/)',
        "numbers": r'\b(\d+\.?\d*[fFdDlL]?|0x[0-9a-fA-F]+[lL]?)\b',
        "annotations": r'(@[a-zA-Z_][a-zA-Z0-9_]*)',
        "functions": r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()',
    },
    ".go": {
        "keywords": r'\b(break|case|chan|const|continue|default|defer|else|fallthrough|for|func|go|goto|if|import|interface|map|package|range|return|select|struct|switch|type|var|true|false|nil|iota)\b',
        "strings": r'(`[^`]*`|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
        "comments": r'(\/\/.*$|\/\*[\s\S]*?\*\/)',
        "numbers": r'\b(\d+\.?\d*(?:e[+-]?\d+)?|0x[0-9a-fA-F]+|0o[0-7]+|0b[01]+)\b',
        "functions": r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()',
    },
    ".rs": {
        "keywords": r'\b(as|async|await|break|const|continue|crate|dyn|else|enum|extern|false|fn|for|if|impl|in|let|loop|match|mod|move|mut|pub|ref|return|self|Self|static|struct|super|trait|true|type|union|unsafe|use|where|while)\b',
        "strings": r'(r#*"[^"]*"#*|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
        "comments": r'(\/\/.*$|\/\*[\s\S]*?\*\/)',
        "numbers": r'\b(\d+\.?\d*(?:e[+-]?\d+)?(?:_\d+)*(?:i8|i16|i32|i64|i128|isize|u8|u16|u32|u64|u128|usize|f32|f64)?|0x[0-9a-fA-F_]+|0o[0-7_]+|0b[01_]+)\b',
        "macros": r'\b([a-zA-Z_][a-zA-Z0-9_]*!)',
        "functions": r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()',
        "lifetimes": r"('[a-zA-Z_][a-zA-Z0-9_]*)",
    },
    ".ts": {
        "keywords": r'\b(break|case|catch|continue|debugger|default|delete|do|else|finally|for|function|if|in|instanceof|new|return|switch|this|throw|try|typeof|var|void|while|with|class|const|enum|export|extends|import|super|implements|interface|let|package|private|protected|public|static|yield|await|async|of|type|namespace|abstract|as|declare|is|module|readonly|require|global|keyof|infer|never|unknown|any|boolean|number|string|symbol|bigint|object|undefined|null)\b',
        "strings": r'(`[\s\S]*?`|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')',
        "comments": r'(\/\/.*$|\/\*[\s\S]*?\*\/)',
        "numbers": r'\b(\d+\.?\d*(?:e[+-]?\d+)?|0x[0-9a-fA-F]+|0b[01]+|0o[0-7]+)\b',
        "functions": r'\b([a-zA-Z_$][a-zA-Z0-9_$]*)\s*(?=\()',
        "decorators": r'(@[a-zA-Z_][a-zA-Z0-9_\.]*)',
        "types": r':\s*([A-Z][a-zA-Z0-9_]*)',
    },
}

# File extension mappings
FILE_EXTENSIONS = {
    ".py": "Python",
    ".pyw": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".json": "JSON",
    ".xml": "XML",
    ".md": "Markdown",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Bash",
    ".ps1": "PowerShell",
    ".psm1": "PowerShell Module",
    ".c": "C",
    ".h": "C Header",
    ".cpp": "C++",
    ".hpp": "C++ Header",
    ".cc": "C++",
    ".cxx": "C++",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin Script",
    ".lua": "Lua",
    ".r": "R",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Config",
    ".conf": "Config",
    ".txt": "Plain Text",
    ".log": "Log",
    ".csv": "CSV",
    ".bat": "Batch",
    ".cmd": "Batch",
}

# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TabData:
    """Data for a single editor tab"""
    filepath: Optional[str] = None
    modified: bool = False
    content_hash: str = ""
    encoding: str = "utf-8"
    line_ending: str = "\n"
    language: str = "Plain Text"
    cursor_pos: tuple = (1, 0)  # line, column
    scroll_pos: tuple = (0, 0)

@dataclass
class SearchState:
    """State for find/replace operations"""
    find_text: str = ""
    replace_text: str = ""
    match_case: bool = False
    whole_word: bool = False
    use_regex: bool = False
    search_up: bool = False
    wrap_around: bool = True
    in_selection: bool = False

@dataclass
class EditorSettings:
    """Editor configuration settings"""
    font_family: str = "Consolas"
    font_size: int = 11
    tab_size: int = 4
    use_spaces: bool = True
    word_wrap: bool = False
    show_line_numbers: bool = True
    highlight_current_line: bool = True
    auto_indent: bool = True
    show_whitespace: bool = False
    show_minimap: bool = False
    recent_files: List[str] = field(default_factory=list)
    max_recent_files: int = 15
    window_geometry: str = "1400x900"
    sidebar_width: int = 250

# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM WIDGETS
# ═══════════════════════════════════════════════════════════════════════════════

class LineNumberCanvas(tk.Canvas):
    """Line number display for text widget"""
    
    def __init__(self, master, text_widget, **kwargs):
        super().__init__(master, **kwargs)
        self.text_widget = text_widget
        self.text_font = None
        self.configure(
            bg=THEME.bg_dark,
            highlightthickness=0,
            width=50
        )
        
    def redraw(self):
        """Redraw line numbers"""
        self.delete("all")
        
        if not self.text_font:
            return
            
        # Get visible range
        first_visible = self.text_widget.index("@0,0")
        last_visible = self.text_widget.index(f"@0,{self.winfo_height()}")
        
        first_line = int(first_visible.split(".")[0])
        last_line = int(last_visible.split(".")[0])
        
        # Get current line for highlighting
        cursor_line = int(self.text_widget.index("insert").split(".")[0])
        
        # Calculate line height
        line_height = self.text_font.metrics()["linespace"]
        
        # Draw line numbers
        for line_num in range(first_line, last_line + 1):
            # Get y position
            dline_info = self.text_widget.dlineinfo(f"{line_num}.0")
            if dline_info:
                y = dline_info[1]
                
                # Choose color based on current line
                color = THEME.text_primary if line_num == cursor_line else THEME.text_muted
                
                self.create_text(
                    self.winfo_width() - 8,
                    y + 2,
                    anchor="ne",
                    text=str(line_num),
                    fill=color,
                    font=self.text_font
                )
        
        # Draw separator line
        self.create_line(
            self.winfo_width() - 1, 0,
            self.winfo_width() - 1, self.winfo_height(),
            fill=THEME.bg_light
        )


class SyntaxHighlighter:
    """Syntax highlighting engine"""
    
    def __init__(self, text_widget: tk.Text, language_ext: str = ".txt"):
        self.text_widget = text_widget
        self.language_ext = language_ext
        self._setup_tags()
        
    def _setup_tags(self):
        """Setup text tags for highlighting"""
        tag_configs = {
            "keyword": THEME.syntax_keyword,
            "string": THEME.syntax_string,
            "comment": THEME.syntax_comment,
            "number": THEME.syntax_number,
            "function": THEME.syntax_function,
            "class": THEME.syntax_class,
            "operator": THEME.syntax_operator,
            "decorator": THEME.syntax_decorator,
            "builtin": THEME.syntax_builtin,
            "preprocessor": THEME.syntax_constant,
            "tags": THEME.syntax_function,
            "attributes": THEME.syntax_decorator,
            "entities": THEME.syntax_constant,
            "selectors": THEME.syntax_function,
            "properties": THEME.syntax_keyword,
            "values": THEME.syntax_string,
            "colors": THEME.syntax_constant,
            "keys": THEME.syntax_function,
            "constants": THEME.syntax_constant,
            "headers": THEME.syntax_function,
            "bold": THEME.text_primary,
            "italic": THEME.text_secondary,
            "code": THEME.syntax_string,
            "links": THEME.accent_blue,
            "lists": THEME.syntax_keyword,
            "cmdlets": THEME.syntax_function,
            "variables": THEME.syntax_decorator,
            "cdata": THEME.syntax_comment,
            "annotations": THEME.syntax_decorator,
            "macros": THEME.syntax_constant,
            "lifetimes": THEME.accent_purple,
            "types": THEME.syntax_class,
        }
        
        for tag, color in tag_configs.items():
            self.text_widget.tag_configure(tag, foreground=color)
            
        # Configure bold/italic styles
        current_font = self.text_widget.cget("font")
        if isinstance(current_font, str):
            font_obj = tkfont.nametofont(current_font) if current_font in tkfont.names() else tkfont.Font(font=current_font)
        else:
            font_obj = current_font
            
        bold_font = font_obj.copy()
        bold_font.configure(weight="bold")
        self.text_widget.tag_configure("bold", font=bold_font)
        
    def set_language(self, ext: str):
        """Set the language for highlighting"""
        self.language_ext = ext
        
    def highlight_all(self):
        """Apply syntax highlighting to entire document"""
        # Remove existing tags
        for tag in self.text_widget.tag_names():
            if tag not in ("sel", "current_line"):
                self.text_widget.tag_remove(tag, "1.0", "end")
        
        patterns = SYNTAX_PATTERNS.get(self.language_ext, {})
        if not patterns:
            return
            
        content = self.text_widget.get("1.0", "end-1c")
        
        # Apply patterns in order (comments/strings should be last to override)
        pattern_order = [
            "preprocessor", "keywords", "builtins", "cmdlets", "functions", 
            "classes", "decorators", "annotations", "macros", "operators",
            "numbers", "variables", "lifetimes", "types", "tags", "attributes",
            "selectors", "properties", "values", "colors", "keys", "constants",
            "headers", "bold", "italic", "links", "lists", "entities", "cdata",
            "strings", "comments", "code"
        ]
        
        for pattern_name in pattern_order:
            if pattern_name not in patterns:
                continue
                
            pattern = patterns[pattern_name]
            flags = re.MULTILINE | re.IGNORECASE if pattern_name in ["keywords", "builtins", "constants"] and self.language_ext == ".sql" else re.MULTILINE
            
            try:
                for match in re.finditer(pattern, content, flags):
                    start_idx = f"1.0+{match.start()}c"
                    end_idx = f"1.0+{match.end()}c"
                    self.text_widget.tag_add(pattern_name[:-1] if pattern_name.endswith("s") and pattern_name not in ["strings", "comments", "classes", "colors", "keys", "lists", "constants", "headers", "links", "entities", "values", "properties", "selectors", "attributes", "tags"] else pattern_name, start_idx, end_idx)
            except re.error:
                pass
                
    def highlight_line(self, line_num: int):
        """Highlight a specific line (for incremental updates)"""
        line_start = f"{line_num}.0"
        line_end = f"{line_num}.end"
        
        # Remove tags from this line
        for tag in self.text_widget.tag_names():
            if tag not in ("sel", "current_line"):
                self.text_widget.tag_remove(tag, line_start, line_end)
        
        patterns = SYNTAX_PATTERNS.get(self.language_ext, {})
        if not patterns:
            return
            
        line_content = self.text_widget.get(line_start, line_end)
        line_offset = len(self.text_widget.get("1.0", line_start))
        
        pattern_order = [
            "preprocessor", "keywords", "builtins", "cmdlets", "functions", 
            "classes", "decorators", "annotations", "macros", "operators",
            "numbers", "variables", "lifetimes", "types", "tags", "attributes",
            "selectors", "properties", "values", "colors", "keys", "constants",
            "headers", "bold", "italic", "links", "lists", "entities", "cdata",
            "strings", "comments", "code"
        ]
        
        for pattern_name in pattern_order:
            if pattern_name not in patterns:
                continue
                
            pattern = patterns[pattern_name]
            flags = re.IGNORECASE if pattern_name in ["keywords", "builtins", "constants"] and self.language_ext == ".sql" else 0
            
            try:
                for match in re.finditer(pattern, line_content, flags):
                    start_idx = f"{line_num}.{match.start()}"
                    end_idx = f"{line_num}.{match.end()}"
                    tag_name = pattern_name[:-1] if pattern_name.endswith("s") and pattern_name not in ["strings", "comments", "classes", "colors", "keys", "lists", "constants", "headers", "links", "entities", "values", "properties", "selectors", "attributes", "tags"] else pattern_name
                    self.text_widget.tag_add(tag_name, start_idx, end_idx)
            except re.error:
                pass


class FileTreeView(ctk.CTkFrame):
    """File explorer tree view"""
    
    def __init__(self, master, on_file_select: Callable, **kwargs):
        super().__init__(master, fg_color=THEME.bg_dark, **kwargs)
        
        self.on_file_select = on_file_select
        self.current_path: Optional[Path] = None
        self.expanded_dirs: set = set()
        
        self._create_widgets()
        
    def _create_widgets(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color=THEME.bg_medium, height=36, corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            header_frame,
            text="  EXPLORER",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=THEME.text_secondary,
            anchor="w"
        ).pack(side="left", padx=8, pady=8)
        
        # Folder button
        self.folder_btn = ctk.CTkButton(
            header_frame,
            text="📁",
            width=28,
            height=24,
            fg_color="transparent",
            hover_color=THEME.bg_light,
            command=self._open_folder,
            font=ctk.CTkFont(size=14)
        )
        self.folder_btn.pack(side="right", padx=4, pady=4)
        
        # Tree container with scrollbar
        tree_container = ctk.CTkFrame(self, fg_color=THEME.bg_dark)
        tree_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Create treeview style
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure(
            "FileTree.Treeview",
            background=THEME.bg_dark,
            foreground=THEME.text_secondary,
            fieldbackground=THEME.bg_dark,
            borderwidth=0,
            rowheight=24,
            font=("Segoe UI", 10)
        )
        style.map(
            "FileTree.Treeview",
            background=[("selected", THEME.bg_medium)],
            foreground=[("selected", THEME.text_primary)]
        )
        style.configure(
            "FileTree.Treeview.Heading",
            background=THEME.bg_dark,
            foreground=THEME.text_secondary,
            borderwidth=0
        )
        style.layout("FileTree.Treeview", [("FileTree.Treeview.treearea", {"sticky": "nswe"})])
        
        # Treeview
        self.tree = ttk.Treeview(
            tree_container,
            style="FileTree.Treeview",
            show="tree",
            selectmode="browse"
        )
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(tree_container, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        
        # Bind events
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Return>", self._on_double_click)
        self.tree.bind("<<TreeviewOpen>>", self._on_expand)
        
    def _open_folder(self):
        """Open folder dialog"""
        folder = filedialog.askdirectory()
        if folder:
            self.set_root(folder)
            
    def set_root(self, path: str):
        """Set the root folder for the tree"""
        self.current_path = Path(path)
        self.expanded_dirs.clear()
        
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add root
        root_id = self.tree.insert(
            "",
            "end",
            text=f"📁 {self.current_path.name}",
            values=(str(self.current_path), "folder"),
            open=True
        )
        
        self._populate_directory(root_id, self.current_path)
        
    def _populate_directory(self, parent_id: str, path: Path):
        """Populate a directory in the tree"""
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                # Skip hidden files and common ignore patterns
                if item.name.startswith(".") or item.name in ["__pycache__", "node_modules", ".git", ".venv", "venv"]:
                    continue
                    
                if item.is_dir():
                    dir_id = self.tree.insert(
                        parent_id,
                        "end",
                        text=f"📁 {item.name}",
                        values=(str(item), "folder")
                    )
                    # Add dummy child for expansion arrow
                    self.tree.insert(dir_id, "end", text="Loading...")
                else:
                    # Get file icon based on extension
                    icon = self._get_file_icon(item.suffix.lower())
                    self.tree.insert(
                        parent_id,
                        "end",
                        text=f"{icon} {item.name}",
                        values=(str(item), "file")
                    )
        except PermissionError:
            pass
            
    def _get_file_icon(self, ext: str) -> str:
        """Get icon for file type"""
        icons = {
            ".py": "🐍",
            ".js": "📜",
            ".ts": "📘",
            ".html": "🌐",
            ".css": "🎨",
            ".json": "📋",
            ".md": "📝",
            ".txt": "📄",
            ".xml": "📰",
            ".sql": "🗃️",
            ".sh": "⚙️",
            ".ps1": "💠",
            ".bat": "📦",
            ".c": "©️",
            ".cpp": "➕",
            ".h": "📎",
            ".java": "☕",
            ".go": "🔵",
            ".rs": "🦀",
            ".rb": "💎",
            ".php": "🐘",
            ".swift": "🦅",
            ".kt": "🎯",
            ".yaml": "⚡",
            ".yml": "⚡",
            ".toml": "⚙️",
            ".ini": "⚙️",
            ".cfg": "⚙️",
            ".log": "📋",
            ".csv": "📊",
            ".png": "🖼️",
            ".jpg": "🖼️",
            ".jpeg": "🖼️",
            ".gif": "🖼️",
            ".svg": "🖼️",
            ".ico": "🖼️",
            ".pdf": "📕",
            ".zip": "📦",
            ".rar": "📦",
            ".7z": "📦",
            ".tar": "📦",
            ".gz": "📦",
        }
        return icons.get(ext, "📄")
        
    def _on_expand(self, event):
        """Handle directory expansion"""
        item_id = self.tree.focus()
        values = self.tree.item(item_id, "values")
        
        if values and values[1] == "folder":
            path = Path(values[0])
            
            if str(path) not in self.expanded_dirs:
                # Remove dummy children
                for child in self.tree.get_children(item_id):
                    self.tree.delete(child)
                    
                # Populate with actual contents
                self._populate_directory(item_id, path)
                self.expanded_dirs.add(str(path))
                
    def _on_double_click(self, event):
        """Handle double-click on item"""
        item_id = self.tree.focus()
        values = self.tree.item(item_id, "values")
        
        if values and values[1] == "file":
            self.on_file_select(values[0])


class FindReplaceBar(ctk.CTkFrame):
    """Find and replace toolbar"""
    
    def __init__(self, master, on_find: Callable, on_replace: Callable, on_replace_all: Callable, on_close: Callable, **kwargs):
        super().__init__(master, fg_color=THEME.bg_medium, height=40, corner_radius=0, **kwargs)
        
        self.on_find = on_find
        self.on_replace = on_replace
        self.on_replace_all = on_replace_all
        self.on_close = on_close
        self.state = SearchState()
        
        self.pack_propagate(False)
        self._create_widgets()
        
    def _create_widgets(self):
        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=8, pady=6)
        
        # Find section
        find_frame = ctk.CTkFrame(container, fg_color="transparent")
        find_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            find_frame,
            text="Find:",
            width=60,
            anchor="w",
            text_color=THEME.text_secondary
        ).pack(side="left")
        
        self.find_entry = ctk.CTkEntry(
            find_frame,
            width=300,
            height=28,
            fg_color=THEME.bg_dark,
            border_color=THEME.bg_light,
            text_color=THEME.text_primary,
            placeholder_text="Enter search text..."
        )
        self.find_entry.pack(side="left", padx=4)
        self.find_entry.bind("<Return>", lambda e: self._do_find())
        self.find_entry.bind("<Escape>", lambda e: self.on_close())
        
        # Find buttons
        ctk.CTkButton(
            find_frame,
            text="▲",
            width=28,
            height=28,
            fg_color=THEME.bg_dark,
            hover_color=THEME.bg_light,
            command=lambda: self._do_find(up=True)
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            find_frame,
            text="▼",
            width=28,
            height=28,
            fg_color=THEME.bg_dark,
            hover_color=THEME.bg_light,
            command=lambda: self._do_find(up=False)
        ).pack(side="left", padx=2)
        
        # Options
        self.case_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            find_frame,
            text="Match Case",
            variable=self.case_var,
            width=100,
            height=24,
            fg_color=THEME.accent_blue,
            hover_color=THEME.accent_blue,
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=8)
        
        self.word_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            find_frame,
            text="Whole Word",
            variable=self.word_var,
            width=100,
            height=24,
            fg_color=THEME.accent_blue,
            hover_color=THEME.accent_blue,
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=4)
        
        self.regex_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            find_frame,
            text="Regex",
            variable=self.regex_var,
            width=80,
            height=24,
            fg_color=THEME.accent_blue,
            hover_color=THEME.accent_blue,
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=4)
        
        # Results label
        self.results_label = ctk.CTkLabel(
            find_frame,
            text="",
            text_color=THEME.text_muted,
            font=ctk.CTkFont(size=11)
        )
        self.results_label.pack(side="left", padx=8)
        
        # Close button
        ctk.CTkButton(
            find_frame,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=THEME.bg_light,
            text_color=THEME.text_secondary,
            command=self.on_close
        ).pack(side="right")
        
        # Replace section
        replace_frame = ctk.CTkFrame(container, fg_color="transparent")
        replace_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(
            replace_frame,
            text="Replace:",
            width=60,
            anchor="w",
            text_color=THEME.text_secondary
        ).pack(side="left")
        
        self.replace_entry = ctk.CTkEntry(
            replace_frame,
            width=300,
            height=28,
            fg_color=THEME.bg_dark,
            border_color=THEME.bg_light,
            text_color=THEME.text_primary,
            placeholder_text="Enter replacement text..."
        )
        self.replace_entry.pack(side="left", padx=4)
        self.replace_entry.bind("<Return>", lambda e: self._do_replace())
        
        ctk.CTkButton(
            replace_frame,
            text="Replace",
            width=70,
            height=28,
            fg_color=THEME.bg_dark,
            hover_color=THEME.bg_light,
            command=self._do_replace
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            replace_frame,
            text="Replace All",
            width=85,
            height=28,
            fg_color=THEME.bg_dark,
            hover_color=THEME.bg_light,
            command=self._do_replace_all
        ).pack(side="left", padx=2)
        
    def _do_find(self, up=False):
        """Execute find"""
        self.state.find_text = self.find_entry.get()
        self.state.match_case = self.case_var.get()
        self.state.whole_word = self.word_var.get()
        self.state.use_regex = self.regex_var.get()
        self.state.search_up = up
        
        result = self.on_find(self.state)
        if result:
            self.results_label.configure(text=result)
            
    def _do_replace(self):
        """Execute replace"""
        self.state.replace_text = self.replace_entry.get()
        self._do_find()
        self.on_replace(self.state)
        
    def _do_replace_all(self):
        """Execute replace all"""
        self.state.find_text = self.find_entry.get()
        self.state.replace_text = self.replace_entry.get()
        self.state.match_case = self.case_var.get()
        self.state.whole_word = self.word_var.get()
        self.state.use_regex = self.regex_var.get()
        
        result = self.on_replace_all(self.state)
        if result:
            self.results_label.configure(text=result)
            
    def focus_find(self):
        """Focus the find entry"""
        self.find_entry.focus_set()
        self.find_entry.select_range(0, "end")
        
    def set_find_text(self, text: str):
        """Set the find text"""
        self.find_entry.delete(0, "end")
        self.find_entry.insert(0, text)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class NotepadPlus(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize state
        self.settings = EditorSettings()
        self.tabs: Dict[str, TabData] = {}  # tab_id -> TabData
        self.current_tab: Optional[str] = None
        self.text_widgets: Dict[str, tk.Text] = {}
        self.line_numbers: Dict[str, LineNumberCanvas] = {}
        self.highlighters: Dict[str, SyntaxHighlighter] = {}
        self.find_bar_visible = False
        
        # Configure window
        self.title("Notepad Plus")
        self.geometry(self.settings.window_geometry)
        self.configure(fg_color=THEME.bg_darkest)
        
        # Set icon (Windows)
        try:
            self.iconbitmap(default="")
        except:
            pass
            
        # Load settings
        self._load_settings()
        
        # Create UI
        self._create_menu()
        self._create_toolbar()
        self._create_main_layout()
        self._create_statusbar()
        
        # Bind shortcuts
        self._bind_shortcuts()
        
        # Create initial tab
        self._new_file()
        
        # Protocol handlers
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _load_settings(self):
        """Load settings from file"""
        settings_path = Path.home() / ".notepad_plus_settings.json"
        if settings_path.exists():
            try:
                with open(settings_path, "r") as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self.settings, key):
                            setattr(self.settings, key, value)
            except:
                pass
                
    def _save_settings(self):
        """Save settings to file"""
        settings_path = Path.home() / ".notepad_plus_settings.json"
        try:
            data = {
                "font_family": self.settings.font_family,
                "font_size": self.settings.font_size,
                "tab_size": self.settings.tab_size,
                "use_spaces": self.settings.use_spaces,
                "word_wrap": self.settings.word_wrap,
                "show_line_numbers": self.settings.show_line_numbers,
                "highlight_current_line": self.settings.highlight_current_line,
                "auto_indent": self.settings.auto_indent,
                "recent_files": self.settings.recent_files[-self.settings.max_recent_files:],
                "window_geometry": self.geometry(),
                "sidebar_width": self.settings.sidebar_width,
            }
            with open(settings_path, "w") as f:
                json.dump(data, f, indent=2)
        except:
            pass
            
    def _create_menu(self):
        """Create menu bar"""
        self.menu_bar = tk.Menu(self, bg=THEME.bg_dark, fg=THEME.text_primary, 
                                activebackground=THEME.bg_medium, activeforeground=THEME.text_primary,
                                borderwidth=0)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME.bg_dark, fg=THEME.text_primary,
                           activebackground=THEME.bg_medium, activeforeground=THEME.text_primary)
        file_menu.add_command(label="New                    Ctrl+N", command=self._new_file)
        file_menu.add_command(label="Open                   Ctrl+O", command=self._open_file)
        file_menu.add_command(label="Save                   Ctrl+S", command=self._save_file)
        file_menu.add_command(label="Save As            Ctrl+Shift+S", command=self._save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab              Ctrl+W", command=self._close_current_tab)
        file_menu.add_command(label="Close All Tabs", command=self._close_all_tabs)
        file_menu.add_separator()
        
        # Recent files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0, bg=THEME.bg_dark, fg=THEME.text_primary,
                                   activebackground=THEME.bg_medium, activeforeground=THEME.text_primary)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self._update_recent_menu()
        
        file_menu.add_separator()
        file_menu.add_command(label="Exit                   Alt+F4", command=self._on_close)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME.bg_dark, fg=THEME.text_primary,
                           activebackground=THEME.bg_medium, activeforeground=THEME.text_primary)
        edit_menu.add_command(label="Undo                   Ctrl+Z", command=self._undo)
        edit_menu.add_command(label="Redo                   Ctrl+Y", command=self._redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut                    Ctrl+X", command=self._cut)
        edit_menu.add_command(label="Copy                   Ctrl+C", command=self._copy)
        edit_menu.add_command(label="Paste                  Ctrl+V", command=self._paste)
        edit_menu.add_command(label="Delete", command=self._delete)
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All             Ctrl+A", command=self._select_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find                   Ctrl+F", command=self._show_find_bar)
        edit_menu.add_command(label="Replace                Ctrl+H", command=self._show_find_bar)
        edit_menu.add_command(label="Go to Line             Ctrl+G", command=self._goto_line)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME.bg_dark, fg=THEME.text_primary,
                           activebackground=THEME.bg_medium, activeforeground=THEME.text_primary)
        
        self.word_wrap_var = tk.BooleanVar(value=self.settings.word_wrap)
        view_menu.add_checkbutton(label="Word Wrap", variable=self.word_wrap_var, command=self._toggle_word_wrap)
        
        self.line_numbers_var = tk.BooleanVar(value=self.settings.show_line_numbers)
        view_menu.add_checkbutton(label="Line Numbers", variable=self.line_numbers_var, command=self._toggle_line_numbers)
        
        self.current_line_var = tk.BooleanVar(value=self.settings.highlight_current_line)
        view_menu.add_checkbutton(label="Highlight Current Line", variable=self.current_line_var, command=self._toggle_current_line)
        
        view_menu.add_separator()
        view_menu.add_command(label="Zoom In                Ctrl++", command=self._zoom_in)
        view_menu.add_command(label="Zoom Out               Ctrl+-", command=self._zoom_out)
        view_menu.add_command(label="Reset Zoom             Ctrl+0", command=self._zoom_reset)
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Sidebar         Ctrl+B", command=self._toggle_sidebar)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        
        # Language menu
        lang_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME.bg_dark, fg=THEME.text_primary,
                           activebackground=THEME.bg_medium, activeforeground=THEME.text_primary)
        
        languages = sorted(set(FILE_EXTENSIONS.values()))
        for lang in languages:
            lang_menu.add_command(label=lang, command=lambda l=lang: self._set_language(l))
            
        self.menu_bar.add_cascade(label="Language", menu=lang_menu)
        
        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0, bg=THEME.bg_dark, fg=THEME.text_primary,
                           activebackground=THEME.bg_medium, activeforeground=THEME.text_primary)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.configure(menu=self.menu_bar)
        
    def _update_recent_menu(self):
        """Update recent files menu"""
        self.recent_menu.delete(0, "end")
        
        if not self.settings.recent_files:
            self.recent_menu.add_command(label="(No recent files)", state="disabled")
        else:
            for filepath in self.settings.recent_files[-10:]:
                display_name = os.path.basename(filepath)
                self.recent_menu.add_command(
                    label=f"{display_name}  ({filepath})",
                    command=lambda f=filepath: self._open_file(f)
                )
            self.recent_menu.add_separator()
            self.recent_menu.add_command(label="Clear Recent Files", command=self._clear_recent)
            
    def _clear_recent(self):
        """Clear recent files"""
        self.settings.recent_files.clear()
        self._update_recent_menu()
        self._save_settings()
        
    def _create_toolbar(self):
        """Create toolbar"""
        self.toolbar = ctk.CTkFrame(self, fg_color=THEME.bg_dark, height=40, corner_radius=0)
        self.toolbar.pack(fill="x", padx=0, pady=0)
        self.toolbar.pack_propagate(False)
        
        # Left buttons
        left_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        left_frame.pack(side="left", padx=8, pady=4)
        
        toolbar_buttons = [
            ("📄", "New (Ctrl+N)", self._new_file),
            ("📂", "Open (Ctrl+O)", self._open_file),
            ("💾", "Save (Ctrl+S)", self._save_file),
            ("|", None, None),
            ("↩️", "Undo (Ctrl+Z)", self._undo),
            ("↪️", "Redo (Ctrl+Y)", self._redo),
            ("|", None, None),
            ("✂️", "Cut (Ctrl+X)", self._cut),
            ("📋", "Copy (Ctrl+C)", self._copy),
            ("📥", "Paste (Ctrl+V)", self._paste),
            ("|", None, None),
            ("🔍", "Find (Ctrl+F)", self._show_find_bar),
        ]
        
        for text, tooltip, command in toolbar_buttons:
            if text == "|":
                separator = ctk.CTkFrame(left_frame, width=1, height=24, fg_color=THEME.bg_light)
                separator.pack(side="left", padx=6)
            else:
                btn = ctk.CTkButton(
                    left_frame,
                    text=text,
                    width=32,
                    height=28,
                    fg_color="transparent",
                    hover_color=THEME.bg_medium,
                    command=command,
                    font=ctk.CTkFont(size=14)
                )
                btn.pack(side="left", padx=1)
                
        # Right side - zoom controls
        right_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        right_frame.pack(side="right", padx=8, pady=4)
        
        ctk.CTkButton(
            right_frame,
            text="−",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=THEME.bg_medium,
            command=self._zoom_out,
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=1)
        
        self.zoom_label = ctk.CTkLabel(
            right_frame,
            text="100%",
            width=50,
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=11)
        )
        self.zoom_label.pack(side="left", padx=4)
        
        ctk.CTkButton(
            right_frame,
            text="+",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=THEME.bg_medium,
            command=self._zoom_in,
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=1)
        
    def _create_main_layout(self):
        """Create main layout with sidebar and editor"""
        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color=THEME.bg_darkest, corner_radius=0)
        self.main_container.pack(fill="both", expand=True)
        
        # Sidebar (File Explorer)
        self.sidebar = FileTreeView(
            self.main_container,
            on_file_select=self._open_file,
            width=self.settings.sidebar_width
        )
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        
        # Editor container
        self.editor_container = ctk.CTkFrame(self.main_container, fg_color=THEME.bg_darkest, corner_radius=0)
        self.editor_container.pack(side="left", fill="both", expand=True)
        
        # Tab bar
        self.tab_bar = ctk.CTkFrame(self.editor_container, fg_color=THEME.bg_dark, height=36, corner_radius=0)
        self.tab_bar.pack(fill="x", padx=0, pady=0)
        self.tab_bar.pack_propagate(False)
        
        self.tab_container = ctk.CTkFrame(self.tab_bar, fg_color="transparent")
        self.tab_container.pack(side="left", fill="both", expand=True)
        
        # New tab button
        ctk.CTkButton(
            self.tab_bar,
            text="+",
            width=32,
            height=28,
            fg_color="transparent",
            hover_color=THEME.bg_medium,
            text_color=THEME.text_secondary,
            command=self._new_file,
            font=ctk.CTkFont(size=16)
        ).pack(side="right", padx=4, pady=4)
        
        # Find/Replace bar (hidden by default)
        self.find_bar = FindReplaceBar(
            self.editor_container,
            on_find=self._do_find,
            on_replace=self._do_replace,
            on_replace_all=self._do_replace_all,
            on_close=self._hide_find_bar
        )
        
        # Editor notebook frame
        self.editor_frame = ctk.CTkFrame(self.editor_container, fg_color=THEME.bg_darkest, corner_radius=0)
        self.editor_frame.pack(fill="both", expand=True)
        
    def _create_statusbar(self):
        """Create status bar"""
        self.statusbar = ctk.CTkFrame(self, fg_color=THEME.bg_dark, height=24, corner_radius=0)
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)
        
        # Left side - file info
        left_frame = ctk.CTkFrame(self.statusbar, fg_color="transparent")
        left_frame.pack(side="left", fill="y", padx=8)
        
        self.status_label = ctk.CTkLabel(
            left_frame,
            text="Ready",
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=10)
        )
        self.status_label.pack(side="left", pady=4)
        
        # Right side - cursor position and language
        right_frame = ctk.CTkFrame(self.statusbar, fg_color="transparent")
        right_frame.pack(side="right", fill="y", padx=8)
        
        self.language_label = ctk.CTkLabel(
            right_frame,
            text="Plain Text",
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=10),
            width=100
        )
        self.language_label.pack(side="right", padx=8, pady=4)
        
        separator = ctk.CTkFrame(right_frame, width=1, height=16, fg_color=THEME.bg_light)
        separator.pack(side="right", padx=8)
        
        self.encoding_label = ctk.CTkLabel(
            right_frame,
            text="UTF-8",
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=10),
            width=60
        )
        self.encoding_label.pack(side="right", padx=4, pady=4)
        
        separator2 = ctk.CTkFrame(right_frame, width=1, height=16, fg_color=THEME.bg_light)
        separator2.pack(side="right", padx=8)
        
        self.position_label = ctk.CTkLabel(
            right_frame,
            text="Ln 1, Col 1",
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=10),
            width=100
        )
        self.position_label.pack(side="right", pady=4)
        
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.bind("<Control-n>", lambda e: self._new_file())
        self.bind("<Control-o>", lambda e: self._open_file())
        self.bind("<Control-s>", lambda e: self._save_file())
        self.bind("<Control-Shift-S>", lambda e: self._save_file_as())
        self.bind("<Control-w>", lambda e: self._close_current_tab())
        self.bind("<Control-f>", lambda e: self._show_find_bar())
        self.bind("<Control-h>", lambda e: self._show_find_bar())
        self.bind("<Control-g>", lambda e: self._goto_line())
        self.bind("<Control-plus>", lambda e: self._zoom_in())
        self.bind("<Control-equal>", lambda e: self._zoom_in())
        self.bind("<Control-minus>", lambda e: self._zoom_out())
        self.bind("<Control-0>", lambda e: self._zoom_reset())
        self.bind("<Control-b>", lambda e: self._toggle_sidebar())
        self.bind("<Escape>", lambda e: self._hide_find_bar())
        
    def _create_tab(self, filepath: Optional[str] = None, content: str = "") -> str:
        """Create a new editor tab"""
        import uuid
        tab_id = str(uuid.uuid4())
        
        # Determine language
        if filepath:
            ext = Path(filepath).suffix.lower()
            language = FILE_EXTENSIONS.get(ext, "Plain Text")
        else:
            ext = ".txt"
            language = "Plain Text"
            
        # Create tab data
        self.tabs[tab_id] = TabData(
            filepath=filepath,
            language=language,
            content_hash=hashlib.md5(content.encode()).hexdigest()
        )
        
        # Create editor frame
        editor_frame = ctk.CTkFrame(self.editor_frame, fg_color=THEME.bg_darkest, corner_radius=0)
        editor_frame.tab_id = tab_id
        
        # Create text widget with line numbers
        text_container = ctk.CTkFrame(editor_frame, fg_color=THEME.bg_darkest, corner_radius=0)
        text_container.pack(fill="both", expand=True)
        
        # Line numbers
        line_canvas = LineNumberCanvas(text_container, None)
        if self.settings.show_line_numbers:
            line_canvas.pack(side="left", fill="y")
            
        # Text widget
        text_widget = tk.Text(
            text_container,
            bg=THEME.bg_darkest,
            fg=THEME.text_primary,
            insertbackground=THEME.text_primary,
            selectbackground=THEME.selection_bg,
            selectforeground=THEME.text_primary,
            font=(self.settings.font_family, self.settings.font_size),
            wrap="none" if not self.settings.word_wrap else "word",
            undo=True,
            maxundo=-1,
            autoseparators=True,
            borderwidth=0,
            highlightthickness=0,
            padx=8,
            pady=8,
            tabs=(f"{self.settings.tab_size * 8}p",)
        )
        text_widget.pack(side="left", fill="both", expand=True)
        
        # Link line numbers to text widget
        line_canvas.text_widget = text_widget
        line_canvas.text_font = tkfont.Font(family=self.settings.font_family, size=self.settings.font_size)
        
        # Scrollbars
        v_scrollbar = ctk.CTkScrollbar(text_container, command=text_widget.yview)
        v_scrollbar.pack(side="right", fill="y")
        
        h_scrollbar = ctk.CTkScrollbar(editor_frame, command=text_widget.xview, orientation="horizontal")
        if not self.settings.word_wrap:
            h_scrollbar.pack(side="bottom", fill="x")
            
        text_widget.configure(
            yscrollcommand=lambda *args: self._on_scroll(v_scrollbar, line_canvas, *args),
            xscrollcommand=h_scrollbar.set
        )
        
        # Current line highlighting
        text_widget.tag_configure("current_line", background=THEME.current_line)
        
        # Create highlighter
        highlighter = SyntaxHighlighter(text_widget, ext)
        
        # Insert content
        if content:
            text_widget.insert("1.0", content)
            text_widget.edit_reset()
            text_widget.edit_modified(False)
            
        # Bind events
        text_widget.bind("<KeyRelease>", lambda e: self._on_text_changed(tab_id))
        text_widget.bind("<ButtonRelease-1>", lambda e: self._update_cursor_position(tab_id))
        text_widget.bind("<KeyRelease>", lambda e: self._update_cursor_position(tab_id), add=True)
        text_widget.bind("<Tab>", lambda e: self._handle_tab(tab_id, e))
        text_widget.bind("<Return>", lambda e: self._handle_return(tab_id, e))
        
        # Store references
        self.text_widgets[tab_id] = text_widget
        self.line_numbers[tab_id] = line_canvas
        self.highlighters[tab_id] = highlighter
        editor_frame.h_scrollbar = h_scrollbar
        editor_frame.v_scrollbar = v_scrollbar
        editor_frame.text_container = text_container
        
        # Create tab button
        self._create_tab_button(tab_id)
        
        # Apply syntax highlighting
        self.after(100, lambda: self._highlight_all(tab_id))
        
        # Switch to new tab
        self._switch_to_tab(tab_id)
        
        return tab_id
        
    def _create_tab_button(self, tab_id: str):
        """Create tab button in tab bar"""
        tab_data = self.tabs[tab_id]
        
        # Get display name
        if tab_data.filepath:
            display_name = os.path.basename(tab_data.filepath)
        else:
            # Count untitled tabs
            untitled_count = sum(1 for t in self.tabs.values() if t.filepath is None)
            display_name = f"Untitled-{untitled_count}"
            
        # Tab frame
        tab_frame = ctk.CTkFrame(self.tab_container, fg_color=THEME.tab_inactive, corner_radius=4)
        tab_frame.pack(side="left", padx=2, pady=4)
        tab_frame.tab_id = tab_id
        
        # Modified indicator
        modified_label = ctk.CTkLabel(
            tab_frame,
            text="",
            width=8,
            text_color=THEME.tab_modified,
            font=ctk.CTkFont(size=10)
        )
        modified_label.pack(side="left", padx=(8, 0))
        tab_frame.modified_label = modified_label
        
        # Tab label
        tab_label = ctk.CTkLabel(
            tab_frame,
            text=display_name,
            text_color=THEME.text_secondary,
            font=ctk.CTkFont(size=11),
            cursor="hand2"
        )
        tab_label.pack(side="left", padx=4, pady=4)
        tab_frame.label = tab_label
        
        # Close button
        close_btn = ctk.CTkButton(
            tab_frame,
            text="×",
            width=20,
            height=20,
            fg_color="transparent",
            hover_color=THEME.bg_light,
            text_color=THEME.text_muted,
            command=lambda: self._close_tab(tab_id),
            font=ctk.CTkFont(size=14)
        )
        close_btn.pack(side="right", padx=(0, 4))
        
        # Bind click to switch tab
        tab_label.bind("<Button-1>", lambda e: self._switch_to_tab(tab_id))
        tab_frame.bind("<Button-1>", lambda e: self._switch_to_tab(tab_id))
        
        # Store reference
        tab_frame.close_btn = close_btn
        self.tabs[tab_id].tab_frame = tab_frame
        
    def _switch_to_tab(self, tab_id: str):
        """Switch to a specific tab"""
        if tab_id not in self.tabs:
            return
            
        # Hide current tab's editor
        if self.current_tab and self.current_tab in self.text_widgets:
            for widget in self.editor_frame.winfo_children():
                if hasattr(widget, "tab_id") and widget.tab_id == self.current_tab:
                    widget.pack_forget()
                    
            # Update old tab appearance
            if hasattr(self.tabs[self.current_tab], "tab_frame"):
                self.tabs[self.current_tab].tab_frame.configure(fg_color=THEME.tab_inactive)
                self.tabs[self.current_tab].tab_frame.label.configure(text_color=THEME.text_secondary)
                
        # Show new tab's editor
        for widget in self.editor_frame.winfo_children():
            if hasattr(widget, "tab_id") and widget.tab_id == tab_id:
                widget.pack(fill="both", expand=True)
                break
        else:
            # Editor frame doesn't exist, need to recreate (shouldn't happen)
            pass
            
        # Update new tab appearance
        if hasattr(self.tabs[tab_id], "tab_frame"):
            self.tabs[tab_id].tab_frame.configure(fg_color=THEME.tab_active)
            self.tabs[tab_id].tab_frame.label.configure(text_color=THEME.text_primary)
            
        self.current_tab = tab_id
        
        # Update status bar
        self._update_statusbar()
        
        # Focus text widget
        if tab_id in self.text_widgets:
            self.text_widgets[tab_id].focus_set()
            self._update_line_numbers(tab_id)
            
    def _close_tab(self, tab_id: str) -> bool:
        """Close a tab, returns False if cancelled"""
        if tab_id not in self.tabs:
            return True
            
        tab_data = self.tabs[tab_id]
        
        # Check for unsaved changes
        if tab_data.modified:
            filename = os.path.basename(tab_data.filepath) if tab_data.filepath else "Untitled"
            result = messagebox.askyesnocancel(
                "Save Changes",
                f"Do you want to save changes to {filename}?"
            )
            if result is None:  # Cancel
                return False
            elif result:  # Yes
                if not self._save_file():
                    return False
                    
        # Remove tab button
        if hasattr(tab_data, "tab_frame"):
            tab_data.tab_frame.destroy()
            
        # Remove editor frame
        for widget in self.editor_frame.winfo_children():
            if hasattr(widget, "tab_id") and widget.tab_id == tab_id:
                widget.destroy()
                break
                
        # Remove references
        del self.tabs[tab_id]
        if tab_id in self.text_widgets:
            del self.text_widgets[tab_id]
        if tab_id in self.line_numbers:
            del self.line_numbers[tab_id]
        if tab_id in self.highlighters:
            del self.highlighters[tab_id]
            
        # Switch to another tab or create new one
        if self.current_tab == tab_id:
            if self.tabs:
                self._switch_to_tab(list(self.tabs.keys())[-1])
            else:
                self._new_file()
                
        return True
        
    def _close_current_tab(self):
        """Close the current tab"""
        if self.current_tab:
            self._close_tab(self.current_tab)
            
    def _close_all_tabs(self):
        """Close all tabs"""
        tab_ids = list(self.tabs.keys())
        for tab_id in tab_ids:
            if not self._close_tab(tab_id):
                break
                
    def _on_scroll(self, scrollbar, line_canvas, *args):
        """Handle scroll events"""
        scrollbar.set(*args)
        line_canvas.redraw()
        
    def _on_text_changed(self, tab_id: str):
        """Handle text change events"""
        if tab_id not in self.tabs:
            return
            
        text_widget = self.text_widgets[tab_id]
        tab_data = self.tabs[tab_id]
        
        # Check if modified
        current_content = text_widget.get("1.0", "end-1c")
        current_hash = hashlib.md5(current_content.encode()).hexdigest()
        
        was_modified = tab_data.modified
        tab_data.modified = current_hash != tab_data.content_hash
        
        # Update tab indicator
        if hasattr(tab_data, "tab_frame") and was_modified != tab_data.modified:
            tab_data.tab_frame.modified_label.configure(text="●" if tab_data.modified else "")
            
        # Update line numbers
        self._update_line_numbers(tab_id)
        
        # Update current line highlight
        self._highlight_current_line(tab_id)
        
        # Incremental syntax highlighting
        self._highlight_current_line_syntax(tab_id)
        
    def _update_line_numbers(self, tab_id: str):
        """Update line numbers display"""
        if tab_id in self.line_numbers:
            self.line_numbers[tab_id].redraw()
            
    def _highlight_current_line(self, tab_id: str):
        """Highlight the current line"""
        if not self.settings.highlight_current_line:
            return
            
        if tab_id not in self.text_widgets:
            return
            
        text_widget = self.text_widgets[tab_id]
        
        # Remove previous highlight
        text_widget.tag_remove("current_line", "1.0", "end")
        
        # Add highlight to current line
        line = text_widget.index("insert").split(".")[0]
        text_widget.tag_add("current_line", f"{line}.0", f"{line}.end+1c")
        text_widget.tag_lower("current_line")
        
    def _highlight_current_line_syntax(self, tab_id: str):
        """Apply syntax highlighting to current line"""
        if tab_id not in self.highlighters:
            return
            
        text_widget = self.text_widgets[tab_id]
        line_num = int(text_widget.index("insert").split(".")[0])
        self.highlighters[tab_id].highlight_line(line_num)
        
    def _highlight_all(self, tab_id: str):
        """Apply syntax highlighting to entire document"""
        if tab_id not in self.highlighters:
            return
            
        self.highlighters[tab_id].highlight_all()
        self._update_line_numbers(tab_id)
        
    def _update_cursor_position(self, tab_id: str):
        """Update cursor position in status bar"""
        if tab_id not in self.text_widgets:
            return
            
        text_widget = self.text_widgets[tab_id]
        pos = text_widget.index("insert")
        line, col = pos.split(".")
        
        self.position_label.configure(text=f"Ln {line}, Col {int(col) + 1}")
        self._highlight_current_line(tab_id)
        self._update_line_numbers(tab_id)
        
    def _update_statusbar(self):
        """Update status bar information"""
        if not self.current_tab or self.current_tab not in self.tabs:
            return
            
        tab_data = self.tabs[self.current_tab]
        
        # Update language
        self.language_label.configure(text=tab_data.language)
        
        # Update encoding
        self.encoding_label.configure(text=tab_data.encoding.upper())
        
        # Update position
        self._update_cursor_position(self.current_tab)
        
    def _handle_tab(self, tab_id: str, event) -> str:
        """Handle tab key press"""
        text_widget = self.text_widgets[tab_id]
        
        if self.settings.use_spaces:
            # Insert spaces instead of tab
            text_widget.insert("insert", " " * self.settings.tab_size)
            return "break"
            
        return None
        
    def _handle_return(self, tab_id: str, event) -> str:
        """Handle return key press for auto-indent"""
        if not self.settings.auto_indent:
            return None
            
        text_widget = self.text_widgets[tab_id]
        
        # Get current line's indentation
        line = text_widget.get("insert linestart", "insert")
        indent = ""
        for char in line:
            if char in " \t":
                indent += char
            else:
                break
                
        # Check if line ends with colon (Python) or opening brace
        stripped = line.rstrip()
        if stripped.endswith(":") or stripped.endswith("{") or stripped.endswith("[") or stripped.endswith("("):
            if self.settings.use_spaces:
                indent += " " * self.settings.tab_size
            else:
                indent += "\t"
                
        # Insert newline with indentation
        text_widget.insert("insert", "\n" + indent)
        return "break"
        
    # ═══════════════════════════════════════════════════════════════════════════
    # FILE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _new_file(self):
        """Create a new file"""
        self._create_tab()
        
    def _open_file(self, filepath: Optional[str] = None):
        """Open a file"""
        if filepath is None:
            filetypes = [
                ("All Files", "*.*"),
                ("Text Files", "*.txt"),
                ("Python Files", "*.py"),
                ("JavaScript Files", "*.js"),
                ("HTML Files", "*.html"),
                ("CSS Files", "*.css"),
                ("JSON Files", "*.json"),
                ("Markdown Files", "*.md"),
            ]
            filepath = filedialog.askopenfilename(filetypes=filetypes)
            
        if not filepath:
            return
            
        # Check if file is already open
        for tab_id, tab_data in self.tabs.items():
            if tab_data.filepath == filepath:
                self._switch_to_tab(tab_id)
                return
                
        # Read file
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(filepath, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file:\n{e}")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{e}")
            return
            
        # Create tab
        self._create_tab(filepath, content)
        
        # Add to recent files
        if filepath not in self.settings.recent_files:
            self.settings.recent_files.append(filepath)
            self._update_recent_menu()
            self._save_settings()
            
        # Set folder in sidebar
        folder = os.path.dirname(filepath)
        if folder and not self.sidebar.current_path:
            self.sidebar.set_root(folder)
            
        self.status_label.configure(text=f"Opened: {os.path.basename(filepath)}")
        
    def _save_file(self) -> bool:
        """Save current file"""
        if not self.current_tab:
            return False
            
        tab_data = self.tabs[self.current_tab]
        
        if tab_data.filepath is None:
            return self._save_file_as()
            
        return self._save_to_path(tab_data.filepath)
        
    def _save_file_as(self) -> bool:
        """Save current file with new name"""
        if not self.current_tab:
            return False
            
        filetypes = [
            ("All Files", "*.*"),
            ("Text Files", "*.txt"),
            ("Python Files", "*.py"),
            ("JavaScript Files", "*.js"),
            ("HTML Files", "*.html"),
            ("CSS Files", "*.css"),
            ("JSON Files", "*.json"),
            ("Markdown Files", "*.md"),
        ]
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=filetypes
        )
        
        if not filepath:
            return False
            
        return self._save_to_path(filepath)
        
    def _save_to_path(self, filepath: str) -> bool:
        """Save to specific path"""
        if not self.current_tab:
            return False
            
        text_widget = self.text_widgets[self.current_tab]
        tab_data = self.tabs[self.current_tab]
        
        try:
            content = text_widget.get("1.0", "end-1c")
            with open(filepath, "w", encoding=tab_data.encoding) as f:
                f.write(content)
                
            # Update tab data
            tab_data.filepath = filepath
            tab_data.content_hash = hashlib.md5(content.encode()).hexdigest()
            tab_data.modified = False
            
            # Update language based on extension
            ext = Path(filepath).suffix.lower()
            tab_data.language = FILE_EXTENSIONS.get(ext, "Plain Text")
            
            # Update highlighter
            if self.current_tab in self.highlighters:
                self.highlighters[self.current_tab].set_language(ext)
                self._highlight_all(self.current_tab)
                
            # Update tab label
            if hasattr(tab_data, "tab_frame"):
                tab_data.tab_frame.label.configure(text=os.path.basename(filepath))
                tab_data.tab_frame.modified_label.configure(text="")
                
            # Update status bar
            self._update_statusbar()
            
            # Add to recent files
            if filepath not in self.settings.recent_files:
                self.settings.recent_files.append(filepath)
                self._update_recent_menu()
                
            self._save_settings()
            self.status_label.configure(text=f"Saved: {os.path.basename(filepath)}")
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")
            return False
            
    # ═══════════════════════════════════════════════════════════════════════════
    # EDIT OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _undo(self):
        """Undo last action"""
        if self.current_tab and self.current_tab in self.text_widgets:
            try:
                self.text_widgets[self.current_tab].edit_undo()
            except:
                pass
                
    def _redo(self):
        """Redo last undone action"""
        if self.current_tab and self.current_tab in self.text_widgets:
            try:
                self.text_widgets[self.current_tab].edit_redo()
            except:
                pass
                
    def _cut(self):
        """Cut selected text"""
        if self.current_tab and self.current_tab in self.text_widgets:
            text_widget = self.text_widgets[self.current_tab]
            try:
                text_widget.event_generate("<<Cut>>")
            except:
                pass
                
    def _copy(self):
        """Copy selected text"""
        if self.current_tab and self.current_tab in self.text_widgets:
            text_widget = self.text_widgets[self.current_tab]
            try:
                text_widget.event_generate("<<Copy>>")
            except:
                pass
                
    def _paste(self):
        """Paste from clipboard"""
        if self.current_tab and self.current_tab in self.text_widgets:
            text_widget = self.text_widgets[self.current_tab]
            try:
                text_widget.event_generate("<<Paste>>")
            except:
                pass
                
    def _delete(self):
        """Delete selected text"""
        if self.current_tab and self.current_tab in self.text_widgets:
            text_widget = self.text_widgets[self.current_tab]
            try:
                text_widget.delete("sel.first", "sel.last")
            except:
                pass
                
    def _select_all(self):
        """Select all text"""
        if self.current_tab and self.current_tab in self.text_widgets:
            text_widget = self.text_widgets[self.current_tab]
            text_widget.tag_add("sel", "1.0", "end")
            
    # ═══════════════════════════════════════════════════════════════════════════
    # FIND/REPLACE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _show_find_bar(self):
        """Show find/replace bar"""
        if not self.find_bar_visible:
            self.find_bar.pack(fill="x", before=self.editor_frame)
            self.find_bar_visible = True
            
        # Set selected text as search term
        if self.current_tab and self.current_tab in self.text_widgets:
            text_widget = self.text_widgets[self.current_tab]
            try:
                selected = text_widget.get("sel.first", "sel.last")
                if selected:
                    self.find_bar.set_find_text(selected)
            except:
                pass
                
        self.find_bar.focus_find()
        
    def _hide_find_bar(self):
        """Hide find/replace bar"""
        if self.find_bar_visible:
            self.find_bar.pack_forget()
            self.find_bar_visible = False
            
            if self.current_tab and self.current_tab in self.text_widgets:
                self.text_widgets[self.current_tab].focus_set()
                
    def _do_find(self, state: SearchState) -> str:
        """Execute find operation"""
        if not self.current_tab or not state.find_text:
            return ""
            
        text_widget = self.text_widgets[self.current_tab]
        
        # Remove previous highlights
        text_widget.tag_remove("search_highlight", "1.0", "end")
        text_widget.tag_remove("search_current", "1.0", "end")
        
        # Build search pattern
        pattern = state.find_text
        if not state.use_regex:
            pattern = re.escape(pattern)
        if state.whole_word:
            pattern = r'\b' + pattern + r'\b'
            
        flags = re.MULTILINE
        if not state.match_case:
            flags |= re.IGNORECASE
            
        # Find all matches
        content = text_widget.get("1.0", "end-1c")
        matches = list(re.finditer(pattern, content, flags))
        
        if not matches:
            return "No results"
            
        # Highlight all matches
        text_widget.tag_configure("search_highlight", background=THEME.bg_light)
        text_widget.tag_configure("search_current", background=THEME.accent_blue)
        
        for match in matches:
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            text_widget.tag_add("search_highlight", start_idx, end_idx)
            
        # Find current match based on cursor position
        cursor_pos = text_widget.index("insert")
        cursor_offset = len(text_widget.get("1.0", cursor_pos))
        
        current_idx = 0
        if state.search_up:
            for i, match in enumerate(matches):
                if match.start() < cursor_offset:
                    current_idx = i
                else:
                    break
        else:
            for i, match in enumerate(matches):
                if match.start() >= cursor_offset:
                    current_idx = i
                    break
            else:
                current_idx = 0
                
        # Highlight current match
        match = matches[current_idx]
        start_idx = f"1.0+{match.start()}c"
        end_idx = f"1.0+{match.end()}c"
        text_widget.tag_remove("search_highlight", start_idx, end_idx)
        text_widget.tag_add("search_current", start_idx, end_idx)
        
        # Move cursor and scroll to match
        text_widget.mark_set("insert", start_idx)
        text_widget.see(start_idx)
        
        return f"{current_idx + 1} of {len(matches)}"
        
    def _do_replace(self, state: SearchState):
        """Execute replace operation"""
        if not self.current_tab or not state.find_text:
            return
            
        text_widget = self.text_widgets[self.current_tab]
        
        # Check if there's a current selection matching the search
        try:
            sel_start = text_widget.index("sel.first")
            sel_end = text_widget.index("sel.last")
            selected = text_widget.get(sel_start, sel_end)
            
            # Check if selection matches search pattern
            pattern = state.find_text
            if not state.use_regex:
                pattern = re.escape(pattern)
            if state.whole_word:
                pattern = r'\b' + pattern + r'\b'
                
            flags = 0 if state.match_case else re.IGNORECASE
            if re.fullmatch(pattern, selected, flags):
                # Replace selection
                text_widget.delete(sel_start, sel_end)
                text_widget.insert(sel_start, state.replace_text)
                
        except tk.TclError:
            pass
            
        # Find next
        self._do_find(state)
        
    def _do_replace_all(self, state: SearchState) -> str:
        """Execute replace all operation"""
        if not self.current_tab or not state.find_text:
            return ""
            
        text_widget = self.text_widgets[self.current_tab]
        
        # Build search pattern
        pattern = state.find_text
        if not state.use_regex:
            pattern = re.escape(pattern)
        if state.whole_word:
            pattern = r'\b' + pattern + r'\b'
            
        flags = re.MULTILINE
        if not state.match_case:
            flags |= re.IGNORECASE
            
        # Get content and replace
        content = text_widget.get("1.0", "end-1c")
        new_content, count = re.subn(pattern, state.replace_text, content, flags=flags)
        
        if count > 0:
            # Replace content
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", new_content)
            
            # Re-highlight
            self._highlight_all(self.current_tab)
            
        return f"Replaced {count} occurrences"
        
    def _goto_line(self):
        """Go to specific line number"""
        if not self.current_tab:
            return
            
        dialog = ctk.CTkInputDialog(
            text="Enter line number:",
            title="Go to Line"
        )
        result = dialog.get_input()
        
        if result:
            try:
                line_num = int(result)
                text_widget = self.text_widgets[self.current_tab]
                text_widget.mark_set("insert", f"{line_num}.0")
                text_widget.see(f"{line_num}.0")
                self._update_cursor_position(self.current_tab)
            except ValueError:
                pass
                
    # ═══════════════════════════════════════════════════════════════════════════
    # VIEW OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _toggle_word_wrap(self):
        """Toggle word wrap"""
        self.settings.word_wrap = self.word_wrap_var.get()
        
        for tab_id, text_widget in self.text_widgets.items():
            text_widget.configure(wrap="word" if self.settings.word_wrap else "none")
            
            # Show/hide horizontal scrollbar
            for widget in self.editor_frame.winfo_children():
                if hasattr(widget, "tab_id") and widget.tab_id == tab_id:
                    if self.settings.word_wrap:
                        widget.h_scrollbar.pack_forget()
                    else:
                        widget.h_scrollbar.pack(side="bottom", fill="x")
                        
        self._save_settings()
        
    def _toggle_line_numbers(self):
        """Toggle line numbers"""
        self.settings.show_line_numbers = self.line_numbers_var.get()
        
        for tab_id, line_canvas in self.line_numbers.items():
            if self.settings.show_line_numbers:
                line_canvas.pack(side="left", fill="y", before=self.text_widgets[tab_id])
            else:
                line_canvas.pack_forget()
                
        self._save_settings()
        
    def _toggle_current_line(self):
        """Toggle current line highlighting"""
        self.settings.highlight_current_line = self.current_line_var.get()
        
        if self.current_tab:
            if self.settings.highlight_current_line:
                self._highlight_current_line(self.current_tab)
            else:
                self.text_widgets[self.current_tab].tag_remove("current_line", "1.0", "end")
                
        self._save_settings()
        
    def _toggle_sidebar(self):
        """Toggle sidebar visibility"""
        if self.sidebar.winfo_viewable():
            self.sidebar.pack_forget()
        else:
            self.sidebar.pack(side="left", fill="y", before=self.editor_container)
            
    def _zoom_in(self):
        """Increase font size"""
        self.settings.font_size = min(self.settings.font_size + 2, 48)
        self._apply_font_size()
        
    def _zoom_out(self):
        """Decrease font size"""
        self.settings.font_size = max(self.settings.font_size - 2, 6)
        self._apply_font_size()
        
    def _zoom_reset(self):
        """Reset font size to default"""
        self.settings.font_size = 11
        self._apply_font_size()
        
    def _apply_font_size(self):
        """Apply font size to all editors"""
        font = (self.settings.font_family, self.settings.font_size)
        
        for text_widget in self.text_widgets.values():
            text_widget.configure(font=font)
            
        for line_canvas in self.line_numbers.values():
            line_canvas.text_font = tkfont.Font(family=self.settings.font_family, size=self.settings.font_size)
            line_canvas.redraw()
            
        # Update zoom label
        zoom_percent = int((self.settings.font_size / 11) * 100)
        self.zoom_label.configure(text=f"{zoom_percent}%")
        
        self._save_settings()
        
    def _set_language(self, language: str):
        """Set language for current tab"""
        if not self.current_tab:
            return
            
        tab_data = self.tabs[self.current_tab]
        tab_data.language = language
        
        # Find extension for language
        ext = ".txt"
        for e, l in FILE_EXTENSIONS.items():
            if l == language:
                ext = e
                break
                
        # Update highlighter
        if self.current_tab in self.highlighters:
            self.highlighters[self.current_tab].set_language(ext)
            self._highlight_all(self.current_tab)
            
        self._update_statusbar()
        
    # ═══════════════════════════════════════════════════════════════════════════
    # DIALOGS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Notepad Plus",
            "Notepad Plus v1.0\n\n"
            "A Notepad++ inspired text editor\n"
            "Built with Python and CustomTkinter\n\n"
            "Features:\n"
            "• Syntax highlighting for 20+ languages\n"
            "• Multi-tab editing\n"
            "• Find and replace with regex\n"
            "• File explorer sidebar\n"
            "• Customizable themes\n"
            "• Auto-indent and more"
        )
        
    def _show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts = """
Keyboard Shortcuts:

File:
  Ctrl+N          New file
  Ctrl+O          Open file
  Ctrl+S          Save file
  Ctrl+Shift+S    Save as
  Ctrl+W          Close tab

Edit:
  Ctrl+Z          Undo
  Ctrl+Y          Redo
  Ctrl+X          Cut
  Ctrl+C          Copy
  Ctrl+V          Paste
  Ctrl+A          Select all
  Ctrl+F          Find
  Ctrl+H          Find and replace
  Ctrl+G          Go to line

View:
  Ctrl++          Zoom in
  Ctrl+-          Zoom out
  Ctrl+0          Reset zoom
  Ctrl+B          Toggle sidebar
  Escape          Close find bar
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
        
    def _on_close(self):
        """Handle window close"""
        # Check for unsaved changes
        for tab_id in list(self.tabs.keys()):
            if not self._close_tab(tab_id):
                return
                
        self._save_settings()
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    # Set appearance
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create and run app
    app = NotepadPlus()
    app.mainloop()


if __name__ == "__main__":
    main()
