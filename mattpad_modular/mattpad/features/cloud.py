"""Cloud sync functionality for Mattpad."""
import os
import time
import base64
import logging
from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.settings import EditorSettings

from ..core.managers import SecretStorage

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class CloudSyncManager:
    """Cloud synchronization manager supporting GitHub."""
    
    def __init__(self, settings: 'EditorSettings'):
        self.settings = settings
    
    def configure_github(self, token: str, repo: str, 
                        branch: str = "main", path: str = "mattpad_sync"):
        """Configure GitHub sync settings."""
        SecretStorage.store("github_token", token)
        self.settings.github_token = token
        self.settings.github_repo = repo
        self.settings.github_branch = branch
        self.settings.github_path = path
        self.settings.sync_provider = "github"
        self.settings.cloud_sync_enabled = True
    
    def sync_file(self, filepath: str, content: str) -> Tuple[bool, str]:
        """Sync a file to the cloud."""
        if not self.settings.cloud_sync_enabled:
            return False, "Cloud sync not enabled"
        
        if self.settings.sync_provider == "github":
            return self._sync_to_github(filepath, content)
        
        return False, "Unknown sync provider"
    
    def sync_to_github(self, filepath: str, content: str) -> bool:
        """Sync file to GitHub (convenience method)."""
        success, _ = self._sync_to_github(filepath, content)
        return success
    
    def _sync_to_github(self, filepath: str, content: str) -> Tuple[bool, str]:
        """Internal GitHub sync implementation."""
        if not REQUESTS_AVAILABLE:
            return False, "requests library not available"
        
        try:
            token = SecretStorage.get("github_token", self.settings.github_token)
            if not token or not self.settings.github_repo:
                return False, "GitHub not configured"
            
            # Prepare file info
            filename = os.path.basename(filepath) if filepath else f"untitled_{int(time.time())}.txt"
            file_path = f"{self.settings.github_path}/{filename}"
            
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # GitHub API URL
            url = f"https://api.github.com/repos/{self.settings.github_repo}/contents/{file_path}"
            
            # Check if file exists (to get SHA for update)
            sha = None
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    params={"ref": self.settings.github_branch},
                    timeout=10
                )
                if response.status_code == 200:
                    sha = response.json().get("sha")
            except Exception:
                pass
            
            # Create or update file
            payload = {
                "message": f"Sync {filename} from Mattpad",
                "content": base64.b64encode(content.encode()).decode(),
                "branch": self.settings.github_branch
            }
            
            if sha:
                payload["sha"] = sha
            
            response = requests.put(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code in (200, 201):
                logger.info(f"Synced {filename} to GitHub")
                return True, "Sync successful"
            else:
                error = response.json().get("message", "Unknown error")
                logger.error(f"GitHub sync failed: {error}")
                return False, f"GitHub error: {error}"
                
        except Exception as e:
            logger.error(f"GitHub sync error: {e}")
            return False, str(e)
    
    def fetch_from_github(self, filename: str) -> Tuple[Optional[str], str]:
        """Fetch a file from GitHub."""
        if not REQUESTS_AVAILABLE:
            return None, "requests library not available"
        
        try:
            token = SecretStorage.get("github_token", self.settings.github_token)
            if not token or not self.settings.github_repo:
                return None, "GitHub not configured"
            
            file_path = f"{self.settings.github_path}/{filename}"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            url = f"https://api.github.com/repos/{self.settings.github_repo}/contents/{file_path}"
            
            response = requests.get(
                url,
                headers=headers,
                params={"ref": self.settings.github_branch},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                content = base64.b64decode(data["content"]).decode()
                return content, "Success"
            else:
                return None, f"File not found: {response.status_code}"
                
        except Exception as e:
            return None, str(e)
    
    def list_github_files(self) -> Tuple[list, str]:
        """List files in GitHub sync folder."""
        if not REQUESTS_AVAILABLE:
            return [], "requests library not available"
        
        try:
            token = SecretStorage.get("github_token", self.settings.github_token)
            if not token or not self.settings.github_repo:
                return [], "GitHub not configured"
            
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            url = f"https://api.github.com/repos/{self.settings.github_repo}/contents/{self.settings.github_path}"
            
            response = requests.get(
                url,
                headers=headers,
                params={"ref": self.settings.github_branch},
                timeout=10
            )
            
            if response.status_code == 200:
                files = []
                for item in response.json():
                    if item["type"] == "file":
                        files.append({
                            "name": item["name"],
                            "path": item["path"],
                            "size": item["size"],
                            "sha": item["sha"]
                        })
                return files, "Success"
            else:
                return [], f"Error: {response.status_code}"
                
        except Exception as e:
            return [], str(e)
