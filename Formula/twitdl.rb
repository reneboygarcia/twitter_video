class Twitdl < Formula
  env :std
  desc "Interactive CLI tool to download videos from Twitter/X"
  homepage "https://github.com/reneboygarcia/twitter_video"
  url "https://github.com/reneboygarcia/twitter_video/archive/refs/tags/v0.2.4.tar.gz"
  version "0.2.4"
  sha256 "f28e4d43467988dfd9bcf3137cf97cf1d4b179c6fd7b9d492f1e326f27108ac7"
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
