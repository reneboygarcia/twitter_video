use clap::Parser;
use console::style;
use inquire::{
    ui::{Color, RenderConfig, StyleSheet, Styled},
    Select, Text,
};
use std::time::Instant;
use twitdl::downloader::TwitterDownloader;
use twitdl::update_checker::UpdateChecker;

const VERSION: &str = env!("CARGO_PKG_VERSION");

#[derive(Parser, Debug)]
#[command(
    name = "twitdl",
    version = VERSION,
    about = "An interactive and command-line tool to download videos from Twitter/X",
    long_about = None
)]
struct Args {
    /// The tweet URL to download the video from
    url: Option<String>,

    /// Video quality settings (best, medium, low)
    #[arg(short, long, value_parser = ["best", "medium", "low"])]
    quality: Option<String>,

    /// Output directory or filename path
    #[arg(short, long)]
    output: Option<String>,

    /// Force interactive guided mode
    #[arg(short, long)]
    guide: bool,
}

struct TwitterDownloaderCLI {
    downloader: TwitterDownloader,
}

impl TwitterDownloaderCLI {
    fn new() -> Self {
        Self {
            downloader: TwitterDownloader::new(),
        }
    }

    fn show_welcome(&self) {
        let ascii_art = vec![
            " ______  __     __   __   ______  _____    __",
            "/\\__  _\\/\\ \\  _ \\ \\ /\\ \\ /\\__  _\\/\\  __-. /\\ \\",
            "\\/_/\\ \\/\\ \\ \\/ \".\\ \\\\ \\ \\\\/_/\\ \\/\\ \\ \\/\\ \\\\ \\ \\____",
            "   \\ \\_\\ \\ \\__/\".~\\_\\\\ \\_\\  \\ \\_\\ \\ \\____- \\ \\_____\\",
            "    \\/_/  \\/_/   \\/_/ \\/_/   \\/_/  \\/____/  \\/_____/",
        ];

        println!();
        for line in ascii_art {
            // First 33 chars are stylized #1da1f2 (cyan-ish), rest is dim gray
            let part1 = &line[0..std::cmp::min(line.len(), 33)];
            let part2 = if line.len() > 33 { &line[33..] } else { "" };
            print!("{}", style(part1).bold().color256(39)); // 39 is standard Cyan/Twitter Blue
            println!("{}", style(part2).dim().color256(243)); // 243 is dim gray
        }

        println!(
            "{} {}",
            style("𝕏 Video Downloader").bold().white(),
            style(format!("v{}", VERSION)).dim()
        );
        println!(
            "{}",
            style("A simple CLI tool to download media from Twitter/X").color256(243)
        );

        // Check for updates
        let checker = UpdateChecker::new(VERSION);
        if let Some(latest_version) = checker.check_for_update() {
            println!(
                "\n{} A new version is available: {}",
                style("🔔 Notification:").bold().color256(220), // gold
                style(format!("v{}", latest_version)).bold().color256(39)
            );
            println!(
                "   Run {} to upgrade!",
                style("brew update && brew upgrade reneboygarcia/tap/twitdl")
                    .bold()
                    .color256(39)
            );
        }
        println!();
    }

    fn main_menu(&self) {
        loop {
            let options = vec![
                "Download a video",
                "Show information",
                "How to update / Check for updates",
                "Exit",
            ];

            let choice_res = Select::new("What would you like to do?", options)
                .with_help_message("(Use ↑/↓ arrows and Enter to select, Esc to exit)")
                .prompt();

            match choice_res {
                Ok("Exit") | Err(_) => {
                    println!(
                        "\n{}",
                        style("🐦 Flying off! Happy timeline scrolling! 🚀")
                            .color256(39)
                            .bold()
                    );
                    std::process::exit(0);
                }
                Ok("Download a video") => {
                    self.download_workflow();
                }
                Ok("Show information") => {
                    self.show_info();
                }
                Ok("How to update / Check for updates") => {
                    self.show_update_instructions();
                }
                _ => {}
            }
        }
    }

    fn download_workflow(&self) {
        // Get tweet URL
        let url = match self.get_tweet_url() {
            Some(u) => u,
            None => return,
        };

        // Select video quality
        let qualities = vec![
            "Best (highest resolution / quality)",
            "Medium (balanced quality)",
            "Low (lowest resolution / smaller size)",
            "⟵ Back",
        ];

        let quality_choice = Select::new("Select video quality:", qualities)
            .with_help_message("(Use ↑/↓ arrows and Enter to select, Esc to go back)")
            .prompt();

        let quality = match quality_choice {
            Ok("Best (highest resolution / quality)") => "best",
            Ok("Medium (balanced quality)") => "medium",
            Ok("Low (lowest resolution / smaller size)") => "low",
            _ => return, // Esc or Back
        };

        // Save location
        let path_options = vec![
            "No (save to Downloads)",
            "Yes (specify custom directory/file)",
            "⟵ Back",
        ];

        let path_choice = Select::new(
            "Do you want to specify a custom save location? (Default: Downloads folder)",
            path_options,
        )
        .with_help_message("(Use ↑/↓ and Enter)")
        .prompt();

        let mut output: Option<String> = None;

        match path_choice {
            Ok("No (save to Downloads)") => {}
            Ok("Yes (specify custom directory/file)") => {
                let default_path = self
                    .downloader
                    .get_downloads_dir()
                    .to_string_lossy()
                    .into_owned();
                let output_path_res = Text::new("Enter the output path (type 'back' to return):")
                    .with_default(&default_path)
                    .prompt();

                match output_path_res {
                    Ok(path) => {
                        if path.trim().to_lowercase() == "back" {
                            return;
                        }
                        output = Some(path);
                    }
                    Err(_) => return, // Esc
                }
            }
            _ => return, // Esc or Back
        }

        println!("\n{}", style("𝕏 Video Downloader").bold().white());
        println!(
            "{}: {}\n",
            style("Initiating stream download for").color256(243),
            url
        );

        let start_time = Instant::now();
        match self
            .downloader
            .download_video(&url, output.as_deref(), quality)
        {
            Ok(output_path) => {
                let duration = start_time.elapsed().as_secs_f64();
                println!(
                    "\n{} Video successfully downloaded to: {}",
                    style("✔").bold().color256(39), // Twitter Blue
                    style(&output_path).bold()
                );
                println!("(took {:.2} seconds)", duration);
                // Notify if a new version is available
                let checker = UpdateChecker::new(VERSION);
                if let Some(latest) = checker.check_for_update() {
                    println!(
                        "{} A new version is available: {}! Run {} to upgrade.\n",
                        style("🔔 Notification:").bold().color256(220),
                        style(format!("v{}", latest)).bold().color256(39),
                        style("brew update && brew upgrade reneboygarcia/tap/twitdl")
                            .bold()
                            .color256(39)
                    );
                } else {
                    println!();
                }
            }
            Err(e) => {
                println!("\n{} {}", style("❌").bold().red(), e);
            }
        }
    }

    fn get_tweet_url(&self) -> Option<String> {
        loop {
            let url_res = Text::new("Enter the tweet URL (type 'back' to return):")
                .with_help_message("(Press Esc or type 'back' to go back)")
                .prompt();

            match url_res {
                Ok(url) => {
                    let trimmed = url.trim().to_string();
                    if trimmed.to_lowercase() == "back" {
                        return None;
                    }
                    if trimmed.starts_with("https://twitter.com/")
                        || trimmed.starts_with("https://x.com/")
                    {
                        return Some(trimmed);
                    }
                    println!(
                        "{}",
                        style("⚠️ Invalid URL. Must start with https://twitter.com/ or https://x.com/")
                            .red()
                    );
                }
                Err(_) => return None, // Esc
            }
        }
    }

    fn show_info(&self) {
        println!();
        println!(" {}", style("About 𝕏 Video Downloader").bold().white());
        println!("A minimal, elegant command-line tool to download videos from Twitter/X.");
        println!();
        println!("{}", style("Features:").bold());
        println!("  • Multiple quality settings (Best, Medium, Low)");
        println!("  • Custom output filenames and directory resolving");
        println!("  • Clean and graceful execution interrupt handling");
        println!();
        println!("{}", style("Repository:").bold());
        println!("  https://github.com/reneboygarcia/twitter_video");
        println!();
        let _ = Text::new("Press Enter to return to main menu...").prompt();
        println!();
    }

    fn show_update_instructions(&self) {
        println!();
        println!(
            " {}",
            style("🔄 Checking for updates from GitHub...")
                .bold()
                .white()
        );
        let checker = UpdateChecker::new(VERSION);
        match checker.check_for_update_live() {
            Ok(Some(latest_version)) => {
                println!(
                    "\n{} A new version is available: {}",
                    style("🔔 Notification:").bold().color256(220),
                    style(format!("v{}", latest_version)).bold().color256(39)
                );
                println!(
                    "   Run {} to upgrade!",
                    style("brew update && brew upgrade reneboygarcia/tap/twitdl")
                        .bold()
                        .color256(39)
                );
            }
            Ok(None) => {
                println!(
                    "\n{} You are up to date! (Current version: {})",
                    style("✔").bold().color256(39), // Twitter Blue
                    style(format!("v{}", VERSION)).bold()
                );
            }
            Err(e) => {
                println!(
                    "\n{} Could not reach GitHub to check for updates: {}",
                    style("⚠️").bold().red(),
                    e
                );
                println!(
                    "   You can manually check or upgrade by running:\n   {}",
                    style("brew update && brew upgrade reneboygarcia/tap/twitdl")
                        .bold()
                        .color256(39)
                );
            }
        }
        println!();
        let _ = Text::new("Press Enter to return to main menu...").prompt();
        println!();
    }
}

fn main() {
    let render_config = RenderConfig {
        prompt_prefix: Styled::new("?").with_fg(Color::AnsiValue(39)),
        answered_prompt_prefix: Styled::new("✔").with_fg(Color::AnsiValue(39)),
        highlighted_option_prefix: Styled::new(">").with_fg(Color::AnsiValue(39)),
        selected_option: Some(StyleSheet::new().with_fg(Color::AnsiValue(39))),
        answer: StyleSheet::new().with_fg(Color::AnsiValue(39)),
        help_message: StyleSheet::new().with_fg(Color::AnsiValue(243)),
        default_value: StyleSheet::new().with_fg(Color::AnsiValue(243)),
        placeholder: StyleSheet::new().with_fg(Color::AnsiValue(243)),
        ..RenderConfig::default()
    };
    inquire::set_global_render_config(render_config);

    let args = Args::parse();
    let cli = TwitterDownloaderCLI::new();

    // Set a global Ctrl+C handler for main process clean exit
    let _ = ctrlc::set_handler(|| {
        println!(
            "\n{}",
            style("🐦 Flying off! Happy timeline scrolling! 🚀")
                .color256(39)
                .bold()
        );
        std::process::exit(0);
    });

    if let Some(ref url) = args.url {
        if !args.guide {
            // Direct download mode
            println!(
                "{} {}",
                style("𝕏 Video Downloader").bold().white(),
                style(format!("v{}", VERSION)).dim()
            );

            // Check for update silently/quickly
            let checker = UpdateChecker::new(VERSION);
            if let Some(latest) = checker.check_for_update() {
                println!(
                    "{} A new version is available: {} (run `brew update && brew upgrade reneboygarcia/tap/twitdl` to upgrade)",
                    style("🔔 Notification:").bold().color256(220),
                    style(format!("v{}", latest)).bold().color256(39)
                );
            }

            println!(
                "{}: {}\n",
                style("Direct download requested for").color256(243),
                url
            );

            let quality = args.quality.as_deref().unwrap_or("best");
            let start_time = Instant::now();

            match cli
                .downloader
                .download_video(url, args.output.as_deref(), quality)
            {
                Ok(output_path) => {
                    let duration = start_time.elapsed().as_secs_f64();
                    println!(
                        "\n{} Video successfully downloaded to: {}",
                        style("✔").bold().color256(39), // Twitter Blue
                        style(&output_path).bold()
                    );
                    println!("(took {:.2} seconds)", duration);
                    // Check for updates again on success to notify user
                    let checker = UpdateChecker::new(VERSION);
                    if let Some(latest) = checker.check_for_update() {
                        println!(
                            "{} A new version is available: {}! Run {} to upgrade.\n",
                            style("🔔 Notification:").bold().color256(220),
                            style(format!("v{}", latest)).bold().color256(39),
                            style("brew update && brew upgrade reneboygarcia/tap/twitdl")
                                .bold()
                                .color256(39)
                        );
                    } else {
                        println!();
                    }
                    std::process::exit(0);
                }
                Err(e) => {
                    println!("\n{} {}", style("❌").bold().red(), e);
                    std::process::exit(1);
                }
            }
        }
    }

    // Interactive guided mode (fallback)
    cli.show_welcome();
    cli.main_menu();
}
