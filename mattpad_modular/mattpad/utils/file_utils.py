"""File utilities for Mattpad."""
import os
from typing import Optional, Tuple

# Try to import chardet for encoding detection
try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False


# File extension to language mapping
FILE_EXTENSIONS = {
    ".py": "Python", ".pyw": "Python", ".pyi": "Python",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".sass": "SASS", ".less": "LESS",
    ".json": "JSON", ".jsonc": "JSON",
    ".xml": "XML", ".xsl": "XML", ".xslt": "XML",
    ".yaml": "YAML", ".yml": "YAML",
    ".md": "Markdown", ".markdown": "Markdown",
    ".sql": "SQL",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".ps1": "PowerShell", ".psm1": "PowerShell", ".psd1": "PowerShell",
    ".bat": "Batch", ".cmd": "Batch",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".hpp": "C++", ".cc": "C++", ".cxx": "C++",
    ".cs": "C#",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin", ".kts": "Kotlin",
    ".r": "R", ".R": "R",
    ".lua": "Lua",
    ".pl": "Perl", ".pm": "Perl",
    ".ini": "INI", ".cfg": "INI", ".conf": "INI",
    ".toml": "TOML",
    ".txt": "Plain Text",
    ".log": "Plain Text",
    ".csv": "CSV",
    ".tsv": "CSV",
}

# File icons by extension/type
FILE_ICONS = {
    ".py": "🐍", ".pyw": "🐍", ".pyi": "🐍",
    ".js": "📜", ".mjs": "📜", ".cjs": "📜", ".jsx": "⚛",
    ".ts": "📘", ".tsx": "⚛",
    ".html": "🌐", ".htm": "🌐",
    ".css": "🎨", ".scss": "🎨", ".sass": "🎨", ".less": "🎨",
    ".json": "📋", ".jsonc": "📋",
    ".xml": "📄", ".xsl": "📄",
    ".yaml": "⚙", ".yml": "⚙",
    ".md": "📝", ".markdown": "📝",
    ".sql": "🗃",
    ".sh": "💻", ".bash": "💻", ".zsh": "💻",
    ".ps1": "💠", ".psm1": "💠", ".psd1": "💠",
    ".bat": "⚡", ".cmd": "⚡",
    ".c": "©", ".h": "©",
    ".cpp": "➕", ".hpp": "➕", ".cc": "➕",
    ".cs": "♯",
    ".java": "☕",
    ".go": "🔵",
    ".rs": "🦀",
    ".rb": "💎",
    ".php": "🐘",
    ".swift": "🕊",
    ".kt": "🅺", ".kts": "🅺",
    ".r": "📊", ".R": "📊",
    ".lua": "🌙",
    ".txt": "📄",
    ".log": "📋",
    ".csv": "📊", ".tsv": "📊",
    ".ini": "⚙", ".cfg": "⚙", ".conf": "⚙",
    ".toml": "⚙",
    ".gitignore": "🚫",
    ".env": "🔐",
    ".dockerfile": "🐳",
    "dockerfile": "🐳",
}

# Folder icons
FOLDER_ICONS = {
    "src": "📁", "source": "📁",
    "lib": "📚", "libs": "📚",
    "test": "🧪", "tests": "🧪", "__tests__": "🧪",
    "doc": "📖", "docs": "📖", "documentation": "📖",
    "build": "🔨", "dist": "📦", "out": "📦",
    "node_modules": "📦",
    ".git": "🔀",
    ".vscode": "💻",
    ".idea": "💡",
    "config": "⚙", "configs": "⚙",
    "public": "🌐", "static": "🌐",
    "assets": "🎨", "images": "🖼", "img": "🖼",
    "scripts": "📜",
    "bin": "⚡",
    "__pycache__": "🗑",
    ".cache": "💾",
}


def get_file_icon(filepath: Optional[str]) -> str:
    """Get icon for a file based on extension."""
    if not filepath:
        return "📄"
    
    basename = os.path.basename(filepath).lower()
    ext = os.path.splitext(filepath)[1].lower()
    
    # Check full filename first
    if basename in FILE_ICONS:
        return FILE_ICONS[basename]
    
    # Then check extension
    return FILE_ICONS.get(ext, "📄")


def get_folder_icon(foldername: str) -> str:
    """Get icon for a folder based on name."""
    name = foldername.lower()
    return FOLDER_ICONS.get(name, "📁")


def detect_line_ending(content: str) -> str:
    """Detect line ending style in content."""
    crlf = content.count("\r\n")
    lf = content.count("\n") - crlf
    cr = content.count("\r") - crlf
    
    if crlf >= lf and crlf >= cr:
        return "CRLF"
    elif lf >= cr:
        return "LF"
    else:
        return "CR"


def normalize_line_endings(content: str, target: str = "CRLF") -> str:
    """Normalize line endings to target format."""
    # First normalize to LF
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    
    if target == "CRLF":
        return content.replace("\n", "\r\n")
    elif target == "CR":
        return content.replace("\n", "\r")
    else:  # LF
        return content


def detect_encoding(filepath: str) -> str:
    """Detect file encoding using chardet if available."""
    if not CHARDET_AVAILABLE:
        return "utf-8"
    
    try:
        with open(filepath, 'rb') as f:
            raw = f.read(65536)  # Read first 64KB
        result = chardet.detect(raw)
        encoding = result.get('encoding', 'utf-8')
        confidence = result.get('confidence', 0)
        
        # Use detected encoding only if confidence is high
        if confidence > 0.7 and encoding:
            return encoding.lower()
    except Exception:
        pass
    
    return "utf-8"


def read_file_safe(filepath: str, encoding: Optional[str] = None) -> Tuple[str, str]:
    """
    Read file with encoding detection and fallback.
    
    Returns:
        Tuple of (content, detected_encoding)
    """
    if encoding is None:
        encoding = detect_encoding(filepath)
    
    # Try detected encoding first
    encodings_to_try = [encoding, 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    
    for enc in encodings_to_try:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
            return content, enc
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception:
            break
    
    # Last resort: read as binary and decode with replacement
    try:
        with open(filepath, 'rb') as f:
            content = f.read().decode('utf-8', errors='replace')
        return content, 'utf-8'
    except Exception as e:
        raise IOError(f"Could not read file: {e}")


def write_file_safe(filepath: str, content: str, encoding: str = "utf-8", 
                    line_ending: str = "CRLF") -> None:
    """Write file with specified encoding and line ending."""
    # Normalize line endings
    content = normalize_line_endings(content, line_ending)
    
    # Write file
    with open(filepath, 'w', encoding=encoding, newline='') as f:
        f.write(content)


def get_language_from_extension(filepath: str) -> str:
    """Get programming language from file extension."""
    if not filepath:
        return "Plain Text"
    ext = os.path.splitext(filepath)[1].lower()
    return FILE_EXTENSIONS.get(ext, "Plain Text")


def is_binary_file(filepath: str) -> bool:
    """Check if a file is binary."""
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(8192)
        # Check for null bytes
        if b'\x00' in chunk:
            return True
        # Check for high ratio of non-text characters
        text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
        non_text = len(chunk.translate(None, text_chars))
        return non_text / len(chunk) > 0.30 if chunk else False
    except Exception:
        return False
