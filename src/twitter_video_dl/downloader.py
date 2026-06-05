import logging
import os
import platform
from pathlib import Path
from typing import Any, Dict, Optional

import yt_dlp
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
    DownloadColumn,
    SpinnerColumn,
)

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class TwitterDownloader:
    """Twitter Video Downloader with support for different qualities."""

    def __init__(self):
        """Initialize the downloader."""
        self._setup_logging()
        self._setup_quality_settings()

    def _get_log_file_path(self) -> Path:
        """Get the platform-specific path for log files."""
        home = Path.home()
        sys_platform = platform.system()

        if sys_platform == "Darwin":  # macOS
            log_dir = home / "Library" / "Logs" / "twitdl"
        elif sys_platform == "Windows":
            local_appdata = os.getenv("LOCALAPPDATA")
            log_dir = (
                Path(local_appdata) / "twitdl"
                if local_appdata
                else home / "AppData" / "Local" / "twitdl"
            )
        else:  # Linux and other Unix-like OSes
            log_dir = home / ".cache" / "twitdl"

        return log_dir / "download.log"

    def _setup_logging(self):
        """Setup logging configuration."""
        self.logger = logging.getLogger("twitter_video_dl")
        self.logger.setLevel(logging.INFO)

        # Avoid adding duplicate handlers if they are already registered
        if not self.logger.handlers:
            log_file = self._get_log_file_path()
            try:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file)
            except Exception:
                file_handler = logging.FileHandler("download.log")

            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)

    def _setup_quality_settings(self):
        """Setup video quality settings."""
        best_format = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        medium_format = (
            "worstvideo[height>=480][ext=mp4]+worstaudio[ext=m4a]/"
            "worst[height>=480][ext=mp4]"
        )
        self.quality_settings = {
            "best": {
                "format": best_format,
                "merge_output_format": "mp4",
            },
            "medium": {
                "format": medium_format,
                "merge_output_format": "mp4",
            },
            "low": {
                "format": "worst[ext=mp4]",
                "merge_output_format": "mp4",
            },
        }

    def _get_downloads_dir(self) -> Path:
        """Get the system's Downloads directory."""
        if platform.system() == "Windows":
            return Path.home() / "Downloads"
        elif platform.system() == "Darwin":  # macOS
            return Path.home() / "Downloads"
        else:  # Linux and others
            return Path.home() / "Downloads"

    def _get_output_path(self, url: str, output: Optional[str] = None) -> Path:
        """Generate output path for the video."""
        downloads_dir = self._get_downloads_dir()

        if output:
            custom_path = Path(output)
            if custom_path.is_dir() or output.endswith(("/", "\\")):
                custom_path.mkdir(parents=True, exist_ok=True)
                tweet_id = self._extract_tweet_id(url)
                return custom_path / f"twitter_video_{tweet_id}.mp4"

            resolved_path = (
                custom_path
                if custom_path.is_absolute()
                else downloads_dir / custom_path
            )

            if resolved_path.is_dir():
                tweet_id = self._extract_tweet_id(url)
                return resolved_path / f"twitter_video_{tweet_id}.mp4"

            return resolved_path

        tweet_id = self._extract_tweet_id(url)
        return downloads_dir / f"twitter_video_{tweet_id}.mp4"

    def _create_progress_hook(self, progress: Optional[Progress] = None, task: Optional[Any] = None) -> Dict[str, Any]:
        """Create a progress hook for download tracking."""
        local_progress = progress
        local_task = task
        is_local = progress is None

        def progress_hook(d):
            nonlocal local_progress, local_task
            if d["status"] == "downloading":
                if local_progress is None:
                    try:
                        total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                        local_progress = Progress(
                            SpinnerColumn(spinner_name="dots"),
                            TextColumn("[bold #1d9bf0]{task.description:<26}"),
                            BarColumn(bar_width=30, complete_style="#1d9bf0", finished_style="#00ba7c"),
                            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                            TextColumn("•"),
                            DownloadColumn(),
                            TextColumn("•"),
                            TransferSpeedColumn(),
                            TextColumn("•"),
                            TimeRemainingColumn(),
                        )
                        local_progress.start()
                        local_task = local_progress.add_task("Downloading", total=total)
                    except Exception as e:
                        self.logger.error(f"Progress bar error: {e}")

                if local_progress and local_task is not None:
                    update_kwargs = {"description": "Downloading", "completed": d.get("downloaded_bytes", 0)}
                    total = d.get("total_bytes") or d.get("total_bytes_estimate")
                    if total is not None:
                        update_kwargs["total"] = total
                    local_progress.update(local_task, **update_kwargs)

            elif d["status"] == "finished":
                if local_progress:
                    local_progress.update(local_task, description="Processing...")
                    if is_local:
                        try:
                            local_progress.stop()
                        except Exception:
                            pass
                        local_progress = None
                        local_task = None
                else:
                    print("\nProcessing video...")

            elif d["status"] == "error":
                if local_progress:
                    local_progress.update(local_task, description="Error")
                    if is_local:
                        try:
                            local_progress.stop()
                        except Exception:
                            pass
                        local_progress = None
                        local_task = None
                else:
                    print(f"\nError: {d.get('error')}")

        return {"progress_hooks": [progress_hook]}

    def _extract_tweet_id(self, url: str) -> str:
        """Extract tweet ID from URL."""
        if not url:
            raise ValueError("URL cannot be empty")
        try:
            parts = url.split("/")
            tweet_id = parts[-1].split("?")[0]
            if not tweet_id or not tweet_id.isdigit():
                raise ValueError("Could not extract a valid numeric tweet ID.")
            return tweet_id
        except (IndexError, ValueError) as e:
            raise ValueError(f"Invalid URL format: {str(e)}")

    def download_video(
        self, url: str, output: Optional[str] = None, quality: str = "best"
    ) -> str:
        """Download video from Twitter URL."""
        if not url.startswith(("https://twitter.com/", "https://x.com/")):
            raise ValueError("Only Twitter/X URLs are supported.")

        output_path = self._get_output_path(url, output)
        self.logger.info(f"Starting download process for: {url}")
        self.logger.info(f"Quality setting: {quality}")
        self.logger.info(f"Output path: {output_path}")

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # YT-DLP options
        ydl_opts = {
            **self.quality_settings[quality],
            "outtmpl": str(output_path),
            "quiet": True,  # Changed to True to avoid duplicate progress bars
            "no_warnings": False,
            "http_headers": {"User-Agent": DEFAULT_USER_AGENT},
            "concurrent_fragment_downloads": 5,
            "socket_timeout": 10,
            "retries": 3,
        }

        progress = Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold #1d9bf0]{task.description:<26}"),
            BarColumn(bar_width=30, complete_style="#1d9bf0", finished_style="#00ba7c"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            DownloadColumn(),
            TextColumn("•"),
            TransferSpeedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
        )

        try:
            with progress:
                task = progress.add_task("Resolving video stream...", total=None)
                ydl_opts.update(self._create_progress_hook(progress, task))

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                if not output_path.exists():
                    raise ValueError("Download failed - output file not found")

                return str(output_path)

        except yt_dlp.utils.DownloadError as e:
            error_msg = f"Download failed: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        except KeyboardInterrupt:
            self.logger.warning("Download process interrupted by user.")
            if output_path.exists():
                try:
                    output_path.unlink()
                except Exception:
                    pass
            # Also clean up any potential .part file
            part_path = output_path.with_suffix(output_path.suffix + ".part")
            if part_path.exists():
                try:
                    part_path.unlink()
                except Exception:
                    pass
            raise
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

    def get_video_info(self, url: str) -> dict:
        """
        Get information about the video without downloading.

        Args:
            url: Tweet URL containing the video

        Returns:
            dict: Video information including available qualities
        """
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "http_headers": {"User-Agent": DEFAULT_USER_AGENT},
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "title": info.get("title", "Untitled"),
                    "duration": info.get("duration", 0),
                    "formats": [
                        {
                            "format_id": f.get("format_id", ""),
                            "ext": f.get("ext", ""),
                            "filesize": f.get("filesize", 0),
                            "height": f.get("height", 0),
                        }
                        for f in info.get("formats", [])
                        if f.get("ext") == "mp4"
                    ],
                }
        except Exception as e:
            raise ValueError(f"Could not fetch video info: {str(e)}")
