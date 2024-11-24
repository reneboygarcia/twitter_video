import os
import requests
import yt_dlp
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

class TwitterDownloader:
    """Twitter Video Downloader with support for different qualities."""
    
    def __init__(self):
        """Initialize the downloader with API credentials."""
        load_dotenv()
        self.bearer_token = os.getenv("BEARER_TOKEN")
        if not self.bearer_token:
            raise ValueError("Bearer token not found. Please run 'twitdl config setup' first.")
        
        # Quality settings mapping
        self.quality_settings = {
            'best': {'format': 'bestvideo+bestaudio/best'},
            'medium': {'format': 'worstvideo[height>=480]+worstaudio/worst[height>=480]'},
            'low': {'format': 'worstvideo+worstaudio/worst'}
        }

    def _extract_tweet_id(self, url: str) -> str:
        """Extract tweet ID from URL."""
        try:
            # Handle both twitter.com and x.com URLs
            parts = url.split('/')
            return parts[-1].split('?')[0]
        except IndexError:
            raise ValueError("Invalid URL format. Could not extract tweet ID.")

    def _get_output_path(self, url: str, output: Optional[str]) -> Path:
        """Generate output path for the video."""
        if output:
            return Path(output)
        
        tweet_id = self._extract_tweet_id(url)
        return Path(f"tweet_{tweet_id}.mp4")

    def download_video(self, url: str, output: Optional[str] = None, quality: str = 'best') -> str:
        """
        Download video from Twitter URL.
        
        Args:
            url: Tweet URL containing the video
            output: Optional custom output path
            quality: Video quality ('best', 'medium', 'low')
            
        Returns:
            str: Path to the downloaded video file
        """
        output_path = self._get_output_path(url, output)
        
        # YT-DLP options
        ydl_opts = {
            **self.quality_settings[quality],
            'outtmpl': str(output_path),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            # Add custom headers for Twitter
            'http_headers': {
                'Authorization': f'Bearer {self.bearer_token}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video information first
                video_info = ydl.extract_info(url, download=False)
                if not video_info:
                    raise ValueError("No video found in tweet")

                # Download the video
                ydl.download([url])

                # Verify the download
                if not output_path.exists():
                    raise ValueError("Download failed - output file not found")

                return str(output_path)

        except yt_dlp.utils.DownloadError as e:
            raise ValueError(f"Download failed: {str(e)}")
        except Exception as e:
            raise ValueError(f"An error occurred: {str(e)}")

    def verify_credentials(self) -> bool:
        """Verify that the bearer token is valid."""
        test_url = "https://api.twitter.com/2/tweets?ids=1"
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        
        try:
            response = requests.get(test_url, headers=headers)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_video_info(self, url: str) -> dict:
        """
        Get information about the video without downloading.
        
        Args:
            url: Tweet URL containing the video
            
        Returns:
            dict: Video information including available qualities
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'http_headers': {
                'Authorization': f'Bearer {self.bearer_token}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Untitled'),
                    'duration': info.get('duration', 0),
                    'formats': [
                        {
                            'format_id': f.get('format_id', ''),
                            'ext': f.get('ext', ''),
                            'filesize': f.get('filesize', 0),
                            'height': f.get('height', 0)
                        }
                        for f in info.get('formats', [])
                        if f.get('ext') == 'mp4'
                    ]
                }
        except Exception as e:
            raise ValueError(f"Could not fetch video info: {str(e)}") 