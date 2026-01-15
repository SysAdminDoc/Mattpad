"""Spellcheck functionality for Mattpad."""
import re
import os
import threading
from pathlib import Path
from typing import Set, List, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import spellchecker
SPELLCHECK_AVAILABLE = False
_EXTERNAL_SPELLCHECK = False

try:
    from spellchecker import SpellChecker as ExternalSpellChecker
    _EXTERNAL_SPELLCHECK = True
    SPELLCHECK_AVAILABLE = True
except ImportError:
    ExternalSpellChecker = None


# App directory for dictionary
APP_DIR = Path.home() / ".mattpad"
DICTIONARY_DIR = APP_DIR / "dictionary"
DICTIONARY_DIR.mkdir(parents=True, exist_ok=True)


class SpellCheckManager:
    """Spell checking with embedded fallback dictionary."""
    
    # Common code words to ignore
    CODE_WORDS = {
        "def", "elif", "func", "init", "args", "kwargs", "str", "int", "bool",
        "dict", "len", "const", "var", "async", "await", "enum", "impl", "struct",
        "println", "printf", "scanf", "malloc", "sizeof", "typedef", "namespace",
        "iostream", "vector", "nullptr", "decltype", "constexpr", "noexcept",
        "http", "https", "www", "html", "css", "json", "xml", "yaml", "sql",
        "api", "url", "uri", "src", "dst", "tmp", "cfg", "config", "env",
        "btn", "img", "div", "nav", "svg", "png", "jpg", "gif", "pdf",
        "app", "db", "ui", "ux", "cli", "gui", "sdk", "ide", "vcs", "git",
        "io", "os", "sys", "util", "utils", "lib", "libs", "pkg", "dep",
        "req", "res", "ctx", "msg", "err", "cmd", "arg", "opt", "val",
        "idx", "ptr", "ref", "obj", "cls", "fn", "cb", "evt", "attr",
        # Common tech terms
        "localhost", "github", "gitlab", "bitbucket", "npm", "pip", "conda",
        "docker", "kubernetes", "nginx", "apache", "redis", "mongodb", "mysql",
        "postgres", "sqlite", "graphql", "restful", "webhook", "oauth",
        "jwt", "csrf", "cors", "ssl", "tls", "ssh", "ftp", "tcp", "udp",
        "rgb", "hex", "rgba", "hsla", "px", "em", "rem", "vh", "vw",
        # Programming patterns
        "todo", "fixme", "hack", "xxx", "bugfix", "hotfix", "refactor",
        "deprecated", "readonly", "nullable", "nonnull", "override",
    }
    
    # Embedded basic dictionary (loaded on first use)
    _embedded_words: Optional[Set[str]] = None
    _custom_words: Set[str] = set()
    _external_checker = None
    
    def __init__(self):
        self._load_custom_dictionary()
    
    @classmethod
    def _get_embedded_words(cls) -> Set[str]:
        """Get embedded word list, loading if necessary."""
        if cls._embedded_words is None:
            cls._embedded_words = cls._load_embedded_dictionary()
        return cls._embedded_words
    
    @staticmethod
    def _load_embedded_dictionary() -> Set[str]:
        """Load embedded dictionary from file or create minimal set."""
        words = set()
        dict_file = DICTIONARY_DIR / "words.txt"
        
        # Try to load from file
        if dict_file.exists():
            try:
                content = dict_file.read_text(encoding='utf-8')
                words = set(w.strip().lower() for w in content.split('\n') if w.strip())
                logger.info(f"Loaded {len(words)} words from dictionary file")
                return words
            except Exception as e:
                logger.error(f"Error loading dictionary: {e}")
        
        # Try to download from web
        try:
            import requests
            urls = [
                "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt",
                "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-no-swears.txt",
            ]
            for url in urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        content = response.text
                        words = set(w.strip().lower() for w in content.split('\n') 
                                   if w.strip() and len(w.strip()) > 1)
                        # Save for next time
                        dict_file.write_text('\n'.join(sorted(words)), encoding='utf-8')
                        logger.info(f"Downloaded {len(words)} words from {url}")
                        return words
                except Exception:
                    continue
        except ImportError:
            pass
        
        # Minimal fallback - common words
        return {
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
            "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
            "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
            "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
            "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
            "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
            "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
            "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
            "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
            "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
            "is", "are", "was", "were", "been", "being", "has", "had", "having", "does",
            "did", "doing", "done", "should", "would", "could", "might", "must", "shall",
            "will", "may", "can", "need", "dare", "ought", "used", "able", "going",
        }
    
    def _load_custom_dictionary(self):
        """Load user's custom dictionary."""
        custom_file = DICTIONARY_DIR / "custom.txt"
        if custom_file.exists():
            try:
                content = custom_file.read_text(encoding='utf-8')
                self._custom_words = set(w.strip().lower() for w in content.split('\n') if w.strip())
            except Exception:
                pass
    
    def _save_custom_dictionary(self):
        """Save user's custom dictionary."""
        custom_file = DICTIONARY_DIR / "custom.txt"
        try:
            custom_file.write_text('\n'.join(sorted(self._custom_words)), encoding='utf-8')
        except Exception:
            pass
    
    def is_correct(self, word: str) -> bool:
        """Check if a word is spelled correctly."""
        if not word or len(word) < 2 or not word.isalpha():
            return True
        
        word_lower = word.lower()
        
        # Check code words first
        if word_lower in self.CODE_WORDS:
            return True
        
        # Check custom dictionary
        if word_lower in self._custom_words:
            return True
        
        # Try external spellchecker
        if _EXTERNAL_SPELLCHECK and self._external_checker is None:
            try:
                self._external_checker = ExternalSpellChecker()
            except Exception:
                pass
        
        if self._external_checker:
            try:
                return word_lower in self._external_checker
            except Exception:
                pass
        
        # Fall back to embedded dictionary
        return word_lower in self._get_embedded_words()
    
    def get_suggestions(self, word: str, max_suggestions: int = 5) -> List[str]:
        """Get spelling suggestions for a word."""
        if not word:
            return []
        
        word_lower = word.lower()
        suggestions = []
        
        # Try external spellchecker first
        if self._external_checker:
            try:
                candidates = self._external_checker.candidates(word_lower)
                if candidates:
                    suggestions = list(candidates)[:max_suggestions]
            except Exception:
                pass
        
        if not suggestions:
            # Simple Levenshtein-based suggestions from embedded dictionary
            words = self._get_embedded_words()
            scored = []
            for w in words:
                if abs(len(w) - len(word_lower)) <= 2:
                    dist = self._levenshtein_distance(word_lower, w)
                    if dist <= 2:
                        scored.append((dist, w))
            scored.sort(key=lambda x: x[0])
            suggestions = [w for _, w in scored[:max_suggestions]]
        
        return suggestions
    
    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return SpellCheckManager._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def add_word(self, word: str):
        """Add word to custom dictionary."""
        if word and len(word) >= 2:
            self._custom_words.add(word.lower())
            self._save_custom_dictionary()
    
    def remove_word(self, word: str):
        """Remove word from custom dictionary."""
        self._custom_words.discard(word.lower())
        self._save_custom_dictionary()
    
    def get_custom_words(self) -> List[str]:
        """Get list of custom dictionary words."""
        return sorted(self._custom_words)
    
    def check_text(self, text: str) -> List[tuple]:
        """
        Check text for misspellings.
        Returns list of (word, start_pos, end_pos) tuples for misspelled words.
        """
        misspelled = []
        # Match words (alphanumeric sequences)
        pattern = re.compile(r'\b[a-zA-Z]+\b')
        for match in pattern.finditer(text):
            word = match.group()
            if not self.is_correct(word):
                misspelled.append((word, match.start(), match.end()))
        return misspelled
