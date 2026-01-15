# Mattpad v6.0 - Professional Text Editor

A modular, feature-rich text editor built with Python and CustomTkinter.

## Features

- **Modern UI**: Dark theme with customizable colors, ribbon toolbar, and Chrome-style tabs
- **Syntax Highlighting**: Support for Python, JavaScript, TypeScript, HTML, CSS, JSON, and more
- **File Management**: Tab-based editing, drag-to-reorder tabs, recent files, session restore
- **Find & Replace**: Search with regex support, find in files
- **Code Tools**: Auto-indent, bracket matching, comment toggle, line numbers, minimap
- **AI Integration**: OpenAI, Anthropic Claude, and Ollama support for text processing
- **Cloud Sync**: GitHub integration for syncing files
- **Clipboard Manager**: History tracking with pin support
- **Spellcheck**: Built-in spell checking with custom dictionary
- **Snippets**: Code snippets with tab expansion
- **Terminal**: Integrated terminal panel
- **Hot Exit**: Preserves unsaved work across sessions

## Installation

### Quick Start

1. Extract the zip file
2. Run `python run_mattpad.py`

The launcher will automatically install required dependencies.

### Manual Installation

```bash
pip install -r mattpad/requirements.txt
python -m mattpad
```

## Project Structure

```
mattpad_v6/
├── run_mattpad.py          # Main launcher (run this)
└── mattpad/
    ├── __init__.py         # Package init
    ├── __main__.py         # Module entry point
    ├── app.py              # Main application
    ├── requirements.txt    # Dependencies
    ├── core/               # Core functionality
    │   ├── settings.py     # Settings management
    │   ├── tabs.py         # Tab data
    │   └── managers.py     # Cache, backup, session managers
    ├── features/           # Feature modules
    │   ├── syntax.py       # Syntax highlighting
    │   ├── spellcheck.py   # Spell checking
    │   ├── ai.py           # AI integration
    │   ├── cloud.py        # Cloud sync
    │   ├── snippets.py     # Snippets & macros
    │   └── clipboard.py    # Clipboard manager
    ├── ui/                 # UI components
    │   ├── ribbon.py       # Ribbon toolbar
    │   ├── minimap.py      # Code minimap
    │   ├── line_numbers.py # Line number display
    │   ├── toast.py        # Toast notifications
    │   ├── welcome.py      # Welcome screen
    │   ├── sidebar.py      # File explorer
    │   ├── clipboard_panel.py
    │   ├── find_replace.py
    │   └── dialogs.py      # Dialog utilities
    ├── utils/              # Utilities
    │   ├── themes.py       # Theme definitions
    │   ├── dispatcher.py   # Thread-safe dispatcher
    │   ├── debouncer.py    # Rate limiting
    │   └── file_utils.py   # File operations
    └── tests/              # Test modules
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New file |
| Ctrl+O | Open file |
| Ctrl+S | Save |
| Ctrl+Shift+S | Save As |
| Ctrl+W | Close tab |
| Ctrl+Shift+T | Reopen closed tab |
| Ctrl+F | Find |
| Ctrl+Shift+F | Find in files |
| Ctrl+G | Go to line |
| Ctrl+D | Duplicate line |
| Ctrl+/ | Toggle comment |
| Ctrl+B | Toggle sidebar |
| Ctrl++ | Zoom in |
| Ctrl+- | Zoom out |
| Ctrl+0 | Reset zoom |
| Ctrl+Tab | Next tab |
| Ctrl+Shift+Tab | Previous tab |
| F11 | Toggle fullscreen |

## Themes

Mattpad includes 10 built-in themes:
- Professional Dark (default)
- Light
- Monokai
- Solarized Dark
- Dracula
- Nord
- One Dark
- Gruvbox Dark
- Catppuccin Mocha
- Tokyo Night
- High Contrast

Change themes via Options → Themes in the ribbon.

## AI Configuration

1. Go to AI tab → Settings
2. Select provider (OpenAI, Anthropic, or Ollama)
3. Enter your API key (not needed for Ollama)
4. Select model (optional - uses defaults)

## GitHub Sync

1. Go to Cloud tab → Configure
2. Enter your GitHub personal access token
3. Enter repository name (e.g., `username/repo`)
4. Set branch and path
5. Use "Sync Now" to sync current file

## Requirements

- Python 3.8+
- customtkinter
- requests (for cloud sync and AI)

Optional:
- chardet (encoding detection)
- pyspellchecker (spell checking)
- keyring (secure credential storage)
- openai (OpenAI API)
- anthropic (Anthropic API)
- Pillow (image support)

## License

MIT License
