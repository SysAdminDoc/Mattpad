"""Snippets and macros management for Mattpad."""
import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Directories
APP_DIR = Path.home() / ".mattpad"
SNIPPETS_DIR = APP_DIR / "snippets"
MACROS_DIR = APP_DIR / "macros"
SNIPPETS_DIR.mkdir(parents=True, exist_ok=True)
MACROS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Snippet:
    """Code snippet definition."""
    name: str
    trigger: str
    content: str
    language: str = ""
    description: str = ""
    
    def expand(self, **variables) -> str:
        """Expand snippet with variables."""
        result = self.content
        for key, value in variables.items():
            result = result.replace(f"${{{key}}}", str(value))
            result = result.replace(f"${key}", str(value))
        return result


@dataclass 
class Macro:
    """Recorded macro definition."""
    name: str
    actions: List[Dict] = field(default_factory=list)
    shortcut: str = ""


class SnippetsManager:
    """Manages code snippets."""
    
    DEFAULT_SNIPPETS = [
        Snippet("For Loop", "for", "for ${1:i} in ${2:range(10)}:\n    ${3:pass}", "Python", "For loop"),
        Snippet("Function", "def", "def ${1:function_name}(${2:args}):\n    \"\"\"${3:Docstring}\"\"\"\n    ${4:pass}", "Python", "Function definition"),
        Snippet("Class", "class", "class ${1:ClassName}:\n    \"\"\"${2:Class docstring}\"\"\"\n    \n    def __init__(self${3:, args}):\n        ${4:pass}", "Python", "Class definition"),
        Snippet("Try/Except", "try", "try:\n    ${1:pass}\nexcept ${2:Exception} as e:\n    ${3:print(e)}", "Python", "Try/except block"),
        Snippet("With Statement", "with", "with ${1:open('file')} as ${2:f}:\n    ${3:pass}", "Python", "With statement"),
        Snippet("List Comprehension", "lc", "[${1:x} for ${2:x} in ${3:items}]", "Python", "List comprehension"),
        Snippet("Dict Comprehension", "dc", "{${1:k}: ${2:v} for ${3:k, v} in ${4:items}}", "Python", "Dict comprehension"),
        Snippet("Lambda", "lam", "lambda ${1:x}: ${2:x}", "Python", "Lambda function"),
        Snippet("If/Else", "ife", "if ${1:condition}:\n    ${2:pass}\nelse:\n    ${3:pass}", "Python", "If/else statement"),
        Snippet("Main Guard", "main", 'if __name__ == "__main__":\n    ${1:main()}', "Python", "Main guard"),
        
        # JavaScript
        Snippet("Function", "fn", "function ${1:name}(${2:params}) {\n    ${3}\n}", "JavaScript", "Function"),
        Snippet("Arrow Function", "af", "const ${1:name} = (${2:params}) => {\n    ${3}\n};", "JavaScript", "Arrow function"),
        Snippet("For Loop", "for", "for (let ${1:i} = 0; ${1:i} < ${2:length}; ${1:i}++) {\n    ${3}\n}", "JavaScript", "For loop"),
        Snippet("ForEach", "fe", "${1:array}.forEach((${2:item}) => {\n    ${3}\n});", "JavaScript", "ForEach loop"),
        Snippet("Map", "map", "${1:array}.map((${2:item}) => {\n    ${3}\n});", "JavaScript", "Map"),
        Snippet("Console Log", "cl", "console.log(${1});", "JavaScript", "Console log"),
        Snippet("Try/Catch", "try", "try {\n    ${1}\n} catch (${2:error}) {\n    ${3:console.error(error);}\n}", "JavaScript", "Try/catch"),
        Snippet("Async Function", "async", "async function ${1:name}(${2:params}) {\n    ${3}\n}", "JavaScript", "Async function"),
        
        # HTML
        Snippet("HTML5 Template", "html5", '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>${1:Document}</title>\n</head>\n<body>\n    ${2}\n</body>\n</html>', "HTML", "HTML5 boilerplate"),
        Snippet("Div", "div", '<div class="${1}">\n    ${2}\n</div>', "HTML", "Div element"),
        Snippet("Link", "link", '<link rel="stylesheet" href="${1:style.css}">', "HTML", "CSS link"),
        Snippet("Script", "script", '<script src="${1:script.js}"></script>', "HTML", "Script tag"),
        
        # CSS
        Snippet("Flexbox Center", "flex", "display: flex;\njustify-content: center;\nalign-items: center;", "CSS", "Flexbox centering"),
        Snippet("Grid", "grid", "display: grid;\ngrid-template-columns: ${1:repeat(3, 1fr)};\ngap: ${2:1rem};", "CSS", "CSS Grid"),
        Snippet("Media Query", "mq", "@media (max-width: ${1:768px}) {\n    ${2}\n}", "CSS", "Media query"),
    ]
    
    def __init__(self):
        self.snippets: List[Snippet] = []
        self._load()
    
    def _load(self):
        """Load snippets from file."""
        self.snippets = self.DEFAULT_SNIPPETS.copy()
        snippets_file = SNIPPETS_DIR / "snippets.json"
        
        if snippets_file.exists():
            try:
                data = json.loads(snippets_file.read_text(encoding='utf-8'))
                for s in data:
                    self.snippets.append(Snippet(**s))
            except Exception:
                pass
    
    def save(self):
        """Save custom snippets to file."""
        snippets_file = SNIPPETS_DIR / "snippets.json"
        custom = [s for s in self.snippets if s not in self.DEFAULT_SNIPPETS]
        data = [
            {
                "name": s.name,
                "trigger": s.trigger,
                "content": s.content,
                "language": s.language,
                "description": s.description
            }
            for s in custom
        ]
        snippets_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    def get_for_language(self, language: str) -> List[Snippet]:
        """Get snippets for a specific language."""
        return [s for s in self.snippets if not s.language or s.language == language]
    
    def find_by_trigger(self, trigger: str, language: str) -> Optional[Snippet]:
        """Find snippet by trigger text."""
        for s in self.snippets:
            if s.trigger == trigger and (not s.language or s.language == language):
                return s
        return None
    
    def add(self, snippet: Snippet):
        """Add a new snippet."""
        self.snippets.append(snippet)
        self.save()
    
    def remove(self, snippet: Snippet):
        """Remove a snippet."""
        if snippet in self.snippets and snippet not in self.DEFAULT_SNIPPETS:
            self.snippets.remove(snippet)
            self.save()
    
    def update(self, old_snippet: Snippet, new_snippet: Snippet):
        """Update an existing snippet."""
        try:
            idx = self.snippets.index(old_snippet)
            self.snippets[idx] = new_snippet
            self.save()
        except ValueError:
            pass


class MacroManager:
    """Manages recorded macros."""
    
    def __init__(self):
        self.macros: List[Macro] = []
        self.recording = False
        self.current_actions: List[Dict] = []
        self._load()
    
    def _load(self):
        """Load macros from file."""
        macros_file = MACROS_DIR / "macros.json"
        if macros_file.exists():
            try:
                data = json.loads(macros_file.read_text(encoding='utf-8'))
                self.macros = [Macro(**m) for m in data]
            except Exception:
                pass
    
    def save(self):
        """Save macros to file."""
        macros_file = MACROS_DIR / "macros.json"
        data = [
            {
                "name": m.name,
                "actions": m.actions,
                "shortcut": m.shortcut
            }
            for m in self.macros
        ]
        macros_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    def start_recording(self):
        """Start recording a macro."""
        self.recording = True
        self.current_actions = []
    
    def stop_recording(self, name: str) -> Macro:
        """Stop recording and save the macro."""
        self.recording = False
        macro = Macro(name=name, actions=self.current_actions.copy())
        self.macros.append(macro)
        self.save()
        return macro
    
    def record_action(self, action_type: str, data: Any):
        """Record an action during macro recording."""
        if self.recording:
            self.current_actions.append({
                "type": action_type,
                "data": data,
                "time": time.time()
            })
    
    def cancel_recording(self):
        """Cancel the current recording."""
        self.recording = False
        self.current_actions = []
    
    def delete_macro(self, macro: Macro):
        """Delete a macro."""
        if macro in self.macros:
            self.macros.remove(macro)
            self.save()
    
    def get_by_name(self, name: str) -> Optional[Macro]:
        """Get macro by name."""
        for m in self.macros:
            if m.name == name:
                return m
        return None
    
    def get_by_shortcut(self, shortcut: str) -> Optional[Macro]:
        """Get macro by keyboard shortcut."""
        for m in self.macros:
            if m.shortcut == shortcut:
                return m
        return None
