use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

const CACHE_EXPIRATION_SECONDS: u64 = 86400; // 24 hours

#[derive(Serialize, Deserialize, Debug, Clone)]
struct CacheData {
    latest_version: String,
    last_check: u64,
}

pub struct UpdateChecker {
    current_version: String,
    cache_file: PathBuf,
}

impl UpdateChecker {
    pub fn new(current_version: &str) -> Self {
        let current_version = current_version.trim_start_matches('v').to_string();
        let cache_dir = Self::get_cache_dir();
        let cache_file = cache_dir.join("update_cache.json");
        Self {
            current_version,
            cache_file,
        }
    }

    pub fn new_with_cache_file(current_version: &str, cache_file: PathBuf) -> Self {
        let current_version = current_version.trim_start_matches('v').to_string();
        Self {
            current_version,
            cache_file,
        }
    }

    fn get_cache_dir() -> PathBuf {
        if let Some(mut cache_dir) = dirs::cache_dir() {
            cache_dir.push("twitdl");
            cache_dir
        } else {
            // Fallback to home cache directory
            let mut path = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
            path.push(".cache");
            path.push("twitdl");
            path
        }
    }

    fn parse_version(version_str: &str) -> Vec<u32> {
        version_str
            .trim_start_matches('v')
            .split('.')
            .map(|s| s.parse::<u32>().unwrap_or(0))
            .collect()
    }

    pub fn check_for_update(&self) -> Option<String> {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        let mut cached_version: Option<String> = None;
        let mut last_check: u64 = 0;

        // Try reading cache
        if self.cache_file.exists() {
            if let Ok(content) = fs::read_to_string(&self.cache_file) {
                if let Ok(cache) = serde_json::from_str::<CacheData>(&content) {
                    cached_version = Some(cache.latest_version);
                    last_check = cache.last_check;
                }
            }
        }

        // Check GitHub if cache is expired or missing
        if cached_version.is_none() || (now - last_check) > CACHE_EXPIRATION_SECONDS {
            if let Some(latest_version) = self.fetch_latest_version_from_github() {
                cached_version = Some(latest_version.clone());
                // Write to cache
                let cache_data = CacheData {
                    latest_version,
                    last_check: now,
                };
                if let Some(parent) = self.cache_file.parent() {
                    let _ = fs::create_dir_all(parent);
                }
                if let Ok(json_str) = serde_json::to_string(&cache_data) {
                    let _ = fs::write(&self.cache_file, json_str);
                }
            }
        }

        if let Some(ref version) = cached_version {
            let current = Self::parse_version(&self.current_version);
            let latest = Self::parse_version(version);
            if latest > current {
                return cached_version;
            }
        }

        None
    }

    fn fetch_latest_version_from_github(&self) -> Option<String> {
        let url = "https://api.github.com/repos/reneboygarcia/twitter_video/releases/latest";

        let agent = ureq::AgentBuilder::new()
            .timeout(std::time::Duration::from_millis(1500))
            .build();

        let response = agent.get(url).set("User-Agent", "twitdl-cli").call();

        if let Ok(res) = response {
            if res.status() == 200 {
                #[derive(Deserialize)]
                struct GithubRelease {
                    tag_name: String,
                }
                if let Ok(release) = res.into_json::<GithubRelease>() {
                    return Some(release.tag_name.trim_start_matches('v').to_string());
                }
            }
        }
        None
    }
}
