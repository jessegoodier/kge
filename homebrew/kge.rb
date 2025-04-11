class Kge < Formula
  include Language::Python::Virtualenv

  desc "A tool to get Kubernetes events"
  homepage "https://github.com/jessegoodier/kge-kubectl-get-events"
  url "https://github.com/jessegoodier/kge-kubectl-get-events/archive/refs/tags/v0.4.0.tar.gz"
  sha256 ""  # You'll need to update this after creating the release
  license "MIT"

  depends_on "python@3.9"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/kge", "--version"
  end
end 