class Twitdl < Formula
  env :std
  desc "Interactive CLI tool to download videos from Twitter/X"
  homepage "https://github.com/reneboygarcia/twitter_video"
  url "https://github.com/reneboygarcia/twitter_video/archive/refs/tags/v0.2.2.tar.gz"
  version "0.2.2"
  sha256 "b91f6a5e1439c0b361b6f7688a0708a5e355e4ed934953cf0475717a3d6b2f98"
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
