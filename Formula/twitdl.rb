class Twitdl < Formula
  env :std
  desc "Interactive CLI tool to download videos from Twitter/X"
  homepage "https://github.com/reneboygarcia/twitter_video"
  url "https://github.com/reneboygarcia/twitter_video/archive/refs/tags/v0.2.6.tar.gz"
  version "0.2.6"
  sha256 "9d2339753c46ae95593c5d7a337523e0df0c74d13576b96f1c57ee57cb62af47"
  head "https://github.com/reneboygarcia/twitter_video.git", branch: "main"

  depends_on "rust" => :build
  depends_on "yt-dlp"

  def install
    system "cargo", "install", *std_cargo_args
  end

  def caveats
    <<~EOS
      Once installed, you can start twitdl from your terminal:

      Interactive mode:
        twitdl

      Direct download mode:
        twitdl <tweet-url>

      For full usage options:
        twitdl --help
    EOS
  end

  test do
    system "#{bin}/twitdl", "--help"
  end
end
