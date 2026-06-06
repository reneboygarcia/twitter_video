import json
import time
from unittest.mock import MagicMock, patch

import requests

from twitter_video_dl.update_checker import UpdateChecker


def test_version_parsing():
    checker = UpdateChecker("0.1.2")
    assert checker._parse_version("0.1.2") == (0, 1, 2)
    assert checker._parse_version("v1.2.3") == (1, 2, 3)
    assert checker._parse_version("invalid") == (0, 0, 0)


@patch("twitter_video_dl.update_checker.UpdateChecker._get_cache_dir")
def test_cache_file_paths(mock_get_cache_dir, tmp_path):
    mock_get_cache_dir.return_value = tmp_path
    checker = UpdateChecker("0.1.2")
    assert checker.cache_file == tmp_path / "update_cache.json"


@patch("twitter_video_dl.update_checker.UpdateChecker._get_cache_dir")
@patch("requests.get")
def test_check_for_update_no_nudge(mock_get, mock_get_cache_dir, tmp_path):
    mock_get_cache_dir.return_value = tmp_path
    checker = UpdateChecker("0.1.2")

    # Mock no update available
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"tag_name": "v0.1.2"}
    mock_get.return_value = mock_response

    # First check fetches from GitHub and caches
    result = checker.check_for_update()
    assert result is None
    assert mock_get.call_count == 1
    assert checker.cache_file.exists()

    # Second check uses cache and doesn't call GitHub
    mock_get.reset_mock()
    result = checker.check_for_update()
    assert result is None
    assert mock_get.call_count == 0


@patch("twitter_video_dl.update_checker.UpdateChecker._get_cache_dir")
@patch("requests.get")
def test_check_for_update_nudge(mock_get, mock_get_cache_dir, tmp_path):
    mock_get_cache_dir.return_value = tmp_path
    checker = UpdateChecker("0.1.2")

    # Mock new version available
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"tag_name": "v0.1.3"}
    mock_get.return_value = mock_response

    # First check fetches and returns new version
    result = checker.check_for_update()
    assert result == "0.1.3"
    assert mock_get.call_count == 1

    # Second check uses cache and still returns new version
    mock_get.reset_mock()
    result = checker.check_for_update()
    assert result == "0.1.3"
    assert mock_get.call_count == 0


@patch("twitter_video_dl.update_checker.UpdateChecker._get_cache_dir")
@patch("requests.get")
def test_check_for_update_cache_expiration(mock_get, mock_get_cache_dir, tmp_path):
    mock_get_cache_dir.return_value = tmp_path
    checker = UpdateChecker("0.1.2")

    # Write old cache (older than 24 hours)
    old_time = time.time() - 90000
    checker.cache_dir.mkdir(parents=True, exist_ok=True)
    with open(checker.cache_file, "w") as f:
        json.dump({"latest_version": "0.1.1", "last_check": old_time}, f)

    # Mock new version
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"tag_name": "v0.1.3"}
    mock_get.return_value = mock_response

    # Check should expire cache, call GitHub, and return new version
    result = checker.check_for_update()
    assert result == "0.1.3"
    assert mock_get.call_count == 1

    # Verify cache got updated
    with open(checker.cache_file, "r") as f:
        data = json.load(f)
        assert data["latest_version"] == "0.1.3"
        assert data["last_check"] > old_time


@patch("twitter_video_dl.update_checker.UpdateChecker._get_cache_dir")
@patch("requests.get")
def test_check_for_update_network_failure(mock_get, mock_get_cache_dir, tmp_path):
    mock_get_cache_dir.return_value = tmp_path
    checker = UpdateChecker("0.1.2")

    # Mock requests exception
    mock_get.side_effect = requests.RequestException("Network down")

    # Should handle gracefully and return None
    result = checker.check_for_update()
    assert result is None
    assert mock_get.call_count == 1
