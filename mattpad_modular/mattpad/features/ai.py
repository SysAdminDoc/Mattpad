"""AI integration for Mattpad."""
import threading
import logging
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.settings import EditorSettings

from ..utils.dispatcher import get_dispatcher
from ..core.managers import SecretStorage

logger = logging.getLogger(__name__)

# Try to import AI libraries
OPENAI_AVAILABLE = False
ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    pass

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class AIManager:
    """AI integration with thread-safe callback dispatch."""
    
    PROMPTS = [
        ("Summarize", "Summarize this text concisely:\n\n{text}"),
        ("Fix Grammar", "Fix grammar and spelling errors:\n\n{text}"),
        ("Professional Email", "Rewrite as a professional email:\n\n{text}"),
        ("Simplify", "Simplify this text for clarity:\n\n{text}"),
        ("Expand", "Expand with more detail:\n\n{text}"),
        ("Explain Code", "Explain what this code does:\n\n{text}"),
        ("Refactor Code", "Refactor this code for clarity and efficiency:\n\n{text}"),
        ("Add Comments", "Add helpful comments to this code:\n\n{text}"),
        ("Convert to Bullet Points", "Convert to bullet points:\n\n{text}"),
        ("Translate to Python", "Convert this code to Python:\n\n{text}"),
    ]
    
    def __init__(self, settings: 'EditorSettings'):
        self.settings = settings
    
    def _safe_callback(self, callback: Callable, result: str, error: str):
        """Dispatch callback to main thread safely."""
        dispatcher = get_dispatcher()
        if dispatcher:
            dispatcher.dispatch(callback, result, error)
        else:
            callback(result, error)
    
    def process(self, text: str, prompt_name: str, callback: Callable):
        """Process text with a named prompt."""
        template = next((p[1] for p in self.PROMPTS if p[0] == prompt_name), None)
        if not template:
            self._safe_callback(callback, "", "Unknown prompt")
            return
        
        full_prompt = template.format(text=text)
        threading.Thread(
            target=lambda: self._call_api(full_prompt, callback),
            daemon=True
        ).start()
    
    def process_custom(self, text: str, prompt: str, callback: Callable):
        """Process text with a custom prompt."""
        full_prompt = f"{prompt}\n\n{text}" if text else prompt
        threading.Thread(
            target=lambda: self._call_api(full_prompt, callback),
            daemon=True
        ).start()
    
    def _call_api(self, prompt: str, callback: Callable):
        """Call the AI API."""
        try:
            # Get API key
            key = SecretStorage.get("ai_api_key", self.settings.ai_api_key)
            
            if not key and self.settings.ai_provider != "ollama":
                self._safe_callback(callback, "", "API key not configured")
                return
            
            # Call appropriate provider
            if self.settings.ai_provider == "openai" and OPENAI_AVAILABLE:
                self._call_openai(key, prompt, callback)
            elif self.settings.ai_provider == "anthropic" and ANTHROPIC_AVAILABLE:
                self._call_anthropic(key, prompt, callback)
            elif self.settings.ai_provider == "ollama":
                self._call_ollama(prompt, callback)
            else:
                self._safe_callback(callback, "", "Provider not configured or not available")
                
        except Exception as e:
            logger.error(f"AI API error: {e}")
            self._safe_callback(callback, "", str(e))
    
    def _call_openai(self, key: str, prompt: str, callback: Callable):
        """Call OpenAI API."""
        try:
            client = openai.OpenAI(api_key=key)
            response = client.chat.completions.create(
                model=self.settings.ai_model or "gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content
            self._safe_callback(callback, result, "")
        except Exception as e:
            self._safe_callback(callback, "", str(e))
    
    def _call_anthropic(self, key: str, prompt: str, callback: Callable):
        """Call Anthropic API."""
        try:
            client = anthropic.Anthropic(api_key=key)
            response = client.messages.create(
                model=self.settings.ai_model or "claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text
            self._safe_callback(callback, result, "")
        except Exception as e:
            self._safe_callback(callback, "", str(e))
    
    def _call_ollama(self, prompt: str, callback: Callable):
        """Call local Ollama API."""
        if not REQUESTS_AVAILABLE:
            self._safe_callback(callback, "", "requests library not available")
            return
        
        try:
            import requests
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.settings.ai_model or "llama3.2",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            result = response.json().get("response", "")
            self._safe_callback(callback, result, "")
        except Exception as e:
            self._safe_callback(callback, "", str(e))
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available AI providers."""
        providers = []
        if OPENAI_AVAILABLE:
            providers.append(("openai", "OpenAI (GPT-4, GPT-3.5)"))
        if ANTHROPIC_AVAILABLE:
            providers.append(("anthropic", "Anthropic (Claude)"))
        if REQUESTS_AVAILABLE:
            providers.append(("ollama", "Ollama (Local)"))
        return providers
