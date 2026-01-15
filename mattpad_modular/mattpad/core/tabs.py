"""Tab data management."""
from dataclasses import dataclass, field
from typing import Optional, Set, Any


@dataclass
class TabData:
    """Data for a single editor tab."""
    tab_id: str
    filepath: Optional[str] = None
    modified: bool = False
    language: str = "Plain Text"
    encoding: str = "utf-8"
    line_ending: str = "CRLF"
    content_hash: str = ""
    is_large_file: bool = False
    
    # Bookmarks and folds
    bookmarks: Set[int] = field(default_factory=set)
    folds: Set[int] = field(default_factory=set)
    
    # UI references (set by app)
    tab_frame: Any = None
    
    @property
    def display_name(self) -> str:
        """Get display name for tab."""
        import os
        if self.filepath:
            return os.path.basename(self.filepath)
        return "Untitled"
    
    @property
    def tooltip(self) -> str:
        """Get tooltip text for tab."""
        if self.filepath:
            return self.filepath
        return "Untitled"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "tab_id": self.tab_id,
            "filepath": self.filepath,
            "modified": self.modified,
            "language": self.language,
            "encoding": self.encoding,
            "line_ending": self.line_ending,
            "bookmarks": list(self.bookmarks),
            "folds": list(self.folds),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TabData':
        """Create TabData from dictionary."""
        bookmarks = set(data.get("bookmarks", []))
        folds = set(data.get("folds", []))
        return cls(
            tab_id=data.get("tab_id", ""),
            filepath=data.get("filepath"),
            modified=data.get("modified", False),
            language=data.get("language", "Plain Text"),
            encoding=data.get("encoding", "utf-8"),
            line_ending=data.get("line_ending", "CRLF"),
            bookmarks=bookmarks,
            folds=folds,
        )
