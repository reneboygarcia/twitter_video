use clap::{CommandFactory, Parser, Subcommand};
use clap_complete::{generate, Shell};
use console::style;
use inquire::{
    ui::{Color, RenderConfig, StyleSheet, Styled},
    Select, Text,
};
use std::io;
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

    /// Check for updates and upgrade twitdl
    #[arg(short = 'u', long)]
    update: bool,

    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Check for updates and upgrade twitdl
    Update {
        /// Check for updates without performing upgrade
        #[arg(long)]
        check_only: bool,
    },
    /// Generate shell completion scripts (zsh, bash, fish, powershell)
    Completions {
        /// Shell to generate completions for (zsh, bash, fish, powershell)
        shell: String,
    },
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

    fn handle_update(&self, check_only: bool) -> i32 {
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
                    "\n{} A new version is available! Current: {} -> Latest: {}",
                    style("🔔 Notification:").bold().color256(220),
                    style(format!("v{}", VERSION)).dim(),
                    style(format!("v{}", latest_version)).bold().color256(39)
                );

                if check_only {
                    println!(
                        "   Run {} to upgrade!",
                        style("twitdl update").bold().color256(39)
                    );
                    return 2;
                }

                if UpdateChecker::is_installed_via_homebrew() {
                    println!(
                        "{}",
                        style("🚀 Upgrading twitdl via Homebrew...")
                            .color256(39)
                            .bold()
                    );
                    match UpdateChecker::perform_brew_upgrade() {
                        Ok(_) => {
                            println!(
                                "{}",
                                style("✔ Successfully upgraded twitdl!").color256(39).bold()
                            );
                            0
                        }
                        Err(e) => {
                            println!(
                                "{} Upgrading via Homebrew failed: {}",
                                style("❌").bold().red(),
                                e
                            );
                            println!(
                                "   Try running manually: {}",
                                style("brew update && brew upgrade reneboygarcia/tap/twitdl")
                                    .bold()
                                    .color256(39)
                            );
                            1
                        }
                    }
                } else {
                    println!(
                        "   To upgrade, run:\n   {}",
                        style("brew update && brew upgrade reneboygarcia/tap/twitdl")
                            .bold()
                            .color256(39)
                    );
                    2
                }
            }
            Ok(None) => {
                println!(
                    "\n{} You are up to date! (Current version: {})",
                    style("✔").bold().color256(39),
                    style(format!("v{}", VERSION)).bold()
                );
                0
            }
            Err(e) => {
                println!(
                    "\n{} Could not reach GitHub to check for updates: {}",
                    style("⚠️").bold().red(),
                    e
                );
                1
            }
        }
    }

    fn generate_completions(&self, shell_str: &str) -> i32 {
        let shell = match shell_str.to_lowercase().as_str() {
            "bash" => Shell::Bash,
            "zsh" => Shell::Zsh,
            "fish" => Shell::Fish,
            "powershell" | "pwsh" => Shell::PowerShell,
            _ => {
                eprintln!(
                    "{} Unsupported shell '{}'. Supported: bash, zsh, fish, powershell",
                    style("❌").bold().red(),
                    shell_str
                );
                return 1;
            }
        };

        let mut cmd = Args::command();
        generate(shell, &mut cmd, "twitdl", &mut io::stdout());
        0
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
            let part1 = &line[0..std::cmp::min(line.len(), 33)];
            let part2 = if line.len() > 33 { &line[33..] } else { "" };
            print!("{}", style(part1).bold().color256(39));
            println!("{}", style(part2).dim().color256(243));
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

        let checker = UpdateChecker::new(VERSION);
        if let Some(latest_version) = checker.check_for_update() {
            println!(
                "\n{} A new version is available: {}",
                style("🔔 Notification:").bold().color256(220),
                style(format!("v{}", latest_version)).bold().color256(39)
            );
            println!(
                "   Run {} to upgrade!",
                style("twitdl update").bold().color256(39)
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
                    let _ = self.handle_update(false);
                    let _ = Text::new("Press Enter to return to main menu...").prompt();
                    println!();
                }
                _ => {}
            }
        }
    }

    fn download_workflow(&self) {
        let url = match self.get_tweet_url() {
            Some(u) => u,
            None => return,
        };

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
            _ => return,
        };

        let default_path = self
            .downloader
            .get_downloads_dir()
            .to_string_lossy()
            .into_owned();

        let output_path_res = Text::new("Output directory:")
            .with_default(&default_path)
            .prompt();

        let mut output: Option<String> = None;

        match output_path_res {
            Ok(path) => {
                let trimmed = path.trim();
                if trimmed.to_lowercase() == "back" {
                    return;
                }
                if !trimmed.is_empty() {
                    output = Some(trimmed.to_string());
                }
            }
            Err(_) => return,
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
                    style("✔").bold().color256(39),
                    style(&output_path).bold()
                );
                println!("(took {:.2} seconds)", duration);

                let checker = UpdateChecker::new(VERSION);
                if let Some(latest) = checker.check_for_update() {
                    println!(
                        "{} A new version is available: {}! Run {} to upgrade.\n",
                        style("🔔 Notification:").bold().color256(220),
                        style(format!("v{}", latest)).bold().color256(39),
                        style("twitdl update").bold().color256(39)
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
                    if twitdl::downloader::is_twitter_url(&trimmed) {
                        return Some(trimmed);
                    }
                    println!(
                        "{}",
                        style("⚠️ Invalid URL. Must be a valid Twitter/X video URL.").red()
                    );
                }
                Err(_) => return None,
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
        println!("  • Built-in update checker & Homebrew upgrade support (`twitdl update`)");
        println!();
        println!("{}", style("Repository:").bold());
        println!("  https://github.com/reneboygarcia/twitter_video");
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

    let _ = ctrlc::set_handler(|| {
        println!(
            "\n{}",
            style("🐦 Flying off! Happy timeline scrolling! 🚀")
                .color256(39)
                .bold()
        );
        std::process::exit(0);
    });

    // Handle subcommands or update flag
    if args.update {
        let code = cli.handle_update(false);
        std::process::exit(code);
    }

    if let Some(cmd) = args.command {
        match cmd {
            Commands::Update { check_only } => {
                let code = cli.handle_update(check_only);
                std::process::exit(code);
            }
            Commands::Completions { shell } => {
                let code = cli.generate_completions(&shell);
                std::process::exit(code);
            }
        }
    }

    if let Some(ref url) = args.url {
        if url == "update" {
            let code = cli.handle_update(false);
            std::process::exit(code);
        }

        if !args.guide {
            // Direct download mode
            println!(
                "{} {}",
                style("𝕏 Video Downloader").bold().white(),
                style(format!("v{}", VERSION)).dim()
            );

            let checker = UpdateChecker::new(VERSION);
            if let Some(latest) = checker.check_for_update() {
                println!(
                    "{} A new version is available: {} (run `twitdl update` to upgrade)",
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
                        style("✔").bold().color256(39),
                        style(&output_path).bold()
                    );
                    println!("(took {:.2} seconds)", duration);

                    let checker = UpdateChecker::new(VERSION);
                    if let Some(latest) = checker.check_for_update() {
                        println!(
                            "{} A new version is available: {}! Run {} to upgrade.\n",
                            style("🔔 Notification:").bold().color256(220),
                            style(format!("v{}", latest)).bold().color256(39),
                            style("twitdl update").bold().color256(39)
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
