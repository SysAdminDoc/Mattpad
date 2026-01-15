"""Theme definitions for Mattpad."""
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class Theme:
    """Theme color scheme."""
    name: str = "Professional Dark"
    
    # Background colors
    bg_darkest: str = "#0d1117"
    bg_dark: str = "#161b22"
    bg_medium: str = "#21262d"
    bg_light: str = "#30363d"
    bg_hover: str = "#3c444d"
    
    # Text colors
    text_primary: str = "#e6edf3"
    text_secondary: str = "#8b949e"
    text_muted: str = "#6e7681"
    text_disabled: str = "#484f58"
    
    # Accent colors
    accent_primary: str = "#238636"
    accent_secondary: str = "#1f6feb"
    accent_red: str = "#f85149"
    accent_yellow: str = "#d29922"
    accent_green: str = "#3fb950"
    accent_purple: str = "#a371f7"
    accent_cyan: str = "#39c5cf"
    accent_orange: str = "#db6d28"
    
    # Syntax colors
    syntax_keyword: str = "#ff7b72"
    syntax_string: str = "#a5d6ff"
    syntax_number: str = "#79c0ff"
    syntax_comment: str = "#8b949e"
    syntax_function: str = "#d2a8ff"
    syntax_class: str = "#ffa657"
    syntax_variable: str = "#ffa657"
    syntax_operator: str = "#ff7b72"
    syntax_decorator: str = "#d2a8ff"
    
    # UI elements
    selection_bg: str = "#264f78"
    current_line: str = "#161b22"
    bracket_match: str = "#1a3d22"
    search_highlight: str = "#3d3218"
    error_bg: str = "#2d1516"
    
    # Ribbon
    ribbon_bg: str = "#1e1e1e"
    ribbon_tab_bg: str = "#2d2d2d"
    ribbon_tab_active: str = "#3c3c3c"
    ribbon_tab_hover: str = "#404040"
    ribbon_group_bg: str = "#252526"
    ribbon_separator: str = "#404040"
    
    # Tabs
    tab_bar_bg: str = "#0d1117"
    tab_active: str = "#1f2428"
    tab_inactive: str = "#0d1117"
    tab_hover: str = "#21262d"
    tab_text_active: str = "#e6edf3"
    tab_text_inactive: str = "#8b949e"
    tab_modified: str = "#d29922"
    tab_close_hover: str = "#f85149"
    
    # Minimap
    minimap_viewport: str = "#2a3038"
    
    # Scrollbar
    scrollbar_bg: str = "#161b22"
    scrollbar_thumb: str = "#30363d"
    scrollbar_thumb_hover: str = "#484f58"


# Predefined themes
THEMES: Dict[str, Theme] = {
    "Professional Dark": Theme(),
    
    "Light": Theme(
        name="Light", ribbon_bg="#f3f3f3", ribbon_tab_bg="#e5e5e5", ribbon_tab_active="#ffffff",
        ribbon_tab_hover="#d0d0d0", ribbon_group_bg="#fafafa", ribbon_separator="#d0d0d0",
        bg_darkest="#ffffff", bg_dark="#f5f5f5", bg_medium="#e8e8e8", bg_light="#d0d0d0", bg_hover="#c0c0c0",
        text_primary="#24292f", text_secondary="#57606a", text_muted="#6e7781", text_disabled="#8c959f",
        tab_bar_bg="#e5e5e5", tab_active="#ffffff", tab_inactive="#f0f0f0",
        tab_hover="#e8e8e8", tab_text_active="#24292f", tab_text_inactive="#57606a",
        selection_bg="#b6d7ff", current_line="#f6f8fa", syntax_keyword="#cf222e",
        syntax_string="#0a3069", syntax_comment="#6e7781", syntax_function="#8250df",
        minimap_viewport="#d0d0d0",
    ),
    
    "Monokai": Theme(
        name="Monokai", ribbon_bg="#272822", ribbon_tab_bg="#1e1f1c", ribbon_tab_active="#3e3d32",
        ribbon_tab_hover="#49483e", ribbon_group_bg="#2d2e27", ribbon_separator="#49483e",
        bg_darkest="#272822", bg_dark="#2d2e27", bg_medium="#3e3d32", bg_light="#49483e", bg_hover="#75715e",
        text_primary="#f8f8f2", text_secondary="#a6a6a6", text_muted="#75715e", text_disabled="#49483e",
        tab_bar_bg="#1e1f1c", tab_active="#3e3d32", tab_inactive="#272822",
        tab_hover="#49483e", tab_text_active="#f8f8f2", tab_text_inactive="#a6a6a6",
        accent_primary="#a6e22e", accent_secondary="#66d9ef", accent_red="#f92672",
        syntax_keyword="#f92672", syntax_string="#e6db74", syntax_number="#ae81ff",
        syntax_comment="#75715e", syntax_function="#a6e22e", syntax_class="#66d9ef",
        minimap_viewport="#3e3d32",
    ),
    
    "Solarized Dark": Theme(
        name="Solarized Dark", ribbon_bg="#002b36", ribbon_tab_bg="#073642", ribbon_tab_active="#094656",
        ribbon_tab_hover="#094656", ribbon_group_bg="#073642", ribbon_separator="#094656",
        bg_darkest="#002b36", bg_dark="#073642", bg_medium="#094656", bg_light="#586e75", bg_hover="#657b83",
        text_primary="#839496", text_secondary="#657b83", text_muted="#586e75", text_disabled="#073642",
        tab_bar_bg="#073642", tab_active="#094656", tab_inactive="#002b36",
        tab_hover="#094656", tab_text_active="#93a1a1", tab_text_inactive="#657b83",
        accent_primary="#859900", accent_secondary="#268bd2", accent_red="#dc322f",
        syntax_keyword="#859900", syntax_string="#2aa198", syntax_number="#d33682",
        syntax_comment="#586e75", syntax_function="#268bd2", syntax_class="#b58900",
        minimap_viewport="#094656",
    ),
    
    "Dracula": Theme(
        name="Dracula", ribbon_bg="#282a36", ribbon_tab_bg="#21222c", ribbon_tab_active="#44475a",
        ribbon_tab_hover="#44475a", ribbon_group_bg="#282a36", ribbon_separator="#44475a",
        bg_darkest="#282a36", bg_dark="#21222c", bg_medium="#343746", bg_light="#44475a", bg_hover="#6272a4",
        text_primary="#f8f8f2", text_secondary="#6272a4", text_muted="#44475a", text_disabled="#343746",
        tab_bar_bg="#21222c", tab_active="#44475a", tab_inactive="#282a36",
        tab_hover="#343746", tab_text_active="#f8f8f2", tab_text_inactive="#6272a4",
        accent_primary="#50fa7b", accent_secondary="#8be9fd", accent_red="#ff5555",
        syntax_keyword="#ff79c6", syntax_string="#f1fa8c", syntax_number="#bd93f9",
        syntax_comment="#6272a4", syntax_function="#50fa7b", syntax_class="#8be9fd",
        minimap_viewport="#44475a",
    ),
    
    "Nord": Theme(
        name="Nord", ribbon_bg="#2e3440", ribbon_tab_bg="#3b4252", ribbon_tab_active="#434c5e",
        ribbon_tab_hover="#4c566a", ribbon_group_bg="#3b4252", ribbon_separator="#4c566a",
        bg_darkest="#2e3440", bg_dark="#3b4252", bg_medium="#434c5e", bg_light="#4c566a", bg_hover="#5e6779",
        text_primary="#eceff4", text_secondary="#d8dee9", text_muted="#a5b0c1", text_disabled="#4c566a",
        tab_bar_bg="#3b4252", tab_active="#434c5e", tab_inactive="#2e3440",
        tab_hover="#4c566a", tab_text_active="#eceff4", tab_text_inactive="#d8dee9",
        accent_primary="#a3be8c", accent_secondary="#88c0d0", accent_red="#bf616a",
        syntax_keyword="#81a1c1", syntax_string="#a3be8c", syntax_number="#b48ead",
        syntax_comment="#616e88", syntax_function="#88c0d0", syntax_class="#8fbcbb",
        minimap_viewport="#434c5e",
    ),
    
    "One Dark": Theme(
        name="One Dark", ribbon_bg="#21252b", ribbon_tab_bg="#282c34", ribbon_tab_active="#2c313a",
        ribbon_tab_hover="#3e4451", ribbon_group_bg="#282c34", ribbon_separator="#3e4451",
        bg_darkest="#282c34", bg_dark="#21252b", bg_medium="#2c313a", bg_light="#3e4451", bg_hover="#4b5263",
        text_primary="#abb2bf", text_secondary="#5c6370", text_muted="#4b5263", text_disabled="#3e4451",
        tab_bar_bg="#21252b", tab_active="#2c313a", tab_inactive="#21252b",
        tab_hover="#3e4451", tab_text_active="#abb2bf", tab_text_inactive="#5c6370",
        accent_primary="#98c379", accent_secondary="#61afef", accent_red="#e06c75",
        syntax_keyword="#c678dd", syntax_string="#98c379", syntax_number="#d19a66",
        syntax_comment="#5c6370", syntax_function="#61afef", syntax_class="#e5c07b",
        minimap_viewport="#2c313a",
    ),
    
    "Gruvbox Dark": Theme(
        name="Gruvbox Dark", ribbon_bg="#282828", ribbon_tab_bg="#1d2021", ribbon_tab_active="#3c3836",
        ribbon_tab_hover="#504945", ribbon_group_bg="#282828", ribbon_separator="#504945",
        bg_darkest="#1d2021", bg_dark="#282828", bg_medium="#3c3836", bg_light="#504945", bg_hover="#665c54",
        text_primary="#ebdbb2", text_secondary="#a89984", text_muted="#928374", text_disabled="#665c54",
        tab_bar_bg="#1d2021", tab_active="#3c3836", tab_inactive="#282828",
        tab_hover="#504945", tab_text_active="#ebdbb2", tab_text_inactive="#a89984",
        accent_primary="#b8bb26", accent_secondary="#83a598", accent_red="#fb4934",
        syntax_keyword="#fb4934", syntax_string="#b8bb26", syntax_number="#d3869b",
        syntax_comment="#928374", syntax_function="#fabd2f", syntax_class="#8ec07c",
        minimap_viewport="#3c3836",
    ),
    
    "Catppuccin Mocha": Theme(
        name="Catppuccin Mocha", ribbon_bg="#1e1e2e", ribbon_tab_bg="#181825", ribbon_tab_active="#313244",
        ribbon_tab_hover="#45475a", ribbon_group_bg="#1e1e2e", ribbon_separator="#45475a",
        bg_darkest="#1e1e2e", bg_dark="#181825", bg_medium="#313244", bg_light="#45475a", bg_hover="#585b70",
        text_primary="#cdd6f4", text_secondary="#a6adc8", text_muted="#6c7086", text_disabled="#45475a",
        tab_bar_bg="#181825", tab_active="#313244", tab_inactive="#1e1e2e",
        tab_hover="#45475a", tab_text_active="#cdd6f4", tab_text_inactive="#a6adc8",
        accent_primary="#a6e3a1", accent_secondary="#89b4fa", accent_red="#f38ba8",
        syntax_keyword="#cba6f7", syntax_string="#a6e3a1", syntax_number="#fab387",
        syntax_comment="#6c7086", syntax_function="#89b4fa", syntax_class="#f9e2af",
        minimap_viewport="#313244",
    ),
    
    "Tokyo Night": Theme(
        name="Tokyo Night", ribbon_bg="#1a1b26", ribbon_tab_bg="#16161e", ribbon_tab_active="#24283b",
        ribbon_tab_hover="#414868", ribbon_group_bg="#1a1b26", ribbon_separator="#414868",
        bg_darkest="#1a1b26", bg_dark="#16161e", bg_medium="#24283b", bg_light="#414868", bg_hover="#565f89",
        text_primary="#c0caf5", text_secondary="#a9b1d6", text_muted="#565f89", text_disabled="#414868",
        tab_bar_bg="#16161e", tab_active="#24283b", tab_inactive="#1a1b26",
        tab_hover="#414868", tab_text_active="#c0caf5", tab_text_inactive="#a9b1d6",
        accent_primary="#9ece6a", accent_secondary="#7aa2f7", accent_red="#f7768e",
        syntax_keyword="#bb9af7", syntax_string="#9ece6a", syntax_number="#ff9e64",
        syntax_comment="#565f89", syntax_function="#7aa2f7", syntax_class="#e0af68",
        minimap_viewport="#24283b",
    ),
    
    "High Contrast": Theme(
        name="High Contrast", ribbon_bg="#000000", ribbon_tab_bg="#000000", ribbon_tab_active="#1a1a1a",
        ribbon_tab_hover="#333333", ribbon_group_bg="#0a0a0a", ribbon_separator="#333333",
        bg_darkest="#000000", bg_dark="#0a0a0a", bg_medium="#1a1a1a", bg_light="#333333", bg_hover="#4d4d4d",
        text_primary="#ffffff", text_secondary="#cccccc", text_muted="#999999", text_disabled="#666666",
        tab_bar_bg="#000000", tab_active="#1a1a1a", tab_inactive="#000000",
        tab_hover="#333333", tab_text_active="#ffffff", tab_text_inactive="#cccccc",
        accent_primary="#00ff00", accent_secondary="#00ffff", accent_red="#ff0000",
        syntax_keyword="#ff6600", syntax_string="#00ff00", syntax_number="#00ffff",
        syntax_comment="#999999", syntax_function="#ffff00", syntax_class="#ff00ff",
        minimap_viewport="#1a1a1a",
    ),
}

# Global theme instance - will be set by app
THEME: Theme = THEMES["Professional Dark"]

def get_theme(name: str) -> Theme:
    """Get theme by name, with fallback to Professional Dark."""
    return THEMES.get(name, THEMES["Professional Dark"])

def set_theme(name: str) -> Theme:
    """Set the global theme and return it."""
    global THEME
    THEME = get_theme(name)
    return THEME
