from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from twitter_video_dl.cli import main


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "interactive and command-line tool" in result.output
    assert "--quality" in result.output
    assert "--output" in result.output


@patch("twitter_video_dl.cli.TwitterDownloader")
def test_cli_direct_download_success(mock_downloader_class):
    mock_downloader = MagicMock()
    mock_downloader_class.return_value = mock_downloader
    mock_downloader.download_video.return_value = "/path/to/downloaded_video.mp4"

    runner = CliRunner()
    url = "https://x.com/NASA/status/123456"
    result = runner.invoke(main, [url, "-q", "medium", "-o", "custom_path.mp4"])

    assert result.exit_code == 0
    assert "Downloading video from:" in result.output
    assert (
        "Video downloaded successfully to: /path/to/downloaded_video.mp4"
        in result.output
    )
    mock_downloader.download_video.assert_called_once_with(
        url, "custom_path.mp4", "medium"
    )


@patch("twitter_video_dl.cli.TwitterDownloader")
def test_cli_direct_download_failure(mock_downloader_class):
    mock_downloader = MagicMock()
    mock_downloader_class.return_value = mock_downloader
    mock_downloader.download_video.side_effect = ValueError("Mocked download error")

    runner = CliRunner()
    url = "https://x.com/NASA/status/123456"
    result = runner.invoke(main, [url])

    assert result.exit_code == 1
    assert "Download failed: Mocked download error" in result.output


@patch("twitter_video_dl.cli.TwitterDownloaderCLI")
def test_cli_guide_mode(mock_cli_class):
    mock_cli = MagicMock()
    mock_cli_class.return_value = mock_cli

    runner = CliRunner()
    result = runner.invoke(main, ["--guide"])

    assert result.exit_code == 0
    mock_cli.show_welcome.assert_called_once()
    mock_cli.main_menu.assert_called_once()


@patch("twitter_video_dl.cli.TwitterDownloaderCLI")
def test_cli_interactive_fallback_without_url(mock_cli_class):
    mock_cli = MagicMock()
    mock_cli_class.return_value = mock_cli

    runner = CliRunner()
    result = runner.invoke(main, [])

    assert result.exit_code == 0
    mock_cli.show_welcome.assert_called_once()
    mock_cli.main_menu.assert_called_once()


@patch("twitter_video_dl.cli.TwitterDownloaderCLI")
def test_cli_url_with_guide_mode(mock_cli_class):
    mock_cli = MagicMock()
    mock_cli_class.return_value = mock_cli

    runner = CliRunner()
    url = "https://x.com/NASA/status/123456"
    result = runner.invoke(main, [url, "--guide"])

    assert result.exit_code == 0
    mock_cli.show_welcome.assert_called_once()
    mock_cli.main_menu.assert_called_once()
