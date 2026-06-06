import json
import os
import platform
import time
from pathlib import Path
from typing import Optional, Tuple

import requests

CACHE_EXPIRATION_SECONDS = 86400  # 24 hours


class UpdateChecker:
    """Checks for updates against GitHub Releases API with 24-hour caching."""

    def __init__(self, current_version: str):
        self.current_version = current_version.lstrip("v")
        self.cache_dir = self._get_cache_dir()
        self.cache_file = self.cache_dir / "update_cache.json"

    def _get_cache_dir(self) -> Path:
        """Get platform-specific cache/data folder."""
        home = Path.home()
        sys_platform = platform.system()

        if sys_platform == "Darwin":  # macOS
            return home / "Library" / "Caches" / "twitdl"
        elif sys_platform == "Windows":
            local_appdata = os.getenv("LOCALAPPDATA")
            return (
                Path(local_appdata) / "twitdl"
                if local_appdata
                else home / "AppData" / "Local" / "twitdl"
            )
        else:  # Linux / Unix
            return home / ".cache" / "twitdl"

    def _parse_version(self, version_str: str) -> Tuple[int, ...]:
        """Convert version string to integer tuple for comparison."""
        try:
            return tuple(map(int, version_str.lstrip("v").split(".")))
        except ValueError:
            return (0, 0, 0)

    def check_for_update(self) -> Optional[str]:
        """Check if an update is available.

        Returns:
            The latest version string if an update is available, otherwise None.
        """
        now = time.time()
        cached_version: Optional[str] = None
        last_check: float = 0.0

        # Try to read cached version check info
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                    cached_version = data.get("latest_version")
                    last_check = data.get("last_check", 0.0)
            except Exception:
                pass

        # Check GitHub if cache is expired or missing
        if not cached_version or (now - last_check) > CACHE_EXPIRATION_SECONDS:
            latest_version = self._fetch_latest_version_from_github()
            if latest_version:
                cached_version = latest_version
                try:
                    self.cache_dir.mkdir(parents=True, exist_ok=True)
                    with open(self.cache_file, "w") as f:
                        json.dump(
                            {
                                "latest_version": latest_version,
                                "last_check": now,
                            },
                            f,
                        )
                except Exception:
                    pass

        if cached_version:
            current = self._parse_version(self.current_version)
            latest = self._parse_version(cached_version)
            if latest > current:
                return cached_version

        return None

    def _fetch_latest_version_from_github(self) -> Optional[str]:
        """Fetch latest release tag name from GitHub Releases API."""
        url = (
            "https://api.github.com/repos/reneboygarcia/"
            "twitter_video/releases/latest"
        )
        headers = {"User-Agent": "twitdl-cli"}
        try:
            # Short timeout to avoid blocking the CLI for long if offline
            response = requests.get(url, headers=headers, timeout=1.5)
            if response.status_code == 200:
                data = response.json()
                tag = data.get("tag_name")
                if tag:
                    return tag.lstrip("v")
        except Exception:
            pass
        return None
