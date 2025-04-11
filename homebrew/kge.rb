class Kge < Formula
  include Language::Python::Virtualenv

  desc "Kubernetes utility for viewing pod and failed replicaset events"
  homepage "https://github.com/jessegoodier/kge"
  url "https://github.com/jessegoodier/kge/raw/refs/heads/main/archive/refs/tags/kge-0.4.0.tar.gz"
  sha256 "9895e3e88f681cf04454b112bb4cd5c702b4833abb69f2feec4a3bb01900d383"
  license "MIT"

  depends_on "python@3.9"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/kge", "--version"
  end
end
