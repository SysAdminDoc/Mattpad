"""Syntax highlighting for Mattpad."""
import re
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk

from ..utils.themes import THEME


class SyntaxHighlighter:
    """Syntax highlighting with viewport-only processing for large files."""
    
    PATTERNS = {
        "Python": {
            "keyword": r"\b(def|class|if|elif|else|for|while|try|except|finally|with|as|import|from|return|yield|break|continue|pass|raise|and|or|not|in|is|lambda|global|nonlocal|async|await|True|False|None|self)\b",
            "string": r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|f"[^"\\]*(?:\\.[^"\\]*)*"|f\'[^\'\\]*(?:\\.[^\'\\]*)*\'|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')',
            "comment": r"#.*$",
            "number": r"\b\d+\.?\d*\b",
            "function": r"\b([a-zA-Z_]\w*)\s*(?=\()",
            "decorator": r"@\w+",
        },
        "JavaScript": {
            "keyword": r"\b(const|let|var|function|return|if|else|for|while|do|switch|case|break|continue|new|this|class|extends|super|import|export|default|from|async|await|try|catch|finally|throw|typeof|instanceof|in|of|null|undefined|true|false)\b",
            "string": r'(`[^`]*`|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')',
            "comment": r"(//.*$|/\*[\s\S]*?\*/)",
            "number": r"\b\d+\.?\d*\b",
            "function": r"\b([a-zA-Z_$]\w*)\s*(?=\()",
        },
        "TypeScript": {
            "keyword": r"\b(const|let|var|function|return|if|else|for|while|do|switch|case|break|continue|new|this|class|extends|super|import|export|default|from|async|await|try|catch|finally|throw|typeof|instanceof|in|of|null|undefined|true|false|interface|type|enum|implements|public|private|protected|readonly|static|abstract|as|is|keyof|never|unknown|any|void|string|number|boolean|symbol|bigint)\b",
            "string": r'(`[^`]*`|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')',
            "comment": r"(//.*$|/\*[\s\S]*?\*/)",
            "number": r"\b\d+\.?\d*\b",
            "function": r"\b([a-zA-Z_$]\w*)\s*(?=\()",
        },
        "HTML": {
            "tag": r"</?[a-zA-Z][a-zA-Z0-9]*",
            "attribute": r'\b([a-zA-Z-]+)=',
            "string": r'"[^"]*"|\'[^\']*\'',
            "comment": r"<!--[\s\S]*?-->",
        },
        "CSS": {
            "selector": r"[.#]?[a-zA-Z_-][\w-]*(?=\s*[{,])",
            "property": r"\b([a-zA-Z-]+)\s*:",
            "value": r":\s*([^;{}]+)",
            "comment": r"/\*[\s\S]*?\*/",
            "number": r"\b\d+\.?\d*(px|em|rem|%|vh|vw|pt|cm|mm|in)?\b",
        },
        "JSON": {
            "key": r'"[^"]*"\s*(?=:)',
            "string": r'"[^"\\]*(?:\\.[^"\\]*)*"',
            "number": r"\b-?\d+\.?\d*([eE][+-]?\d+)?\b",
            "keyword": r"\b(true|false|null)\b",
        },
        "Markdown": {
            "header": r"^#{1,6}\s+.*$",
            "bold": r"\*\*[^*]+\*\*|__[^_]+__",
            "italic": r"\*[^*]+\*|_[^_]+_",
            "code": r"`[^`]+`",
            "link": r"\[[^\]]+\]\([^)]+\)",
            "list": r"^[\s]*[-*+]\s+",
        },
        "SQL": {
            "keyword": r"\b(SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TABLE|INDEX|VIEW|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AND|OR|NOT|IN|IS|NULL|AS|ORDER|BY|GROUP|HAVING|LIMIT|OFFSET|UNION|ALL|DISTINCT|COUNT|SUM|AVG|MAX|MIN|CASE|WHEN|THEN|ELSE|END|PRIMARY|KEY|FOREIGN|REFERENCES|CONSTRAINT|DEFAULT|AUTO_INCREMENT|INT|VARCHAR|TEXT|BOOLEAN|DATE|DATETIME|TIMESTAMP|FLOAT|DOUBLE|DECIMAL)\b",
            "string": r"'[^']*'",
            "comment": r"(--.*$|/\*[\s\S]*?\*/)",
            "number": r"\b\d+\.?\d*\b",
        },
        "Shell": {
            "keyword": r"\b(if|then|else|elif|fi|for|while|do|done|case|esac|function|return|exit|echo|read|export|source|alias|cd|pwd|ls|mkdir|rm|cp|mv|cat|grep|sed|awk|find|xargs|pipe|sudo|chmod|chown)\b",
            "string": r'("([^"\\]|\\.)*"|\'[^\']*\')',
            "comment": r"#.*$",
            "variable": r"\$[a-zA-Z_]\w*|\$\{[^}]+\}",
            "number": r"\b\d+\b",
        },
        "PowerShell": {
            "keyword": r"\b(if|else|elseif|switch|foreach|for|while|do|until|break|continue|return|function|param|begin|process|end|try|catch|finally|throw|trap|exit|Write-Host|Write-Output|Get-|Set-|New-|Remove-|Import-|Export-|Invoke-|Start-|Stop-|Test-|Add-|Clear-|Select-|Where-Object|ForEach-Object|Sort-Object|Group-Object)\b",
            "string": r'("([^"\\]|\\.)*"|\'[^\']*\'|@"[\s\S]*?"@|@\'[\s\S]*?\'@)',
            "comment": r"(#.*$|<#[\s\S]*?#>)",
            "variable": r"\$[a-zA-Z_]\w*",
            "number": r"\b\d+\.?\d*\b",
        },
        "C": {
            "keyword": r"\b(auto|break|case|char|const|continue|default|do|double|else|enum|extern|float|for|goto|if|int|long|register|return|short|signed|sizeof|static|struct|switch|typedef|union|unsigned|void|volatile|while|NULL)\b",
            "string": r'"[^"\\]*(?:\\.[^"\\]*)*"',
            "comment": r"(//.*$|/\*[\s\S]*?\*/)",
            "number": r"\b\d+\.?\d*[fFlLuU]*\b",
            "preprocessor": r"#\s*\w+",
        },
        "C++": {
            "keyword": r"\b(alignas|alignof|and|and_eq|asm|auto|bitand|bitor|bool|break|case|catch|char|char16_t|char32_t|class|compl|const|constexpr|const_cast|continue|decltype|default|delete|do|double|dynamic_cast|else|enum|explicit|export|extern|false|float|for|friend|goto|if|inline|int|long|mutable|namespace|new|noexcept|not|not_eq|nullptr|operator|or|or_eq|private|protected|public|register|reinterpret_cast|return|short|signed|sizeof|static|static_assert|static_cast|struct|switch|template|this|thread_local|throw|true|try|typedef|typeid|typename|union|unsigned|using|virtual|void|volatile|wchar_t|while|xor|xor_eq)\b",
            "string": r'"[^"\\]*(?:\\.[^"\\]*)*"',
            "comment": r"(//.*$|/\*[\s\S]*?\*/)",
            "number": r"\b\d+\.?\d*[fFlLuU]*\b",
            "preprocessor": r"#\s*\w+",
        },
        "Java": {
            "keyword": r"\b(abstract|assert|boolean|break|byte|case|catch|char|class|const|continue|default|do|double|else|enum|extends|final|finally|float|for|goto|if|implements|import|instanceof|int|interface|long|native|new|null|package|private|protected|public|return|short|static|strictfp|super|switch|synchronized|this|throw|throws|transient|try|void|volatile|while|true|false)\b",
            "string": r'"[^"\\]*(?:\\.[^"\\]*)*"',
            "comment": r"(//.*$|/\*[\s\S]*?\*/)",
            "number": r"\b\d+\.?\d*[fFdDlL]?\b",
            "annotation": r"@\w+",
        },
        "Go": {
            "keyword": r"\b(break|case|chan|const|continue|default|defer|else|fallthrough|for|func|go|goto|if|import|interface|map|package|range|return|select|struct|switch|type|var|nil|true|false|iota)\b",
            "string": r'(`[^`]*`|"[^"\\]*(?:\\.[^"\\]*)*")',
            "comment": r"(//.*$|/\*[\s\S]*?\*/)",
            "number": r"\b\d+\.?\d*\b",
            "function": r"\b([a-zA-Z_]\w*)\s*(?=\()",
        },
        "Rust": {
            "keyword": r"\b(as|async|await|break|const|continue|crate|dyn|else|enum|extern|false|fn|for|if|impl|in|let|loop|match|mod|move|mut|pub|ref|return|self|Self|static|struct|super|trait|true|type|unsafe|use|where|while)\b",
            "string": r'(r#*"[^"]*"#*|"[^"\\]*(?:\\.[^"\\]*)*")',
            "comment": r"(//.*$|/\*[\s\S]*?\*/)",
            "number": r"\b\d+\.?\d*([fiu](8|16|32|64|128|size))?\b",
            "lifetime": r"'\w+",
            "macro": r"\w+!",
        },
        "YAML": {
            "key": r"^[\s]*[a-zA-Z_][a-zA-Z0-9_-]*(?=\s*:)",
            "string": r'"[^"]*"|\'[^\']*\'',
            "comment": r"#.*$",
            "number": r"\b\d+\.?\d*\b",
            "keyword": r"\b(true|false|null|yes|no|on|off)\b",
        },
    }
    
    # Language aliases
    LANGUAGE_MAP = {
        ".py": "Python", ".pyw": "Python", ".pyi": "Python",
        ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".jsx": "JavaScript",
        ".ts": "TypeScript", ".tsx": "TypeScript",
        ".html": "HTML", ".htm": "HTML",
        ".css": "CSS", ".scss": "CSS", ".sass": "CSS", ".less": "CSS",
        ".json": "JSON", ".jsonc": "JSON",
        ".md": "Markdown", ".markdown": "Markdown",
        ".sql": "SQL",
        ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
        ".ps1": "PowerShell", ".psm1": "PowerShell", ".psd1": "PowerShell",
        ".c": "C", ".h": "C",
        ".cpp": "C++", ".hpp": "C++", ".cc": "C++", ".cxx": "C++",
        ".java": "Java",
        ".go": "Go",
        ".rs": "Rust",
        ".yaml": "YAML", ".yml": "YAML",
    }
    
    def __init__(self, text_widget: 'tk.Text', extension: str = ".txt"):
        self.text_widget = text_widget
        self.extension = extension.lower()
        self.language = self.LANGUAGE_MAP.get(self.extension, "Plain Text")
        self.large_file_mode = False
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._setup_tags()
        self._compile_patterns()
    
    def _setup_tags(self):
        """Configure syntax highlighting tags."""
        self.text_widget.tag_configure("keyword", foreground=THEME.syntax_keyword)
        self.text_widget.tag_configure("string", foreground=THEME.syntax_string)
        self.text_widget.tag_configure("comment", foreground=THEME.syntax_comment)
        self.text_widget.tag_configure("number", foreground=THEME.syntax_number)
        self.text_widget.tag_configure("function", foreground=THEME.syntax_function)
        self.text_widget.tag_configure("class", foreground=THEME.syntax_class)
        self.text_widget.tag_configure("decorator", foreground=THEME.syntax_decorator)
        self.text_widget.tag_configure("variable", foreground=THEME.syntax_variable)
        self.text_widget.tag_configure("operator", foreground=THEME.syntax_operator)
        self.text_widget.tag_configure("preprocessor", foreground=THEME.syntax_decorator)
        self.text_widget.tag_configure("tag", foreground=THEME.syntax_keyword)
        self.text_widget.tag_configure("attribute", foreground=THEME.syntax_function)
        self.text_widget.tag_configure("selector", foreground=THEME.syntax_function)
        self.text_widget.tag_configure("property", foreground=THEME.syntax_keyword)
        self.text_widget.tag_configure("value", foreground=THEME.syntax_string)
        self.text_widget.tag_configure("key", foreground=THEME.syntax_keyword)
        self.text_widget.tag_configure("header", foreground=THEME.syntax_keyword, font=("", 0, "bold"))
        self.text_widget.tag_configure("bold", font=("", 0, "bold"))
        self.text_widget.tag_configure("italic", font=("", 0, "italic"))
        self.text_widget.tag_configure("code", foreground=THEME.syntax_string)
        self.text_widget.tag_configure("link", foreground=THEME.accent_secondary, underline=True)
        self.text_widget.tag_configure("list", foreground=THEME.syntax_keyword)
        self.text_widget.tag_configure("lifetime", foreground=THEME.syntax_decorator)
        self.text_widget.tag_configure("macro", foreground=THEME.syntax_function)
        self.text_widget.tag_configure("annotation", foreground=THEME.syntax_decorator)
    
    def _compile_patterns(self):
        """Compile regex patterns for current language."""
        patterns = self.PATTERNS.get(self.language, {})
        self._compiled_patterns = {}
        for tag, pattern in patterns.items():
            try:
                self._compiled_patterns[tag] = re.compile(pattern, re.MULTILINE)
            except re.error:
                pass
    
    def set_language(self, language: str):
        """Change the highlighting language."""
        if language in self.PATTERNS:
            self.language = language
            self._compile_patterns()
    
    def set_large_file_mode(self, enabled: bool):
        """Enable/disable large file mode (viewport-only highlighting)."""
        self.large_file_mode = enabled
    
    def highlight(self, start: str = "1.0", end: str = "end"):
        """Apply syntax highlighting."""
        if not self._compiled_patterns:
            return
        
        # Clear existing tags
        for tag in self._compiled_patterns:
            self.text_widget.tag_remove(tag, start, end)
        
        # Get text to highlight
        try:
            if self.large_file_mode:
                # Only highlight visible viewport
                start = self.text_widget.index("@0,0")
                end = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}")
            
            content = self.text_widget.get(start, end)
        except Exception:
            return
        
        # Apply patterns
        for tag, pattern in self._compiled_patterns.items():
            for match in pattern.finditer(content):
                try:
                    match_start = f"{start}+{match.start()}c"
                    match_end = f"{start}+{match.end()}c"
                    self.text_widget.tag_add(tag, match_start, match_end)
                except Exception:
                    pass
    
    def highlight_line(self, line: int):
        """Highlight a single line."""
        start = f"{line}.0"
        end = f"{line}.end"
        self.highlight(start, end)
    
    def highlight_visible(self):
        """Highlight only the visible portion of the text."""
        try:
            start = self.text_widget.index("@0,0")
            end = self.text_widget.index(f"@0,{self.text_widget.winfo_height()}")
            self.highlight(start, end)
        except Exception:
            pass
