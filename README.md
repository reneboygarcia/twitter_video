# Twitter Video Downloader

This tool helps you download videos from Twitter/X using `yt-dlp`. It's designed to be easy to use, especially in Google Colab!

## 🚀 Quick Start (Google Colab)

1. Open this notebook in Google Colab: [Open in Colab](https://colab.research.google.com/github/reneboygarcia/twitter_video/blob/main/twitter_video_downloader.ipynb)
   
2. Install required packages:
   - Click on the first code cell and run: `!pip install yt-dlp requests`

3. Download the video:
   - Run all cells in the notebook
   - The video will be downloaded to the `output_video` folder

## 📝 How to Use

1. **Basic Download (Default)**
   - The video will be downloaded in the best available format
   - Just run the code as is!

2. **Custom Download Options**
   - Modify the `ydl_opts` dictionary in the `download_twitter_video` function to customize download options
   - Example: Change the output template or format

## 🛠️ Setting Up a Virtual Environment

To ensure a clean and isolated environment, it's recommended to use a virtual environment. Here's a quick guide:

1. **Create a Virtual Environment:**
   - Run `python -m venv venv` to create a virtual environment named `venv`.

2. **Activate the Virtual Environment:**
   - On Windows, run `venv\Scripts\activate`.
   - On macOS and Linux, run `source venv/bin/activate`.

3. **Install Required Packages:**
   - Once activated, install the necessary packages using `pip install -r requirements.txt`.

## ⚠️ Important Notes

- Make sure the URL of the Twitter/X video is correct
- The downloaded video will be saved in the `output_video` folder
- Download your video from the files panel before closing Colab

## 🆘 Need Help?

If you run into any issues, check that:
1. The Twitter/X video URL is correct
2. You've installed the `yt-dlp` and `requests` packages
