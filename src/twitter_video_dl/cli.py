import sys
from functools import wraps
from typing import Callable, Optional, TypeVar

import click
import questionary
from rich.console import Console
from rich.panel import Panel

from .downloader import TwitterDownloader

console = Console()
T = TypeVar("T")


def handle_back_option(func: Callable[..., Optional[T]]) -> Callable[..., Optional[T]]:
    """Decorator to handle 'back' option in user inputs."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Optional[T]:
        result = func(*args, **kwargs)
        if isinstance(result, str) and result.lower() == "back":
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
            console.print("• Verify the tweet URL is correct and public")
            return None

    return wrapper


class TwitterDownloaderCLI:
    """Interactive CLI for Twitter Video Downloader."""

    def __init__(self):
        self.downloader = None
        # Configure questionary to use keyboard shortcuts
        questionary.Style(
            [
                ("qmark", "fg:#673ab7 bold"),  # Colors for the selection indicator
                ("question", "bold"),  # Question text
                ("answer", "fg:#ff9d00 bold"),  # Selected answer
                ("pointer", "fg:#673ab7 bold"),  # Pointer arrow
                ("highlighted", "fg:#673ab7 bold"),  # Highlighted choice
                ("selected", "fg:#cc5454"),  # Selected choice
            ]
        )

    def show_welcome(self):
        """Display welcome message."""
        console.print(
            Panel.fit(
                "Download videos from Twitter/X easily!\n\n"
                "Quick Start:\n"
                "1. Paste a tweet URL\n"
                "2. Choose video quality\n"
                "3. Download!\n\n"
                "Navigation:\n"
                "• Use ↑/↓ arrows to move\n"
                "• Press Enter to select\n"
                "• Press Esc or type 'back' to go back",
                title="🐦 Twitter Video Downloader",
                border_style="blue",
            )
        )

    def initialize_downloader(self) -> None:
        """Initialize the downloader."""
        if not self.downloader:
            self.downloader = TwitterDownloader()

    def main_menu(self) -> None:
        """Display and handle main menu."""
        while True:
            choice = questionary.select(
                "What would you like to do?",
                choices=[
                    "Download a video",
                    "Show information",
                    "Exit",
                ],
                use_indicator=True,
                instruction="(Use ↑/↓ arrows and Enter to select, Esc to exit)",
                qmark="🔹",
            ).ask()

            if choice is None or choice == "Exit":  # User pressed Esc or chose Exit
                console.print("👋 Goodbye!", style="yellow")
                sys.exit(0)

            actions = {
                "Download a video": self.download_workflow,
                "Show information": self.show_info,
            }

            if action := actions.get(choice):
                action()

    @handle_errors
    def download_workflow(self) -> None:
        """Handle the video download workflow."""
        self.initialize_downloader()

        # Get tweet URL
        url = self._get_tweet_url()
        if url is None:  # User pressed Esc or chose back
            return

        # Get video quality
        quality = questionary.select(
            "Select video quality:",
            choices=["best", "medium", "low", "⟵ Back"],
            default="best",
            instruction="(Use ↑/↓ arrows and Enter to select, Esc to go back)",
            qmark="🔹",
        ).ask()

        if quality is None or quality == "⟵ Back":  # User pressed Esc or Back
            return

        # Ask for custom path or use default Downloads directory
        prompt_text = (
            "Do you want to specify a custom save location? "
            "(Default: Downloads folder)"
        )
        use_custom_path_choice = questionary.select(
            prompt_text,
            choices=["Yes", "No", "⟵ Back"],
            instruction="(Use ↑/↓ and Enter)",
            qmark="🔹",
        ).ask()

        if (
            use_custom_path_choice is None or use_custom_path_choice == "⟵ Back"
        ):  # User pressed Esc or Back
            return

        output = None
        if use_custom_path_choice == "Yes":
            output = questionary.path(
                "Enter the output path (type 'back' to return):",
                default=str(self.downloader._get_downloads_dir()),
                qmark="🔹",
            ).ask()

            if output is None:  # User pressed Esc
                return
            if isinstance(output, str) and output.lower() == "back":
                return

        try:
            print(f"\nDownloading video from: {url}")
            output_path = self.downloader.download_video(url, output, quality)
            console.print(
                f"\n✅ Video downloaded successfully to: {output_path}", style="green"
            )
        except Exception as e:
            console.print(f"\n❌ Download failed: {str(e)}", style="red")
            return

        self._show_next_steps()

    @handle_back_option
    def _get_tweet_url(self) -> Optional[str]:
        """Get and validate tweet URL."""
        while True:
            url = questionary.text(
                "Enter the tweet URL (type 'back' to return):",
                validate=lambda x: x.startswith(
                    ("https://twitter.com/", "https://x.com/")
                ),
                instruction="(Press Esc or type 'back' to go back)",
                qmark="🔹",
            ).ask()

            if url is None:  # User pressed Esc
                return None
            return url

    def _show_next_steps(self) -> None:
        """Show available next steps."""
        console.print("\n📌 What's next?", style="blue bold")
        console.print("• Download another video")
        console.print("• Change settings")
        console.print("• Exit the program")
        console.print("\nUse ↑/↓ arrows to navigate and Enter to select")

    def show_info(self) -> None:
        """Display information about the tool."""
        console.print(
            Panel.fit(
                "A command-line tool to download videos from Twitter/X\n\n"
                "Features:\n"
                "• Download videos in different qualities\n"
                "• Custom output filenames\n"
                "• Easy configuration management\n\n"
                "Navigation:\n"
                "• Use ↑/↓ arrows to move\n"
                "• Press Enter to select\n"
                "• Press Esc or type 'back' to go back\n\n"
                "For more information, visit: "
                "https://github.com/reneboygarcia/twitter_video",
                title="ℹ️ About Twitter Video Downloader",
                border_style="blue",
            )
        )


@click.command()
@click.argument("url", required=False)
@click.option(
    "--quality",
    "-q",
    type=click.Choice(["best", "medium", "low"]),
    help="Video quality settings (default: best)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(writable=True),
    help="Output directory or filename path",
)
def main(
    url: Optional[str] = None,
    quality: Optional[str] = None,
    output: Optional[str] = None,
):
    """An interactive and command-line tool to download videos from Twitter/X."""
    try:
        cli = TwitterDownloaderCLI()

        # If url is specified, perform direct download (non-interactive)
        if url:
            cli.initialize_downloader()
            q = quality or "best"
            try:
                print(f"Downloading video from: {url}")
                output_path = cli.downloader.download_video(url, output, q)
                console.print(
                    f"\n✅ Video downloaded successfully to: {output_path}",
                    style="green",
                )
            except Exception as e:
                console.print(f"\n❌ Download failed: {str(e)}", style="red")
                sys.exit(1)
        else:
            # Fall back to interactive mode
            cli.show_welcome()
            cli.main_menu()
    except KeyboardInterrupt:
        console.print("\n👋 Operation cancelled by user", style="yellow")
        sys.exit(0)


if __name__ == "__main__":
    main()
