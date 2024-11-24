#!/usr/bin/env python3

import os
import sys
import click
import questionary
from pathlib import Path
from typing import Optional, Callable, TypeVar
from functools import wraps
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime
from .downloader import TwitterDownloader

console = Console()
T = TypeVar('T')

def handle_back_option(func: Callable[..., Optional[T]]) -> Callable[..., Optional[T]]:
    """Decorator to handle 'back' option in user inputs."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Optional[T]:
        result = func(*args, **kwargs)
        if isinstance(result, str) and result.lower() == 'back':
            return None
        return result
    return wrapper

def handle_errors(func: Callable) -> Callable:
    """Decorator to handle exceptions gracefully."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            console.print(f"❌ Error: {str(e)}", style="red")
            console.print("\n💡 Tips:", style="yellow")
            console.print("• Check your internet connection")
            console.print("• Verify the tweet URL is correct")
            console.print("• Ensure your bearer token is valid")
            console.print("\nRun 'make dev-setup' to set up the environment")
            return None
    return wrapper

class TwitterDownloaderCLI:
    """Interactive CLI for Twitter Video Downloader."""

    def __init__(self):
        self.downloader = None
        self._check_environment()

    def _check_environment(self):
        """Check if the environment is properly set up."""
        if not Path('venv').exists():
            console.print("⚠️  Virtual environment not found!", style="yellow")
            console.print("Please run 'make dev-setup' to set up the environment")
            sys.exit(1)

    def show_welcome(self):
        """Display welcome message."""
        console.print(Panel.fit(
            "Download videos from Twitter/X easily!\n\n"
            "Quick Start:\n"
            "1. Configure your Twitter API token\n"
            "2. Paste a tweet URL\n"
            "3. Choose video quality\n"
            "4. Download!",
            title="🐦 Twitter Video Downloader",
            border_style="blue"
        ))

    def initialize_downloader(self) -> bool:
        """Initialize the downloader with credentials."""
        try:
            self.downloader = TwitterDownloader()
            return True
        except ValueError as e:
            console.print(f"⚠️  {str(e)}", style="yellow")
            return False

    def main_menu(self) -> None:
        """Display and handle main menu."""
        while True:
            choice = questionary.select(
                "What would you like to do?",
                choices=[
                    "Download a video",
                    "Configure settings",
                    "Show information",
                    "Exit"
                ],
                use_indicator=True
            ).ask()

            if choice == "Exit":
                console.print("👋 Goodbye!", style="yellow")
                sys.exit(0)

            actions = {
                "Download a video": self.download_workflow,
                "Configure settings": self.config_workflow,
                "Show information": self.show_info
            }

            if action := actions.get(choice):
                action()

    @handle_errors
    def download_workflow(self) -> None:
        """Handle the video download workflow."""
        if not self.initialize_downloader():
            if questionary.confirm("Would you like to configure your settings now?").ask():
                self.config_workflow()
            return

        # Get tweet URL
        url = self._get_tweet_url()
        if not url:
            return

        # Get video quality
        quality = questionary.select(
            "Select video quality:",
            choices=["best", "medium", "low"],
            default="best"
        ).ask()

        # Get output path
        output = self._get_output_path()
        if output is None:
            return

        # Download the video
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Downloading video...", total=None)
            output_path = self.downloader.download_video(url, output, quality)
            progress.update(task, completed=True)

        console.print(f"\n✅ Video downloaded successfully to: {output_path}", style="green")
        
        self._show_next_steps()

    @handle_back_option
    def _get_tweet_url(self) -> Optional[str]:
        """Get and validate tweet URL."""
        while True:
            url = questionary.text(
                "Enter the tweet URL (or 'back' to return):",
                validate=lambda x: x.startswith(('https://twitter.com/', 'https://x.com/')) or x.lower() == 'back'
            ).ask()
            
            if url.lower() == 'back':
                return None
            return url

    @handle_back_option
    def _get_output_path(self) -> Optional[str]:
        """Get output path for the video."""
        save_type = questionary.select(
            "How would you like to save the video?",
            choices=[
                "Use default filename",
                "Specify custom filename",
                "Back"
            ]
        ).ask()

        if save_type == "Back":
            return None
        elif save_type == "Use default filename":
            return None  # Downloader will use default filename
        else:
            return questionary.path("Enter the output filename:").ask()

    def config_workflow(self) -> None:
        """Handle configuration workflow."""
        while True:
            choice = questionary.select(
                "Configuration options:",
                choices=[
                    "Set up bearer token",
                    "Show current configuration",
                    "Back to main menu"
                ]
            ).ask()

            if choice == "Back to main menu":
                break
            elif choice == "Set up bearer token":
                self._setup_bearer_token()
            else:
                self._show_current_config()

    def _setup_bearer_token(self) -> None:
        """Set up bearer token configuration."""
        console.print("\n📝 Twitter API Configuration", style="blue bold")
        console.print("You can get your bearer token from https://developer.twitter.com")

        if Path('.env').exists():
            if not questionary.confirm("Configuration file exists. Overwrite?").ask():
                return

        token = questionary.password("Enter your Twitter Bearer Token:").ask()
        
        with open('.env', 'w') as f:
            f.write(f"BEARER_TOKEN={token}")
        
        console.print("✅ Configuration saved successfully!", style="green")

    def _show_current_config(self) -> None:
        """Display current configuration."""
        token = os.getenv('BEARER_TOKEN')
        if token:
            masked_token = f"{token[:8]}...{token[-4:]}"
            console.print(Panel.fit(
                f"Bearer Token: {masked_token}",
                title="📌 Current Configuration",
                border_style="blue"
            ))
        else:
            console.print("⚠️  No configuration found!", style="yellow")

    def _show_next_steps(self) -> None:
        """Show available next steps."""
        console.print("\n📌 What's next?", style="blue bold")
        console.print("• Download another video")
        console.print("• Change settings")
        console.print("• Exit the program")

    def show_info(self) -> None:
        """Display information about the tool."""
        console.print(Panel.fit(
            "A command-line tool to download videos from Twitter/X\n\n"
            "Features:\n"
            "• Download videos in different qualities\n"
            "• Custom output filenames\n"
            "• Easy configuration management\n\n"
            "For more information, visit: https://github.com/yourusername/twitter-video-dl",
            title="ℹ️ About Twitter Video Downloader",
            border_style="blue"
        ))

def main():
    """Entry point for the CLI application."""
    try:
        cli = TwitterDownloaderCLI()
        cli.show_welcome()
        cli.main_menu()
    except KeyboardInterrupt:
        console.print("\n👋 Operation cancelled by user", style="yellow")
        sys.exit(0)

if __name__ == "__main__":
    main() 