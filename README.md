# Mattpad

<p align="center">

<img width="128" height="128" alt="mattpad" src="https://github.com/user-attachments/assets/efcc4354-6eb3-4fc1-b3c3-ee284037c09e" />

</p>

Mattpad is a cache-first, multi-tab text editor built with CustomTkinter that removes save nagging by continuously auto-saving tab content to a local session cache. It supports modern editor UX including themes, minimap, line numbers, find/replace with regex, find-in-files, clipboard history, and middle-click auto-scroll. Optional cloud sync mirrors tab content to GitHub or Google Drive on a timer, and built-in AI actions can rewrite or explain selected text via OpenAI, Anthropic, or local Ollama, all accessible from the context menu.

---

## Installation

### Option 1: Run from Source (Python Required)

1. Make sure you have Python 3.8+ installed
2. Download or clone this repository
3. Run the script:
   ```bash
   python mattpad.py
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
# Just run the batch file
build_exe.bat
```

### Manual Build

```bash
# Install PyInstaller
pip install pyinstaller customtkinter pillow chardet requests

# Build the executable
pyinstaller --onefile --windowed --name "Mattpad" ^
    --icon=mattpad.ico ^
    --collect-all customtkinter ^
    --add-data "mattpad.ico;." ^
    mattpad.py
```

### Using the Spec File

```bash
pip install pyinstaller customtkinter pillow chardet requests
pyinstaller Mattpad.spec
```

### Output
The compiled executable will be in the `dist` folder:
```
dist/
  └── Mattpad.exe  (~50-100 MB)
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

Settings are stored in `~/.mattpad/settings.json` and include:
- Theme preference
- UI scale
- Default file extension
- Font size and family
- Cloud sync credentials
- AI provider settings
- Recent files list
- Clipboard history

Session data (open tabs, content) is cached in `~/.mattpad/cache/`

---

## Troubleshooting

### Build Fails
Try the alternative command:
```bash
pyinstaller --onefile --windowed --name "Mattpad" --collect-all customtkinter mattpad.py
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

---

## License

This project is provided as-is for personal and commercial use.

---

## Acknowledgments

- Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- Themes inspired by popular code editors
- Icons and design following modern UI principles
