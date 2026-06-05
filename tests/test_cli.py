from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from twitter_video_dl.cli import (TwitterDownloaderCLI, handle_back_option,
                                  handle_errors, main)


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


def test_decorator_handle_back_option():
    @handle_back_option
    def mock_input(val):
        return val

    assert mock_input("back") is None
    assert mock_input("BACK") is None
    assert mock_input("some_value") == "some_value"
    assert mock_input(None) is None


def test_decorator_handle_errors():
    @handle_errors
    def mock_function_success():
        return "success"

    @handle_errors
    def mock_function_failure():
        raise RuntimeError("Something failed")

    assert mock_function_success() == "success"
    # Verify failure prints error and returns None without crash
    with patch("twitter_video_dl.cli.console.print") as mock_print:
        res = mock_function_failure()
        assert res is None
        assert mock_print.call_count >= 2


def test_cli_show_welcome_and_info():
    cli = TwitterDownloaderCLI()
    with patch("twitter_video_dl.cli.console.print") as mock_print:
        cli.show_welcome()
        mock_print.assert_called_once()

    with patch("twitter_video_dl.cli.console.print") as mock_print:
        cli.show_info()
        mock_print.assert_called_once()


@patch("questionary.text")
def test_cli_get_tweet_url(mock_text):
    cli = TwitterDownloaderCLI()
    mock_prompt = MagicMock()
    mock_text.return_value = mock_prompt

    # 1. Valid URL path
    mock_prompt.ask.return_value = "https://x.com/NASA/status/123"
    assert cli._get_tweet_url() == "https://x.com/NASA/status/123"

    # 2. 'back' option path (from decorator)
    mock_prompt.ask.return_value = "back"
    assert cli._get_tweet_url() is None

    # 3. None option path
    mock_prompt.ask.return_value = None
    assert cli._get_tweet_url() is None


@patch("questionary.select")
def test_cli_main_menu_exit_paths(mock_select):
    import pytest

    cli = TwitterDownloaderCLI()
    mock_prompt = MagicMock()
    mock_select.return_value = mock_prompt

    # 1. User selects "Exit" - should call sys.exit
    mock_prompt.ask.return_value = "Exit"
    with pytest.raises(SystemExit):
        cli.main_menu()

    # 2. User presses Esc (returns None) - should call sys.exit
    mock_prompt.ask.return_value = None
    with pytest.raises(SystemExit):
        cli.main_menu()

    # 3. KeyboardInterrupt raised in menu loop
    mock_prompt.ask.side_effect = KeyboardInterrupt
    with pytest.raises(SystemExit):
        cli.main_menu()


@patch("questionary.select")
def test_cli_main_menu_navigation(mock_select):
    import pytest

    cli = TwitterDownloaderCLI()
    mock_prompt = MagicMock()
    mock_select.return_value = mock_prompt

    # Loop needs to execute a flow then exit (we raise SystemExit to break the loop)
    # We will mock the choice to be "Show information" then "Exit"
    mock_prompt.ask.side_effect = ["Show information", "Exit"]

    with patch.object(cli, "show_info") as mock_show_info, pytest.raises(SystemExit):
        cli.main_menu()

    mock_show_info.assert_called_once()


@patch("twitter_video_dl.cli.TwitterDownloader")
@patch("questionary.select")
@patch("questionary.path")
@patch("questionary.text")
def test_cli_download_workflow_paths(
    mock_text, mock_path, mock_select, mock_downloader_class
):
    mock_downloader = MagicMock()
    mock_downloader_class.return_value = mock_downloader

    cli = TwitterDownloaderCLI()
    cli.initialize_downloader()

    # 0. User escapes or types "back" on Tweet URL input
    mock_text.return_value.ask.return_value = None
    cli.download_workflow()
    mock_downloader.download_video.assert_not_called()

    # Re-enable valid tweet URL for subsequent subtests
    mock_text.return_value.ask.return_value = "https://x.com/NASA/status/123"

    # 1. Back/Esc on quality choice
    # select choices: quality choice, use custom path choice
    mock_select.return_value.ask.return_value = "⟵ Back"
    cli.download_workflow()  # Should return without calling downloader
    mock_downloader.download_video.assert_not_called()

    # 2. Back/Esc on custom path choice
    mock_select.return_value.ask.side_effect = ["best", "⟵ Back"]
    cli.download_workflow()
    mock_downloader.download_video.assert_not_called()

    # 3. Custom path "No" and download success
    mock_select.return_value.ask.side_effect = ["best", "No"]
    mock_downloader.download_video.return_value = "/downloads/video.mp4"
    cli.download_workflow()
    mock_downloader.download_video.assert_called_once_with(
        "https://x.com/NASA/status/123", None, "best"
    )

    # Reset mock for next subtest
    mock_downloader.download_video.reset_mock()

    # 4. Custom path "Yes" with standard path input
    mock_select.return_value.ask.side_effect = ["best", "Yes"]
    mock_path.return_value.ask.return_value = "/custom/dir/video.mp4"
    mock_downloader.download_video.return_value = "/custom/dir/video.mp4"
    cli.download_workflow()
    mock_downloader.download_video.assert_called_once_with(
        "https://x.com/NASA/status/123", "/custom/dir/video.mp4", "best"
    )

    mock_downloader.download_video.reset_mock()

    # 5. Custom path "Yes" with "back" text
    mock_select.return_value.ask.side_effect = ["best", "Yes"]
    mock_path.return_value.ask.return_value = "back"
    cli.download_workflow()
    mock_downloader.download_video.assert_not_called()

    # 6. Custom path "Yes" with Esc/None path input
    mock_select.return_value.ask.side_effect = ["best", "Yes"]
    mock_path.return_value.ask.return_value = None
    cli.download_workflow()
    mock_downloader.download_video.assert_not_called()

    # 7. Downloader throws ValueError
    mock_select.return_value.ask.side_effect = ["best", "No"]
    mock_downloader.download_video.side_effect = ValueError("Failed to get stream")
    with patch("twitter_video_dl.cli.console.print") as mock_print:
        cli.download_workflow()
        assert any(
            "Download failed" in call[0][0] for call in mock_print.call_args_list
        )

    # Reset side effect
    mock_downloader.download_video.side_effect = None
    mock_downloader.download_video.reset_mock()

    # 8. KeyboardInterrupt in download flow
    mock_select.return_value.ask.side_effect = KeyboardInterrupt
    with patch("twitter_video_dl.cli.console.print") as mock_print:
        cli.download_workflow()
        assert any(
            "Download cancelled" in call[0][0] for call in mock_print.call_args_list
        )


def test_main_cli_keyboard_interrupt():
    with patch(
        "twitter_video_dl.cli.TwitterDownloaderCLI", side_effect=KeyboardInterrupt
    ), patch("twitter_video_dl.cli.console.print") as mock_print:
        from click.testing import CliRunner

        from twitter_video_dl.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["--guide"])
        assert result.exit_code == 0

    assert any(
        "Operation cancelled" in call[0][0] for call in mock_print.call_args_list
    )
