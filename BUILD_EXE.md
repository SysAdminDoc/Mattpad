# Building Notepad Plus Pro as a Portable EXE

## Quick Method (Recommended)

### Step 1: Install PyInstaller
```
pip install pyinstaller
```

### Step 2: Build the EXE
Open a command prompt in the folder containing `notepad_plus_pro.py` and `notepad_plus_pro.ico` and run:

```
pyinstaller --onefile --windowed --name "NotepadPlusPro" --icon=notepad_plus_pro.ico --collect-all customtkinter --add-data "notepad_plus_pro.ico;." notepad_plus_pro.py
```

### Step 3: Find Your EXE
The portable exe will be in the `dist` folder:
```
dist\NotepadPlusPro.exe
```

---

## Using the Batch File (Easiest)

1. Make sure you have these files in the same folder:
   - `notepad_plus_pro.py`
   - `notepad_plus_pro.ico`
   - `build_exe.bat`
2. Double-click `build_exe.bat`
3. Wait for the build to complete
4. Find your exe in the `dist` folder

---

## Custom Icon

The included `notepad_plus_pro.ico` file provides:
- Application icon in the taskbar
- Icon in File Explorer
- Icon in the title bar
- Icon when pinned to Start/Taskbar

To use your own icon:
1. Create a `.ico` file with multiple sizes (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)
2. Name it `notepad_plus_pro.ico` and place it in the same folder
3. Run the build script

---

## Dark Title Bar

The application automatically enables the dark title bar on Windows 10 (20H1+) and Windows 11. This matches the dark theme of the editor.

If you're on an older Windows version, the title bar will use your system theme.

---

## Detailed Method (If Quick Method Fails)

### Step 1: Install All Dependencies
```
pip install pyinstaller customtkinter pillow chardet requests openai anthropic
```

### Step 2: Create a Spec File
Create a file named `NotepadPlusPro.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter

block_cipher = None

# Find customtkinter location
ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ['notepad_plus_pro.py'],
    pathex=[],
    binaries=[],
    datas=[(ctk_path, 'customtkinter')],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL._tkinter_finder',
        'chardet',
        'requests',
        'openai',
        'anthropic',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NotepadPlusPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

### Step 3: Build Using Spec File
```
pyinstaller NotepadPlusPro.spec
```

---

## Troubleshooting

### "ModuleNotFoundError: customtkinter"
Add customtkinter manually:
```
pyinstaller --onefile --windowed --collect-all customtkinter --hidden-import customtkinter notepad_plus_pro.py
```

### "DLL load failed"
Try adding --collect-all for problematic modules:
```
pyinstaller --onefile --windowed --collect-all customtkinter --collect-all PIL notepad_plus_pro.py
```

### EXE is too large
The exe will be ~50-100MB due to bundled Python and libraries. This is normal for portable Python apps.

### Antivirus False Positive
Some antivirus software flags PyInstaller executables. You can:
1. Add an exception for the exe
2. Sign the exe with a code signing certificate
3. Use `--key` flag to encrypt the exe

---

## Alternative: Use Nuitka (Smaller EXE)

Nuitka compiles Python to C and creates smaller, faster executables:

```
pip install nuitka
nuitka --standalone --onefile --enable-plugin=tk-inter --windows-disable-console notepad_plus_pro.py
```

---

## What Gets Bundled

The portable exe includes:
- Python interpreter
- All required libraries (customtkinter, PIL, etc.)
- Your script

The exe creates these folders in your user directory:
- `~/.notepad_plus_pro/` - Settings and cache
- `~/.notepad_plus_gdrive_token.json` - Google Drive auth (if used)

---

## Distribution

The final `NotepadPlusPro.exe` is completely portable:
- No Python installation required
- No dependencies to install
- Just copy and run anywhere on Windows!
