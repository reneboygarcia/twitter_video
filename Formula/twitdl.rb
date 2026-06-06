class Twitdl < Formula
  desc "Interactive CLI tool to download videos from Twitter/X"
  homepage "https://github.com/reneboygarcia/twitter_video"
  version "0.1.1"

  if Hardware::CPU.arm?
    url "https://github.com/reneboygarcia/twitter_video/releases/download/v0.1.1/twitdl-macos-arm64.tar.gz"
    sha256 "6546618500f7fdad20cf7f018214b21dae38eb45be87bc36a3ca5acf20cc4a3b"
  else
    url "https://github.com/reneboygarcia/twitter_video/releases/download/v0.1.1/twitdl-macos-x86_64.tar.gz"
    sha256 "PLACEHOLDER_X86_64_SHA256"
  end

  def install
    bin.install "twitdl"
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
