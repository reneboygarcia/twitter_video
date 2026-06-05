import platform
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from twitter_video_dl.downloader import TwitterDownloader


def test_extract_tweet_id():
    downloader = TwitterDownloader()

    # Test standard x.com URL
    url1 = "https://x.com/NASA/status/1800000000000000000"
    assert downloader._extract_tweet_id(url1) == "1800000000000000000"

    # Test twitter.com URL with query parameters
    url2 = "https://twitter.com/NASA/status/123456?s=20"
    assert downloader._extract_tweet_id(url2) == "123456"

    # Test malformed URL
    with pytest.raises(ValueError):
        downloader._extract_tweet_id("")


def test_get_log_file_path():
    downloader = TwitterDownloader()
    log_file = downloader._get_log_file_path()
    assert log_file.name == "download.log"
    assert isinstance(log_file, Path)


def test_get_output_path():
    downloader = TwitterDownloader()
    url = "https://x.com/NASA/status/123456"

    # Default output path should be in Downloads folder
    output_path = downloader._get_output_path(url)
    assert output_path.name == "twitter_video_123456.mp4"
    assert output_path.parent == downloader._get_downloads_dir()

    # Custom absolute path
    custom_abs = (
        "/tmp/my_video.mp4"
        if platform.system() != "Windows"
        else "C:\\temp\\my_video.mp4"
    )
    output_path = downloader._get_output_path(url, custom_abs)
    assert str(output_path) == custom_abs

    # Custom relative path (resolved against Downloads)
    output_path = downloader._get_output_path(url, "my_custom_folder/video.mp4")
    assert output_path.name == "video.mp4"
    assert output_path.parent.name == "my_custom_folder"


@patch("yt_dlp.YoutubeDL")
def test_download_video_success(mock_ytdl_class):
    mock_ytdl = MagicMock()
    mock_ytdl_class.return_value.__enter__.return_value = mock_ytdl

    mock_ytdl.extract_info.return_value = {"title": "Test Video"}

    downloader = TwitterDownloader()
    url = "https://x.com/NASA/status/123456"

    with patch("pathlib.Path.exists", return_value=True):
        output = downloader.download_video(url, quality="best")
        assert "twitter_video_123456.mp4" in output

    mock_ytdl_class.assert_called_once()
    mock_ytdl.download.assert_called_once_with([url])


def test_download_video_invalid_domain():
    downloader = TwitterDownloader()
    url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
    with pytest.raises(ValueError, match="Only Twitter/X URLs are supported"):
        downloader.download_video(url)
