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


def test_get_log_file_path_platforms():
    # Test Darwin
    with patch("platform.system", return_value="Darwin"):
        downloader = TwitterDownloader()
        log_file = downloader._get_log_file_path()
        assert "Library/Logs/twitdl" in log_file.as_posix()

    # Test Windows
    with patch("platform.system", return_value="Windows"), patch(
        "os.getenv", return_value="/custom/appdata"
    ):
        downloader = TwitterDownloader()
        log_file = downloader._get_log_file_path()
        assert "/custom/appdata/twitdl" in log_file.as_posix()

    # Test Windows fallback when LOCALAPPDATA environment variable is empty
    with patch("platform.system", return_value="Windows"), patch(
        "os.getenv", return_value=None
    ):
        downloader = TwitterDownloader()
        log_file = downloader._get_log_file_path()
        assert "AppData/Local/twitdl" in log_file.as_posix()

    # Test Linux / Other
    with patch("platform.system", return_value="Linux"):
        downloader = TwitterDownloader()
        log_file = downloader._get_log_file_path()
        assert ".cache/twitdl" in log_file.as_posix()


def test_get_downloads_dir_platforms():
    # Test Darwin
    with patch("platform.system", return_value="Darwin"):
        downloader = TwitterDownloader()
        dl_dir = downloader._get_downloads_dir()
        assert dl_dir == Path.home() / "Downloads"

    # Test Windows
    with patch("platform.system", return_value="Windows"):
        downloader = TwitterDownloader()
        dl_dir = downloader._get_downloads_dir()
        assert dl_dir == Path.home() / "Downloads"

    # Test Linux
    with patch("platform.system", return_value="Linux"):
        downloader = TwitterDownloader()
        dl_dir = downloader._get_downloads_dir()
        assert dl_dir == Path.home() / "Downloads"


def test_setup_logging_fallback():
    import logging

    # Make Path.mkdir raise an OSError/Exception to trigger fallback to "download.log"
    with patch("pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")):
        downloader = TwitterDownloader()
        # Clear existing handlers to trigger the setup block
        downloader.logger.handlers.clear()
        downloader._setup_logging()
        handlers = downloader.logger.handlers
        assert len(handlers) > 0
        file_handlers = [h for h in handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0
        assert file_handlers[0].baseFilename.endswith("download.log")


def test_extract_tweet_id_failures():
    downloader = TwitterDownloader()

    # Test URL with invalid (non-numeric) status ID
    with pytest.raises(ValueError, match="Could not extract a valid numeric tweet ID"):
        downloader._extract_tweet_id("https://x.com/NASA/status/abc")

    # Test URL with empty status ID
    with pytest.raises(ValueError, match="Could not extract a valid numeric tweet ID"):
        downloader._extract_tweet_id("https://x.com/NASA/status/")

    # Test URL that causes split index issues
    with pytest.raises(ValueError, match="Invalid URL format"):
        downloader._extract_tweet_id("just_some_random_text_without_slashes")


def test_progress_hook_callback():
    downloader = TwitterDownloader()
    hook_dict = downloader._create_progress_hook()
    progress_hook = hook_dict["progress_hooks"][0]

    # 1. Test status "downloading" with total_bytes
    with patch("twitter_video_dl.downloader.tqdm") as mock_tqdm:
        mock_pbar = mock_tqdm.return_value
        mock_pbar.n = 0

        # Initial call creates progress bar
        progress_hook(
            {"status": "downloading", "total_bytes": 1000, "downloaded_bytes": 100}
        )
        mock_tqdm.assert_called_once()
        mock_pbar.update.assert_called_once_with(100)

        # Subsequent call updates progress bar
        mock_pbar.n = 100
        mock_pbar.update.reset_mock()
        progress_hook(
            {"status": "downloading", "total_bytes": 1000, "downloaded_bytes": 250}
        )
        mock_pbar.update.assert_called_once_with(150)

    # 2. Test status "downloading" with total_bytes_estimate
    with patch("twitter_video_dl.downloader.tqdm") as mock_tqdm:
        mock_pbar = mock_tqdm.return_value
        mock_pbar.n = 0
        progress_hook = downloader._create_progress_hook()["progress_hooks"][0]
        progress_hook(
            {
                "status": "downloading",
                "total_bytes_estimate": 500,
                "downloaded_bytes": 50,
            }
        )
        mock_tqdm.assert_called_once()

    # 3. Test progress bar creation error
    with patch(
        "twitter_video_dl.downloader.tqdm", side_effect=Exception("tqdm init failed")
    ):
        progress_hook = downloader._create_progress_hook()["progress_hooks"][0]
        with patch.object(downloader.logger, "error") as mock_log_error:
            progress_hook(
                {"status": "downloading", "total_bytes": 1000, "downloaded_bytes": 100}
            )
            mock_log_error.assert_called_once_with(
                "Progress bar error: tqdm init failed"
            )

    # 4. Test status "finished"
    with patch("twitter_video_dl.downloader.tqdm") as mock_tqdm:
        mock_pbar = mock_tqdm.return_value
        mock_pbar.n = 0
        progress_hook = downloader._create_progress_hook()["progress_hooks"][0]
        # Initialize pbar
        progress_hook(
            {"status": "downloading", "total_bytes": 1000, "downloaded_bytes": 100}
        )
        # Finished call should close it
        progress_hook({"status": "finished"})
        mock_pbar.close.assert_called_once()

    # 5. Test status "error"
    with patch("twitter_video_dl.downloader.tqdm") as mock_tqdm:
        mock_pbar = mock_tqdm.return_value
        mock_pbar.n = 0
        progress_hook = downloader._create_progress_hook()["progress_hooks"][0]
        # Initialize pbar
        progress_hook(
            {"status": "downloading", "total_bytes": 1000, "downloaded_bytes": 100}
        )
        # Error call should close it
        progress_hook({"status": "error", "error": "Download error occurred"})
        mock_pbar.close.assert_called_once()


@patch("yt_dlp.YoutubeDL")
def test_download_video_errors(mock_ytdl_class):
    import yt_dlp

    downloader = TwitterDownloader()
    url = "https://x.com/NASA/status/123456"

    # 1. Output file not found after mock download
    mock_ytdl = MagicMock()
    mock_ytdl_class.return_value.__enter__.return_value = mock_ytdl

    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(ValueError, match="Download failed - output file not found"):
            downloader.download_video(url)

    # 2. DownloadError from yt-dlp
    mock_ytdl.download.side_effect = yt_dlp.utils.DownloadError("Mocked yt-dlp error")
    with patch("pathlib.Path.exists", return_value=True):
        with pytest.raises(ValueError, match="Download failed: Mocked yt-dlp error"):
            downloader.download_video(url)

    # 3. Unexpected Exception from yt-dlp
    mock_ytdl.download.side_effect = RuntimeError("Something went wrong internally")
    with patch("pathlib.Path.exists", return_value=True):
        with pytest.raises(
            ValueError, match="Unexpected error: Something went wrong internally"
        ):
            downloader.download_video(url)


@patch("yt_dlp.YoutubeDL")
def test_download_video_keyboard_interrupt(mock_ytdl_class):
    downloader = TwitterDownloader()
    url = "https://x.com/NASA/status/123456"
    mock_ytdl = MagicMock()
    mock_ytdl_class.return_value.__enter__.return_value = mock_ytdl
    mock_ytdl.download.side_effect = KeyboardInterrupt()

    with patch("pathlib.Path.exists") as mock_exists, patch(
        "pathlib.Path.unlink"
    ) as mock_unlink:

        mock_exists.return_value = True

        with pytest.raises(KeyboardInterrupt):
            downloader.download_video(url)

        assert mock_exists.call_count >= 2
        assert mock_unlink.call_count == 2


@patch("yt_dlp.YoutubeDL")
def test_get_video_info_success(mock_ytdl_class):
    mock_ytdl = MagicMock()
    mock_ytdl_class.return_value.__enter__.return_value = mock_ytdl

    mock_ytdl.extract_info.return_value = {
        "title": "NASA Launch",
        "duration": 42.5,
        "formats": [
            {"format_id": "1", "ext": "mp4", "filesize": 1000, "height": 720},
            {"format_id": "2", "ext": "webm", "filesize": 800, "height": 720},
            {"format_id": "3", "ext": "mp4", "filesize": 500, "height": 360},
        ],
    }

    downloader = TwitterDownloader()
    url = "https://x.com/NASA/status/123456"

    info = downloader.get_video_info(url)

    assert info["title"] == "NASA Launch"
    assert info["duration"] == 42.5
    assert len(info["formats"]) == 2
    assert info["formats"][0]["format_id"] == "1"
    assert info["formats"][1]["format_id"] == "3"
    mock_ytdl.extract_info.assert_called_once_with(url, download=False)


@patch("yt_dlp.YoutubeDL")
def test_get_video_info_failure(mock_ytdl_class):
    mock_ytdl = MagicMock()
    mock_ytdl_class.return_value.__enter__.return_value = mock_ytdl
    mock_ytdl.extract_info.side_effect = RuntimeError("Could not retrieve metadata")

    downloader = TwitterDownloader()
    url = "https://x.com/NASA/status/123456"

    with pytest.raises(
        ValueError, match="Could not fetch video info: Could not retrieve metadata"
    ):
        downloader.get_video_info(url)
