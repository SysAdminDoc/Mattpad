# Notepad Plus Pro

<p align="center">
  <img src="notepad_plus_pro.ico" alt="Notepad Plus Pro" width="128">
</p>

<p align="center">
  <strong>A professional-grade text editor with auto-save, cloud sync, AI integration, and 50+ language syntax highlighting.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#building-from-source">Build</a> •
  <a href="#usage">Usage</a> •
  <a href="#keyboard-shortcuts">Shortcuts</a>
</p>

---

## Features

### 🎨 Modern Dark Interface
- **7 Built-in Themes**: GitHub Dark, Monokai Pro, Dracula, Nord, One Dark, Solarized Dark, Gruvbox
- **Dark Title Bar**: Native Windows 10/11 dark mode support
- **Scalable UI**: 100% to 200% scaling for high-DPI displays
- **Code Minimap**: VS Code-style document overview

### 💾 Never Lose Your Work
- **Auto-Save Cache**: Automatically saves every 10 seconds locally
- **Session Restore**: Reopens all tabs exactly where you left off
- **No Save Prompts**: Just close the window - your work is always preserved
- **External Change Detection**: Prompts to reload when files change outside the editor

### ☁️ Cloud Sync
- **GitHub Integration**: Sync files to any GitHub repository
- **Google Drive Integration**: One-click OAuth authentication
- **Automatic Sync**: Background sync every 5 minutes

### 🤖 AI Integration
- **Multiple Providers**: OpenAI, Anthropic (Claude), Ollama (local)
- **Built-in Prompts**: Explain, improve, fix bugs, add comments, translate, and more
- **Custom Prompts**: Write your own AI instructions
- **Context Menu**: Right-click to access AI features

### ✨ Editor Features
- **50+ Languages**: Syntax highlighting for Python, JavaScript, PowerShell, Batch, C++, Rust, Go, and many more
- **Find & Replace**: With regex support
- **Find in Files**: Search across entire directories
- **Clipboard History**: Access your last 50 copied items (Ctrl+Shift+V)
- **Line Numbers & Bookmarks**: Click to toggle bookmarks
- **Bracket Matching**: Automatic highlight and auto-close
- **Current Line Highlight**: Always know where your cursor is
- **Word Wrap Toggle**: View menu or settings

### 📁 File Management
- **Multi-Tab Interface**: Drag and drop to reorder tabs
- **File Tree Sidebar**: Browse and open files easily
- **Recent Files**: Quick access to recently opened files
- **Default Extension**: Set your preferred file type (.ps1, .bat, .py, etc.)

### 🖱️ Quality of Life
- **Middle-Click Scroll**: Browser-style auto-scroll
- **Click Tab Bar**: Click empty space to create new tab
- **Maximized by Default**: Opens full screen
- **Zoom**: Ctrl+Plus/Minus to adjust font size

---

## Installation

### Option 1: Run from Source (Python Required)

1. Make sure you have Python 3.8+ installed
2. Download or clone this repository
3. Run the script:
   ```bash
   python notepad_plus_pro.py
   ```
   Dependencies are installed automatically on first run.

### Option 2: Build Portable EXE (Windows)

1. Download or clone this repository
2. Double-click `build_exe.bat`
3. Wait for the build to complete (~2-5 minutes)
4. Find `NotepadPlusPro.exe` in the `dist` folder

The portable exe requires no installation - just copy and run anywhere!

---

## Building from Source

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Quick Build (Windows)

```batch
# Just run the batch file
build_exe.bat
```

### Manual Build

```bash
# Install PyInstaller
pip install pyinstaller customtkinter pillow chardet requests

# Build the executable
pyinstaller --onefile --windowed --name "NotepadPlusPro" ^
    --icon=notepad_plus_pro.ico ^
    --collect-all customtkinter ^
    --add-data "notepad_plus_pro.ico;." ^
    notepad_plus_pro.py
```

### Using the Spec File

```bash
pip install pyinstaller customtkinter pillow chardet requests
pyinstaller NotepadPlusPro.spec
```

### Output
The compiled executable will be in the `dist` folder:
```
dist/
  └── NotepadPlusPro.exe  (~50-100 MB)
```

---

## Usage

### First Launch
1. The application opens maximized with a dark theme
2. A new untitled tab is created automatically
3. Start typing or open a file (Ctrl+O)

### Cloud Sync Setup

**GitHub:**
1. Go to Cloud → Configure GitHub
2. Enter your Personal Access Token (create at github.com/settings/tokens)
3. Enter repository name (e.g., `username/my-notes`)
4. Click Save

**Google Drive:**
1. Go to Cloud → Configure Google Drive
2. Click "Sign in with Google"
3. Complete the OAuth flow in your browser
4. Files sync to your Drive automatically

### AI Setup
1. Go to AI → AI Settings
2. Select your provider (OpenAI, Anthropic, or Ollama)
3. Enter your API key
4. Select a model
5. Use AI features via the AI menu or right-click context menu

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
| **Edit** | |
| Undo | `Ctrl+Z` |
| Redo | `Ctrl+Y` |
| Cut | `Ctrl+X` |
| Copy | `Ctrl+C` |
| Paste | `Ctrl+V` |
| Duplicate Line | `Ctrl+D` |
| Toggle Comment | `Ctrl+/` |
| Clipboard History | `Ctrl+Shift+V` |
| **Find** | |
| Find/Replace | `Ctrl+F` |
| Find in Files | `Ctrl+Shift+F` |
| Find Next | `F3` |
| Find Previous | `Shift+F3` |
| Go to Line | `Ctrl+G` |
| **View** | |
| Zoom In | `Ctrl++` |
| Zoom Out | `Ctrl+-` |
| Reset Zoom | `Ctrl+0` |
| Toggle Sidebar | `Ctrl+B` |

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

Settings are stored in `~/.notepad_plus_pro/settings.json` and include:
- Theme preference
- UI scale
- Default file extension
- Font size and family
- Cloud sync credentials
- AI provider settings
- Recent files list
- Clipboard history

Session data (open tabs, content) is cached in `~/.notepad_plus_pro/cache/`

---

## Troubleshooting

### Build Fails
Try the alternative command:
```bash
pyinstaller --onefile --windowed --name "NotepadPlusPro" --collect-all customtkinter notepad_plus_pro.py
```

### Missing Dependencies
Run manually:
```bash
pip install customtkinter pillow chardet requests openai anthropic
```

### Antivirus Warning
Some antivirus software flags PyInstaller executables. Add an exception for `NotepadPlusPro.exe` or the `dist` folder.

### Dark Title Bar Not Working
Dark title bar requires Windows 10 version 20H1 or later. On older versions, the system theme is used.

---

## License

This project is provided as-is for personal and commercial use.

---

## Acknowledgments

- Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- Themes inspired by popular code editors
- Icons and design following modern UI principles
