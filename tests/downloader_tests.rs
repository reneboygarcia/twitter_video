use std::path::{Path, PathBuf};
use twitdl::downloader::{normalize_path, TwitterDownloader};

#[test]
fn test_normalize_path() {
    let path = Path::new("/foo/bar/../baz");
    let normalized = normalize_path(path);
    assert_eq!(normalized, PathBuf::from("/foo/baz"));

    let path2 = Path::new("foo/./bar");
    let normalized2 = normalize_path(path2);
    assert_eq!(normalized2, PathBuf::from("foo/bar"));
}

#[test]
fn test_extract_tweet_id() {
    let downloader = TwitterDownloader::new();

    // Standard x.com URL
    let url1 = "https://x.com/NASA/status/1800000000000000000";
    assert_eq!(
        downloader.extract_tweet_id(url1).unwrap(),
        "1800000000000000000"
    );

    // Twitter.com URL with query parameters
    let url2 = "https://twitter.com/NASA/status/123456?s=20";
    assert_eq!(downloader.extract_tweet_id(url2).unwrap(), "123456");

    // Empty URL
    assert!(downloader.extract_tweet_id("").is_err());

    // Invalid numeric tweet ID
    assert!(downloader
        .extract_tweet_id("https://x.com/NASA/status/abc")
        .is_err());
    assert!(downloader
        .extract_tweet_id("https://x.com/NASA/status/")
        .is_err());
    assert!(downloader
        .extract_tweet_id("just_some_random_text_without_slashes")
        .is_err());
}

#[test]
fn test_get_log_file_path() {
    let downloader = TwitterDownloader::new();
    let log_file = downloader.get_log_file_path();
    assert_eq!(log_file.file_name().unwrap(), "download.log");
}

#[test]
fn test_is_safe_path() {
    let downloader = TwitterDownloader::new();

    // Critical Unix paths (should be blocked)
    assert!(!downloader.is_safe_path(Path::new("/System")));
    assert!(!downloader.is_safe_path(Path::new("/System/Library")));
    assert!(!downloader.is_safe_path(Path::new("/etc/passwd")));

    // Safe paths
    assert!(downloader.is_safe_path(Path::new("/Users/user/Downloads/video.mp4")));
    assert!(downloader.is_safe_path(Path::new("video.mp4")));
}

#[test]
fn test_get_output_path() {
    let downloader = TwitterDownloader::new();
    let url = "https://x.com/NASA/status/123456";

    // Default output path should be in Downloads folder
    let output_path = downloader.get_output_path(url, None).unwrap();
    assert_eq!(output_path.file_name().unwrap(), "twitter_video_123456.mp4");
    assert_eq!(
        output_path.parent().unwrap(),
        downloader.get_downloads_dir()
    );

    // Custom absolute path
    let custom_abs = "/tmp/my_video.mp4";
    let output_path_abs = downloader.get_output_path(url, Some(custom_abs)).unwrap();
    assert_eq!(output_path_abs, PathBuf::from(custom_abs));

    // Custom relative path (resolved against Downloads)
    let output_path_rel = downloader
        .get_output_path(url, Some("my_custom_folder/video.mp4"))
        .unwrap();
    assert_eq!(output_path_rel.file_name().unwrap(), "video.mp4");
    assert_eq!(
        output_path_rel.parent().unwrap().file_name().unwrap(),
        "my_custom_folder"
    );

    // Custom directory path
    let downloads_dir = downloader.get_downloads_dir();
    let output_path_dir = downloader
        .get_output_path(url, Some(&downloads_dir.to_string_lossy()))
        .unwrap();
    assert_eq!(
        output_path_dir.file_name().unwrap(),
        "twitter_video_123456.mp4"
    );
    assert_eq!(output_path_dir.parent().unwrap(), downloads_dir);
}

#[test]
fn test_get_output_path_traversal_prevention() {
    let downloader = TwitterDownloader::new();
    let url = "https://x.com/NASA/status/123456";

    // Directory traversal using relative path
    let err1 = downloader.get_output_path(url, Some("../traversal_test.mp4"));
    assert!(err1.is_err());
    assert!(err1.unwrap_err().contains("Path traversal detected"));

    let err2 = downloader.get_output_path(url, Some("subdir/../../traversal_test.mp4"));
    assert!(err2.is_err());
    assert!(err2.unwrap_err().contains("Path traversal detected"));
}

#[test]
fn test_get_output_path_system_write_safety() {
    let downloader = TwitterDownloader::new();
    let url = "https://x.com/NASA/status/123456";

    // System-critical absolute directory (block list check)
    let bad_abs_path = "/etc/passwd";
    let err1 = downloader.get_output_path(url, Some(bad_abs_path));
    assert!(err1.is_err());
    assert!(err1.unwrap_err().contains("Write safety violation"));

    let bad_abs_dir = "/System";
    let err2 = downloader.get_output_path(url, Some(bad_abs_dir));
    assert!(err2.is_err());
    assert!(err2.unwrap_err().contains("Write safety violation"));
}

#[test]
fn test_download_video_invalid_domain() {
    let downloader = TwitterDownloader::new();
    let url = "https://youtube.com/watch?v=dQw4w9WgXcQ";
    let err = downloader.download_video(url, None, "best");
    assert!(err.is_err());
    assert!(err
        .unwrap_err()
        .contains("Only Twitter/X URLs are supported"));
}

#[test]
fn test_download_video_failure() {
    let downloader = TwitterDownloader::new();
    let url = "https://x.com/NASA/status/0000000000000000000";
    let err = downloader.download_video(url, None, "best");
    assert!(err.is_err());
    assert!(err.unwrap_err().contains("Download failed"));
}

#[test]
fn test_get_video_info_failure() {
    let downloader = TwitterDownloader::new();
    let url = "https://x.com/NASA/status/0000000000000000000";
    let err = downloader.get_video_info(url);
    assert!(err.is_err());
    assert!(err.unwrap_err().contains("Could not fetch video info"));
}
