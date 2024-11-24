from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="twitter_video_dl",
    version="0.1.0",
    description="An interactive CLI tool to download videos from Twitter/X",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "yt-dlp==2024.11.4",
        "tqdm==4.66.4",
        "questionary>=1.10.0",
        "rich>=13.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "twitdl=downloader.cli:main",
        ],
    },
)