import sys
import time
from functools import wraps
from typing import Callable, Optional, TypeVar

import click
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from . import __version__
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
            error_message = (
                f"[bold #f4212e]Error:[/bold #f4212e] {str(e)}\n\n"
                "[bold #f5b800]Tips:[/bold #f5b800]\n"
                "• Check your internet connection\n"
                "• Verify the tweet URL is correct, public, and contains a video"
            )
            console.print(
                Panel(
                    error_message,
                    title="⚠️ Something Went Wrong",
                    title_align="left",
                    border_style="#f4212e",
                    expand=False,
                )
            )
            return None

    return wrapper


class TwitterDownloaderCLI:
    """Interactive CLI for Twitter Video Downloader."""

    def __init__(self):
        self.downloader: Optional[TwitterDownloader] = None
        # Configure questionary to use brand-aligned Twitter/X colors
        self.style = questionary.Style(
            [
                ("qmark", "fg:#ffffff bold"),  # X White question marks
                ("question", "bold"),  # Standard bold question
                ("answer", "fg:#ffffff bold"),  # X White answer
                ("pointer", "fg:#ffffff bold"),  # X White pointer
                ("highlighted", "fg:#ffffff bold"),  # X White highlighted choice
                ("selected", "fg:#ffffff"),  # X White selected choice
                ("instruction", "fg:#6e767d italic"),  # Muted Twitter Gray tips
            ]
        )

    def show_welcome(self):
        """Display welcome message."""
        # ASCII art rendered as plain string (trailing spaces are part of the art)
        ascii_art = (
            " ______  __     __   __   ______  _____    __\n"
            "/\\__  _\\/\\ \\  _ \\ \\ /\\ \\ /\\__  _\\/\\  __-. /\\ \\\n"
            '\\/_/\\ \\/\\ \\ \\/ ".\\ \\\\ \\ \\\\/_/\\ \\/\\ \\ \\/\\ \\\\ \\ \\____\n'  # noqa: E501
            '   \\ \\_\\ \\ \\__/".~\\_\\\\ \\_\\  \\ \\_\\ \\ \\____- \\ \\_____\\\n'
            "    \\/_/  \\/_/   \\/_/ \\/_/   \\/_/  \\/____/  \\/_____/"
        )
        console.print()
        for line in ascii_art.split("\n"):
            t = Text(line)
            t.stylize("bold #1da1f2", 0, 33)
            t.stylize("dim #6e767d", 33, len(line))
            console.print(t)
        console.print(
            f"[bold #ffffff]𝕏 Video Downloader[/bold #ffffff] [dim]v{__version__}[/dim]"
        )
        console.print(
            "[#6e767d]A simple CLI tool to download media from Twitter/X[/#6e767d]"
        )
        console.print("[dim]💡 To update: brew update && brew upgrade reneboygarcia/tap/twitdl[/dim]")
        console.print()

    def initialize_downloader(self) -> None:
        """Initialize the downloader."""
        if not self.downloader:
            self.downloader = TwitterDownloader()

    def main_menu(self) -> None:
        """Display and handle main menu."""
        while True:
            try:
                choice = questionary.select(
                    "What would you like to do?",
                    choices=[
                        questionary.Choice(
                            "Download a video", value="Download a video"
                        ),
                        questionary.Choice(
                            "Show information", value="Show information"
                        ),
                        questionary.Choice(
                            "How to update / Check for updates", value="How to update"
                        ),
                        questionary.Choice("Exit", value="Exit"),
                    ],
                    style=self.style,
                    instruction="(Use ↑/↓ arrows and Enter to select, Esc to exit)",
                    qmark="?",
                ).ask()

                if choice is None or choice == "Exit":  # Esc or Exit
                    console.print("👋 Goodbye!", style="yellow")
                    sys.exit(0)

                actions = {
                    "Download a video": self.download_workflow,
                    "Show information": self.show_info,
                    "How to update": self.show_update_instructions,
                }

                if action := actions.get(choice):
                    action()
            except KeyboardInterrupt:
                console.print("\n👋 Goodbye!", style="yellow")
                sys.exit(0)

    @handle_errors
    def download_workflow(self) -> None:
        """Handle the video download workflow."""
        try:
            self.initialize_downloader()
            assert self.downloader is not None

            # Get tweet URL
            url = self._get_tweet_url()
            if url is None:  # User pressed Esc or chose back
                return

            # Get video quality
            quality = questionary.select(
                "Select video quality:",
                choices=[
                    questionary.Choice(
                        "Best (highest resolution / quality)", value="best"
                    ),
                    questionary.Choice("Medium (balanced quality)", value="medium"),
                    questionary.Choice(
                        "Low (lowest resolution / smaller size)", value="low"
                    ),
                    questionary.Choice("⟵ Back", value="⟵ Back"),
                ],
                default="best",
                style=self.style,
                instruction="(Use ↑/↓ arrows and Enter to select, Esc to go back)",
                qmark="?",
            ).ask()

            if quality is None or quality == "⟵ Back":  # Esc or Back
                return

            # Ask for custom path or use default Downloads directory
            use_custom_path_choice = questionary.select(
                "Do you want to specify a custom save location?"
                " (Default: Downloads folder)",
                choices=[
                    questionary.Choice("No (save to Downloads)", value="No"),
                    questionary.Choice(
                        "Yes (specify custom directory/file)", value="Yes"
                    ),
                    questionary.Choice("⟵ Back", value="⟵ Back"),
                ],
                style=self.style,
                instruction="(Use ↑/↓ and Enter)",
                qmark="?",
            ).ask()

            if (
                use_custom_path_choice is None or use_custom_path_choice == "⟵ Back"
            ):  # Esc or Back
                return

            output = None
            if use_custom_path_choice == "Yes":
                output = questionary.path(
                    "Enter the output path (type 'back' to return):",
                    default=str(self.downloader._get_downloads_dir()),
                    style=self.style,
                    qmark="?",
                ).ask()

                if output is None:  # User pressed Esc
                    return
                if isinstance(output, str) and output.lower() == "back":
                    return

            try:
                console.print("\n[bold #ffffff]𝕏 Video Downloader[/bold #ffffff]")
                console.print(
                    f"[#6e767d]Initiating stream download for:[/#6e767d] {url}\n"
                )
                start_time = time.time()
                output_path = self.downloader.download_video(url, output, quality)
                duration = time.time() - start_time
                console.print(
                    f"\n[bold #00ba7c]✔[/bold #00ba7c] Video successfully"
                    f" downloaded to: [bold]{output_path}[/bold]"
                    f" (took {duration:.2f} seconds)"
                )
                console.print(
                    "[dim]💡 Keep twitdl up-to-date: brew update && brew upgrade reneboygarcia/tap/twitdl[/dim]\n"
                )
            except Exception as e:
                console.print(f"\n[bold #f4212e]❌[/bold #f4212e] {str(e)}")
                return
        except KeyboardInterrupt:
            console.print("\n[bold #f5b800]⚠️[/bold #f5b800] Download cancelled")
            return

    @handle_back_option
    def _get_tweet_url(self) -> Optional[str]:
        """Get and validate tweet URL."""
        while True:
            url = questionary.text(
                "Enter the tweet URL (type 'back' to return):",
                validate=lambda x: x.lower() == "back"
                or x.startswith(("https://twitter.com/", "https://x.com/")),
                style=self.style,
                instruction="(Press Esc or type 'back' to go back)",
                qmark="?",
            ).ask()

            if url is None:  # User pressed Esc
                return None
            return url

    def show_info(self) -> None:
        """Display information about the tool."""
        console.print()
        console.print("[bold #ffffff] About 𝕏 Video Downloader[/bold #ffffff]")
        console.print(
            "A minimal, elegant command-line tool to download videos" " from Twitter/X."
        )
        console.print()
        console.print("[bold]Features:[/bold]")
        console.print("  • Multiple quality settings (Best, Medium, Low)")
        console.print("  • Custom output filenames and directory resolving")
        console.print("  • Clean and graceful execution interrupt handling")
        console.print()
        console.print("[bold]Repository:[/bold]")
        console.print("  https://github.com/reneboygarcia/twitter_video")
        console.print()
        questionary.press_any_key_to_continue(
            "Press any key to return to main menu..."
        ).ask()
        console.print()

    def show_update_instructions(self) -> None:
        """Display instructions on how to update the CLI."""
        console.print()
        console.print(
            "[bold #ffffff]🔄 How to Update 𝕏 Video Downloader[/bold #ffffff]"
        )
        console.print(f"Current version: [bold #1da1f2]v{__version__}[/bold #1da1f2]")
        console.print(
            "To check for and install updates, run the following command:"
        )
        console.print()
        console.print(
            "  [bold #1da1f2]brew update && brew upgrade reneboygarcia/tap/twitdl[/bold #1da1f2]"
        )
        console.print()
        questionary.press_any_key_to_continue(
            "Press any key to return to main menu..."
        ).ask()
        console.print()


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
@click.option(
    "--guide",
    "-g",
    is_flag=True,
    help="Force interactive guided mode",
)
def main(
    url: Optional[str] = None,
    quality: Optional[str] = None,
    output: Optional[str] = None,
    guide: bool = False,
):
    """An interactive and command-line tool to download videos from Twitter/X."""
    try:
        cli = TwitterDownloaderCLI()

        # If url is specified and guide is not requested, perform direct download
        if url and not guide:
            cli.initialize_downloader()
            assert cli.downloader is not None
            q = quality or "best"
            try:
                console.print(
                    "[bold #ffffff]𝕏 Video Downloader[/bold #ffffff]"
                    f" [dim]v{__version__}[/dim]"
                )
                console.print(
                    f"[#6e767d]Direct download requested for:[/#6e767d] {url}\n"
                )
                start_time = time.time()
                output_path = cli.downloader.download_video(url, output, q)
                duration = time.time() - start_time
                console.print(
                    f"\n[bold #00ba7c]✔[/bold #00ba7c] Video successfully"
                    f" downloaded to: [bold]{output_path}[/bold]"
                    f" (took {duration:.2f} seconds)"
                )
                console.print(
                    "[dim]💡 Keep twitdl up-to-date: brew update && brew upgrade reneboygarcia/tap/twitdl[/dim]\n"
                )
            except Exception as e:
                console.print(f"\n[bold #f4212e]❌[/bold #f4212e] {str(e)}")
                sys.exit(1)
        else:
            # Fall back to interactive mode
            cli.show_welcome()
            cli.main_menu()
    except KeyboardInterrupt:
        console.print("\n[bold #f5b800]👋[/bold #f5b800] Operation cancelled by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
