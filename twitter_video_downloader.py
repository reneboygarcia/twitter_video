import requests
import os
import yt_dlp as youtube_dl
from yt_dlp.utils import DownloadError
from tqdm import tqdm

print("Setup Complete")


def progress_hook(d):
    if d['status'] == 'downloading':
        pbar.update(d['downloaded_bytes'] - pbar.n)
    elif d['status'] == 'finished':
        pbar.close()


def download_twitter_video(url: str) -> None:
    """
    Downloads a video from Twitter/X using yt-dlp.
    
    Args:
        url (str): URL of the Twitter/X video to download
        
    Returns:
        None
    """
    try:
        # Convert x.com URLs to twitter.com
        url = url.replace('x.com', 'twitter.com')
        
        # Create output directory if needed
        output_dir = 'output_video'
        os.makedirs(output_dir, exist_ok=True)
        
        # Configure yt-dlp options
        ydl_opts = {
            'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
            'format': 'best',
            'quiet': False,
            'no_warnings': False,
            'extract_flat': True,  # Add this to handle Twitter's new structure
            'progress_hooks': [progress_hook]
        }
        
        # Download video
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            global pbar
            info_dict = ydl.extract_info(url, download=False)
            total_bytes = info_dict.get('filesize', 0)
            pbar = tqdm(total=total_bytes, unit='B', unit_scale=True, desc='Downloading')
            ydl.download([url])
            print("Download successful!")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    twitter_video_url = input("Copy and paste the Twitter/X video URL here: ")
    download_twitter_video(twitter_video_url)
