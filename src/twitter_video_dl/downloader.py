import os
import yt_dlp
from typing import Optional, Dict, Any
from pathlib import Path
from tqdm import tqdm
import logging
import platform


class TwitterDownloader:
    """Twitter Video Downloader with support for different qualities."""

    def __init__(self):
        """Initialize the downloader."""
        self._setup_logging()
        self._setup_quality_settings()

    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(), logging.FileHandler("download.log")],
        )
        self.logger = logging.getLogger(__name__)

    def _setup_quality_settings(self):
        """Setup video quality settings."""
        self.quality_settings = {
            "best": {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
            },
            "medium": {
                "format": "worstvideo[height>=480][ext=mp4]+worstaudio[ext=m4a]/worst[height>=480][ext=mp4]",
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
            return custom_path if custom_path.is_absolute() else downloads_dir / custom_path
        
        tweet_id = self._extract_tweet_id(url)
        return downloads_dir / f"twitter_video_{tweet_id}.mp4"

    def _create_progress_hook(self) -> Dict[str, Any]:
        """Create a progress hook for download tracking."""
        pbar = None

        def progress_hook(d):
            nonlocal pbar
            if d["status"] == "downloading":
                if pbar is None:
                    try:
                        total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                        pbar = tqdm(
                            total=total,
                            unit="B",
                            unit_scale=True,
                            desc="Downloading",
                            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
                        )
                    except Exception as e:
                        self.logger.error(f"Progress bar error: {e}")

                if pbar:
                    update = d.get("downloaded_bytes", 0) - pbar.n
                    if update > 0:
                        pbar.update(update)

            elif d["status"] == "finished" and pbar:
                pbar.close()
                print("\nProcessing video...")

            elif d["status"] == "error":
                if pbar:
                    pbar.close()
                print(f"\nError: {d.get('error')}")

        return {"progress_hooks": [progress_hook]}

    def _extract_tweet_id(self, url: str) -> str:
        """Extract tweet ID from URL."""
        try:
            # Handle both twitter.com and x.com URLs
            parts = url.split("/")
            return parts[-1].split("?")[0]
        except IndexError:
            raise ValueError("Invalid URL format. Could not extract tweet ID.")

    def download_video(self, url: str, output: Optional[str] = None, quality: str = "best") -> str:
        """Download video from Twitter URL."""
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
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        }

        # Add progress hooks
        ydl_opts.update(self._create_progress_hook())

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("Fetching video information...")
                video_info = ydl.extract_info(url, download=False)

                if not video_info:
                    raise ValueError("No video found in tweet")

                ydl.download([url])

                if not output_path.exists():
                    raise ValueError("Download failed - output file not found")

                return str(output_path)

        except yt_dlp.utils.DownloadError as e:
            error_msg = f"Download failed: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
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
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
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
