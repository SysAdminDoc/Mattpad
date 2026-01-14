# Mattpad v5.0

<p align="center">
  <img src="mattpad.ico" alt="Mattpad" width="128">
</p>

<p align="center">
  <strong>A professional-grade text editor with hot exit, cloud sync, AI integration, and 50+ language syntax highlighting.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#building-from-source">Build</a> •
  <a href="#usage">Usage</a> •
  <a href="#keyboard-shortcuts">Shortcuts</a>
</p>

---

## What's New in v5.0

### 🔥 Hot Exit (Notepad++ Style)
- **Never lose work again**: All tabs saved automatically on close
- **Full state restoration**: Reopens with exact cursor positions, scroll positions, and unsaved content
- **No save prompts**: Just close the window - everything is preserved
- **Modified indicators**: Visual feedback for unsaved changes

### ⚡ Performance Improvements
- **Viewport-only highlighting**: Only processes visible lines + buffer
- **Large file mode**: Files >1MB auto-disable syntax highlighting
- **Thread-safe dispatcher**: All background operations safely marshal to UI thread

### 🛠️ New Line Operations
- **Move lines**: `Ctrl+Shift+Up/Down` to move lines or selections
- **Delete line**: `Ctrl+Shift+K` removes current line
- **Duplicate**: `Ctrl+D` duplicates line or selection with full undo support

### 📊 Enhanced Status Bar
- **Clickable line ending**: Toggle between CRLF and LF
- **Clickable encoding**: Toggle between UTF-8 and ANSI
- **Click position**: Jump to Go to Line dialog
- **Click zoom**: Reset to 100%

---

## Features

### 🎨 Modern Ribbon Interface
- **12 Built-in Themes**: Professional Dark, Light, Monokai, Solarized Dark/Light, Dracula, Nord, One Dark, Catppuccin, Tokyo Night, High Contrast, Gruvbox
- **Dark Title Bar**: Native Windows 10/11 dark mode support
- **Scalable UI**: 100% to 200% scaling for high-DPI displays
- **Collapsible Ribbon**: Auto-hide or pin the ribbon toolbar
- **Code Minimap**: VS Code-style document overview

### 💾 Never Lose Your Work
- **Hot Exit**: Saves complete session state including unsaved content
- **Auto-Save Cache**: Automatically saves every 10 seconds locally
- **Session Restore**: Reopens all tabs exactly where you left off
- **External Change Detection**: Prompts to reload when files change outside the editor
- **Backup Manager**: View and restore previous versions of files

### ☁️ Cloud Sync
- **GitHub Integration**: Sync files to any GitHub repository
- **Automatic Sync**: Background sync with status indicator
- **Connection Testing**: Verify sync setup before committing

### 🤖 AI Integration
- **Multiple Providers**: OpenAI (GPT-4), Anthropic (Claude), Ollama (local)
- **Built-in Prompts**: Summarize, Fix Grammar, Professional Email, Simplify, Expand, Explain Code, Refactor, Add Comments, Convert to Bullet Points, Translate to Python
- **Custom Prompts**: Write your own AI instructions
- **Thread-safe**: AI operations run in background without freezing UI

### ✨ Editor Features
- **50+ Languages**: Syntax highlighting for Python, JavaScript, TypeScript, PowerShell, JSON, HTML, CSS, Markdown, and many more
- **Find & Replace**: With regex support and whole word matching
- **Find in Files**: Search across entire directories
- **Clipboard Panel**: Access clipboard history with pinning support
- **Line Numbers**: With bookmarks and fold markers
- **Bracket Matching**: Automatic highlight and auto-close
- **Current Line Highlight**: Always know where your cursor is
- **Spell Check**: Built-in with custom dictionary support
- **Snippets**: Code templates with tab stops
- **Macros**: Record and playback actions

### 📁 File Management
- **Multi-Tab Interface**: Drag and drop to reorder tabs
- **File Tree Sidebar**: Browse and open files easily
- **Recent Files**: Quick access dropdown in tab bar
- **Closed Tabs Recovery**: `Ctrl+Shift+T` to reopen closed tabs
- **Notepad++ Import**: Import sessions from Notepad++

### 🖱️ Quality of Life
- **Middle-Click Scroll**: Browser-style auto-scroll
- **Click Tab Bar**: Click empty space to create new tab
- **Tab Context Menu**: Right-click for close options
- **Command Palette**: `Ctrl+Shift+P` for quick access to all commands
- **Integrated Terminal**: `Ctrl+\`` to toggle terminal
- **File Comparison**: Diff view for comparing files

---

## Installation

### Option 1: Run from Source (Python Required)

1. Make sure you have Python 3.8+ installed
2. Download or clone this repository
3. Run the script:
   ```bash
   python mattpad_v5.py
   ```
   Dependencies are installed automatically on first run.

### Option 2: Build Portable EXE (Windows)

1. Download or clone this repository
2. Double-click `build_exe.bat`
3. Wait for the build to complete (~2-5 minutes)
4. Find `Mattpad.exe` in the `dist` folder

The portable exe requires no installation - just copy and run anywhere!

---

## Building from Source

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Quick Build (Windows)

```batch
# Run the build menu
build_exe.bat
```

This presents two options:
1. **Portable EXE** - Single file, includes spellcheck, runs anywhere
2. **Installer Build** - Creates files for Inno Setup installer

### Manual Build

```bash
# Install dependencies
pip install pyinstaller customtkinter pillow chardet requests pyspellchecker openai anthropic

# Build portable exe with spellcheck
pyinstaller --onefile --windowed --name "Mattpad" --icon=mattpad.ico ^
    --collect-all customtkinter ^
    --collect-all spellchecker ^
    --collect-data spellchecker ^
    mattpad_v5.py
```

### Output
The compiled executable will be in the `dist` folder:
```
dist/
  └── Mattpad.exe  (~50-100 MB)
```

### Creating an Installer
1. Run `build_exe.bat` and select option 2
2. Download [Inno Setup](https://jrsoftware.org/isdl.php)
3. Open `Mattpad_Setup.iss`
4. Build → Compile
5. Find `Mattpad_Setup_v5.0.exe` in the `installer` folder

---

## Usage

### First Launch
1. The application opens maximized with a dark theme
2. A new untitled tab is created automatically
3. Start typing or open a file (Ctrl+O)

### Hot Exit
Just close the window! Mattpad automatically:
- Saves all tab content (including unsaved files)
- Preserves cursor positions and scroll positions
- Restores everything on next launch

No save prompts, no data loss.

### Cloud Sync Setup

**GitHub:**
1. Go to Cloud tab → Configure GitHub
2. Enter your Personal Access Token (create at github.com/settings/tokens)
3. Enter repository name (e.g., `username/my-notes`)
4. Click Save

### AI Setup
1. Go to AI tab → Settings
2. Select your provider (OpenAI, Anthropic, or Ollama)
3. Enter your API key
4. Select a model
5. Use AI features via the AI tab or right-click context menu

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| **File** | |
| New File | `Ctrl+N` |
| Open File | `Ctrl+O` |
| Save | `Ctrl+S` |
| Save As | `Ctrl+Shift+S` |
| Close Tab | `Ctrl+W` |
| Reopen Closed Tab | `Ctrl+Shift+T` |
| **Edit** | |
| Undo | `Ctrl+Z` |
| Redo | `Ctrl+Y` |
| Cut | `Ctrl+X` |
| Copy | `Ctrl+C` |
| Paste | `Ctrl+V` |
| Duplicate Line | `Ctrl+D` |
| Move Line Up | `Ctrl+Shift+Up` |
| Move Line Down | `Ctrl+Shift+Down` |
| Delete Line | `Ctrl+Shift+K` |
| Toggle Comment | `Ctrl+/` |
| **Find** | |
| Find/Replace | `Ctrl+F` |
| Find in Files | `Ctrl+Shift+F` |
| Find Next | `F3` |
| Go to Line | `Ctrl+G` |
| **View** | |
| Zoom In | `Ctrl++` |
| Zoom Out | `Ctrl+-` |
| Reset Zoom | `Ctrl+0` |
| Toggle Sidebar | `Ctrl+B` |
| Toggle Terminal | `Ctrl+\`` |
| Command Palette | `Ctrl+Shift+P` |

---

## Supported Languages

Syntax highlighting for 50+ languages including:

| Languages | | | |
|-----------|-----------|-----------|-----------|
| Python | JavaScript | TypeScript | PowerShell |
| Batch | Bash | C | C++ |
| C# | Java | Kotlin | Swift |
| Go | Rust | Ruby | PHP |
| HTML | CSS | SCSS | SQL |
| JSON | YAML | XML | Markdown |
| Lua | Perl | R | MATLAB |
| Haskell | Scala | Clojure | F# |
| Dart | Julia | Zig | Nim |
| TOML | INI | Dockerfile | Makefile |

---

## Configuration

Settings are stored in `~/.mattpad/settings.json` and include:
- Theme preference
- UI scale
- Font size and family
- Hot exit enabled/disabled
- Cloud sync credentials
- AI provider settings
- Recent files list

Data directories:
- `~/.mattpad/cache/` - Session data
- `~/.mattpad/hot_exit/` - Hot exit snapshots
- `~/.mattpad/backups/` - File backups
- `~/.mattpad/closed_tabs/` - Closed tab recovery
- `~/.mattpad/snippets/` - Custom snippets
- `~/.mattpad/macros/` - Recorded macros

---

## Troubleshooting

### Build Fails
Try the alternative command:
```bash
pyinstaller --onefile --windowed --name "Mattpad" --collect-all customtkinter mattpad_v5.py
```

### Missing Dependencies
Run manually:
```bash
pip install customtkinter pillow chardet requests openai anthropic
```

### Antivirus Warning
Some antivirus software flags PyInstaller executables. Add an exception for `Mattpad.exe` or the `dist` folder.

### Dark Title Bar Not Working
Dark title bar requires Windows 10 version 20H1 or later. On older versions, the system theme is used.

### Large File Performance
Files over 1MB automatically disable syntax highlighting for better performance. This is indicated in the status bar.

---

## Version History

### v5.0 (Current)
- Hot Exit: Complete session persistence without save prompts
- Thread-safe dispatcher for background operations
- Line operations: move up/down, delete line
- Clickable status bar toggles (line ending, encoding)
- Viewport-only syntax highlighting
- Large file mode (>1MB)
- Tab order preservation

### v4.5
- Ribbon interface
- DPI awareness
- Improved themes

### v4.0
- AI integration
- Cloud sync
- Clipboard panel

---

## License

This project is provided as-is for personal and commercial use.

---

## Acknowledgments

- Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- Themes inspired by popular code editors
- Icons and design following modern UI principles
