use chrono::Local;
use serde::Deserialize;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::{Component, Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};

const DEFAULT_USER_AGENT: &str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36";

pub fn normalize_path(path: &Path) -> PathBuf {
    let mut components = Vec::new();
    for component in path.components() {
        match component {
            Component::ParentDir => {
                components.pop();
            }
            Component::CurDir => {}
            Component::Normal(c) => {
                components.push(c);
            }
            c => {
                components.push(c.as_os_str());
            }
        }
    }
    components.iter().collect()
}

#[allow(dead_code)]
#[derive(Deserialize, Debug, Clone)]
struct ProgressJson {
    status: Option<String>,
    downloaded_bytes: Option<u64>,
    total_bytes: Option<u64>,
    total_bytes_estimate: Option<u64>,
    speed: Option<f64>,
    eta: Option<u64>,
}

#[derive(Deserialize, Debug)]
pub struct VideoFormat {
    pub format_id: Option<String>,
    pub ext: Option<String>,
    pub filesize: Option<u64>,
    pub height: Option<u32>,
}

#[derive(Deserialize, Debug)]
pub struct VideoInfo {
    pub title: Option<String>,
    pub duration: Option<f64>,
    pub formats: Option<Vec<VideoFormat>>,
}

struct CleanupGuard {
    path: PathBuf,
    active: bool,
}

impl Drop for CleanupGuard {
    fn drop(&mut self) {
        if self.active {
            let _ = fs::remove_file(&self.path);

            // Try clean up different variations of .part files
            let part_path1 = self.path.with_extension("mp4.part");
            let _ = fs::remove_file(&part_path1);

            let part_path2 = PathBuf::from(format!("{}.part", self.path.display()));
            let _ = fs::remove_file(&part_path2);
        }
    }
}

pub struct TwitterDownloader {
    quality_settings: std::collections::HashMap<String, (&'static str, &'static str)>,
}

impl TwitterDownloader {
    pub fn new() -> Self {
        let mut quality_settings = std::collections::HashMap::new();
        quality_settings.insert(
            "best".to_string(),
            (
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "mp4",
            ),
        );
        quality_settings.insert(
            "medium".to_string(),
            (
                "worstvideo[height>=480][ext=mp4]+worstaudio[ext=m4a]/worst[height>=480][ext=mp4]",
                "mp4",
            ),
        );
        quality_settings.insert("low".to_string(), ("worst[ext=mp4]", "mp4"));

        Self { quality_settings }
    }

    pub fn get_log_file_path(&self) -> PathBuf {
        let mut path = if cfg!(target_os = "macos") {
            dirs::home_dir()
                .map(|h| h.join("Library").join("Logs"))
                .unwrap_or_else(|| PathBuf::from("."))
        } else if cfg!(target_os = "windows") {
            if let Some(local_appdata) = std::env::var_os("LOCALAPPDATA") {
                PathBuf::from(local_appdata)
            } else {
                dirs::home_dir()
                    .map(|h| h.join("AppData").join("Local"))
                    .unwrap_or_else(|| PathBuf::from("."))
            }
        } else {
            dirs::cache_dir().unwrap_or_else(|| PathBuf::from("."))
        };
        path.push("twitdl");
        path.push("download.log");
        path
    }

    pub fn log_info(&self, msg: &str) {
        let log_file = self.get_log_file_path();
        if let Some(parent) = log_file.parent() {
            let _ = fs::create_dir_all(parent);
        }

        let file_res = fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&log_file)
            .or_else(|_| {
                fs::OpenOptions::new()
                    .create(true)
                    .append(true)
                    .open("download.log")
            });

        if let Ok(mut file) = file_res {
            use std::io::Write;
            let timestamp = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
            let _ = writeln!(file, "{} - INFO - {}", timestamp, msg);
        }
    }

    pub fn get_downloads_dir(&self) -> PathBuf {
        dirs::download_dir()
            .unwrap_or_else(|| std::env::current_dir().unwrap_or_else(|_| PathBuf::from(".")))
    }

    pub fn is_safe_path(&self, path: &Path) -> bool {
        let normalized = normalize_path(path);
        let path_str = normalized.to_string_lossy();

        let critical_prefixes = [
            "/System",
            "/Library",
            "/private/etc",
            "/private/var",
            "/etc",
            "/bin",
            "/sbin",
            "/boot",
            "/dev",
            "/proc",
            "/sys",
            "/root",
        ];

        for prefix in &critical_prefixes {
            if path_str == *prefix || path_str.starts_with(&format!("{}/", prefix)) {
                return false;
            }
        }

        #[cfg(target_os = "windows")]
        {
            let path_lower = path_str.to_lowercase();
            let windir = std::env::var("windir")
                .unwrap_or_else(|_| "C:\\Windows".to_string())
                .to_lowercase();
            let sysdrive = std::env::var("SystemDrive")
                .unwrap_or_else(|_| "C:".to_string())
                .to_lowercase();

            let critical_prefixes_win = [
                windir,
                format!("{}\\\\windows", sysdrive),
                format!("{}\\\\program files", sysdrive),
                format!("{}\\\\program files (x86)", sysdrive),
            ];
            for prefix in &critical_prefixes_win {
                let norm_prefix = prefix.replace("\\", "/");
                let norm_path_lower = path_lower.replace("\\", "/");
                if norm_path_lower == norm_prefix
                    || norm_path_lower.starts_with(&format!("{}/", norm_prefix))
                {
                    return false;
                }
            }
        }

        true
    }

    pub fn extract_tweet_id(&self, url: &str) -> Result<String, String> {
        if url.is_empty() {
            return Err("URL cannot be empty".to_string());
        }

        let parts: Vec<&str> = url.split('/').collect();
        if parts.len() < 2 {
            return Err(
                "Invalid URL format: Could not extract a valid numeric tweet ID.".to_string(),
            );
        }

        let last_part = parts
            .last()
            .ok_or_else(|| "Invalid URL format".to_string())?;
        let tweet_id = last_part
            .split('?')
            .next()
            .ok_or_else(|| "Invalid URL format".to_string())?;

        if tweet_id.is_empty() || !tweet_id.chars().all(|c| c.is_ascii_digit()) {
            return Err("Could not extract a valid numeric tweet ID.".to_string());
        }

        Ok(tweet_id.to_string())
    }

    pub fn get_output_path(&self, url: &str, output: Option<&str>) -> Result<PathBuf, String> {
        let downloads_dir = self.get_downloads_dir();
        let tweet_id = self.extract_tweet_id(url)?;
        let downloads_dir_normalized = normalize_path(&downloads_dir);

        if let Some(out) = output {
            let custom_path = Path::new(out);
            let is_absolute = custom_path.is_absolute();

            let is_dir = out.ends_with('/')
                || out.ends_with('\\')
                || custom_path.is_dir()
                || custom_path == downloads_dir;

            let resolved_path = if is_absolute {
                normalize_path(custom_path)
            } else {
                normalize_path(&downloads_dir.join(custom_path))
            };

            // Traversal check for relative paths
            if !is_absolute {
                if !resolved_path.starts_with(&downloads_dir_normalized) {
                    return Err(
                        "Path traversal detected: path escapes downloads directory.".to_string()
                    );
                }
            }

            // Safety check against critical system directories
            if !self.is_safe_path(&resolved_path) {
                return Err(format!(
                    "Write safety violation: Output path '{}' is a restricted system location.",
                    resolved_path.display()
                ));
            }

            if is_dir {
                let _ = fs::create_dir_all(&resolved_path);
                Ok(resolved_path.join(format!("twitter_video_{}.mp4", tweet_id)))
            } else {
                if let Some(parent) = resolved_path.parent() {
                    let _ = fs::create_dir_all(parent);
                }
                Ok(resolved_path)
            }
        } else {
            let default_path = downloads_dir.join(format!("twitter_video_{}.mp4", tweet_id));
            let resolved_path = normalize_path(&default_path);
            if !self.is_safe_path(&resolved_path) {
                return Err(format!(
                    "Write safety violation: Default output path '{}' is a restricted system location.",
                    resolved_path.display()
                ));
            }
            Ok(resolved_path)
        }
    }

    pub fn check_ytdlp_installed(&self) -> Result<(), String> {
        let check = Command::new("yt-dlp")
            .arg("--version")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();

        match check {
            Ok(status) if status.success() => Ok(()),
            _ => Err("yt-dlp is not installed on your system. Please install it (e.g., run 'brew install yt-dlp') or ensure it is in your PATH.".to_string()),
        }
    }

    pub fn download_video(
        &self,
        url: &str,
        output: Option<&str>,
        quality: &str,
    ) -> Result<String, String> {
        if !url.starts_with("https://twitter.com/") && !url.starts_with("https://x.com/") {
            return Err("Only Twitter/X URLs are supported.".to_string());
        }

        self.check_ytdlp_installed()?;

        let output_path = self.get_output_path(url, output)?;
        self.log_info(&format!("Starting download process for: {}", url));
        self.log_info(&format!("Quality setting: {}", quality));
        self.log_info(&format!("Output path: {}", output_path.display()));

        if let Some(parent) = output_path.parent() {
            let _ = fs::create_dir_all(parent);
        }

        let quality_opts = self
            .quality_settings
            .get(quality)
            .ok_or_else(|| "Invalid quality setting".to_string())?;

        let mut child = Command::new("yt-dlp")
            .arg("-f")
            .arg(quality_opts.0)
            .arg("--merge-output-format")
            .arg(quality_opts.1)
            .arg("-o")
            .arg(&output_path)
            .arg("--no-warnings")
            .arg("--add-headers")
            .arg(format!("User-Agent:{}", DEFAULT_USER_AGENT))
            .arg("--concurrent-fragments")
            .arg("5")
            .arg("--socket-timeout")
            .arg("10")
            .arg("--retries")
            .arg("3")
            .arg("--progress-template")
            .arg("%(progress)j")
            .arg(url)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to spawn yt-dlp: {}", e))?;

        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| "Failed to open stdout of child".to_string())?;
        let reader = BufReader::new(stdout);

        let pb = indicatif::ProgressBar::new_spinner();
        pb.set_style(
            indicatif::ProgressStyle::default_spinner()
                .tick_chars("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
                .template("{spinner:.bold.white} {msg}")
                .unwrap(),
        );
        pb.set_message("Resolving video stream...");
        pb.enable_steady_tick(std::time::Duration::from_millis(80));

        let mut has_started = false;
        let child_id = child.id();

        // Safe cleanup guard setup
        let cleanup_guard = Arc::new(Mutex::new(CleanupGuard {
            path: output_path.clone(),
            active: true,
        }));

        // Set up ctrlc handler
        let cleanup_guard_clone = Arc::clone(&cleanup_guard);
        let _ = ctrlc::set_handler(move || {
            let mut guard = cleanup_guard_clone.lock().unwrap();
            // Kill child process
            let _ = Command::new("kill").arg(child_id.to_string()).status();
            guard.active = true;
            std::process::exit(130);
        });

        for line_res in reader.lines() {
            if let Ok(line) = line_res {
                if let Ok(progress_data) = serde_json::from_str::<ProgressJson>(&line) {
                    if let Some(ref status) = progress_data.status {
                        if status == "downloading" {
                            let downloaded = progress_data.downloaded_bytes.unwrap_or(0);
                            let total = progress_data
                                .total_bytes
                                .or(progress_data.total_bytes_estimate)
                                .unwrap_or(0);

                            if !has_started {
                                has_started = true;
                                pb.set_style(
                                    indicatif::ProgressStyle::default_bar()
                                        .template("{spinner:.bold.white} {msg:<26} [{bar:30.white/dim}] {percent:>3}% • {bytes}/{total_bytes} • {speed} • {eta}")
                                        .unwrap()
                                        .progress_chars("█░")
                                );
                                pb.set_message("Downloading");
                                pb.set_length(total);
                            }

                            pb.set_position(downloaded);
                            if total > 0 {
                                pb.set_length(total);
                            }
                        } else if status == "finished" {
                            pb.set_message("Processing...");
                        }
                    }
                }
            }
        }

        let status = child
            .wait()
            .map_err(|e| format!("Failed to wait on child: {}", e))?;
        pb.finish_and_clear();

        if status.success() {
            if output_path.exists() {
                // Disable cleanup guard since download succeeded
                cleanup_guard.lock().unwrap().active = false;
                Ok(output_path.to_string_lossy().into_owned())
            } else {
                Err("Download failed - output file not found".to_string())
            }
        } else {
            // Read stderr for detailed error
            let mut stderr_msg = String::new();
            if let Some(mut stderr) = child.stderr.take() {
                use std::io::Read;
                let _ = stderr.read_to_string(&mut stderr_msg);
            }
            if stderr_msg.is_empty() {
                Err("Download failed with non-zero exit status".to_string())
            } else {
                Err(format!("Download failed: {}", stderr_msg.trim()))
            }
        }
    }

    pub fn get_video_info(&self, url: &str) -> Result<VideoInfo, String> {
        self.check_ytdlp_installed()?;

        let output = Command::new("yt-dlp")
            .arg("--dump-json")
            .arg("--quiet")
            .arg("--no-warnings")
            .arg("--add-headers")
            .arg(format!("User-Agent:{}", DEFAULT_USER_AGENT))
            .arg(url)
            .output()
            .map_err(|e| format!("Failed to execute yt-dlp: {}", e))?;

        if !output.status.success() {
            let err_msg = String::from_utf8_lossy(&output.stderr);
            return Err(format!("Could not fetch video info: {}", err_msg.trim()));
        }

        let info: VideoInfo = serde_json::from_slice(&output.stdout)
            .map_err(|e| format!("Could not parse metadata: {}", e))?;

        // Filter formats to only include mp4
        let filtered_formats = info.formats.map(|formats| {
            formats
                .into_iter()
                .filter(|f| f.ext.as_deref() == Some("mp4"))
                .collect()
        });

        Ok(VideoInfo {
            title: info.title.or_else(|| Some("Untitled".to_string())),
            duration: info.duration.or_else(|| Some(0.0)),
            formats: filtered_formats,
        })
    }
}
