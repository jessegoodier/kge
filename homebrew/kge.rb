class kge < Formula
  include Language::Python::Virtualenv

  desc "Kubernetes utility for viewing pod and failed replicaset events"
  homepage "https://github.com/jessegoodier/kge"
  url "https://github.com/jessegoodier/kge/raw/refs/heads/main/archive/refs/tags/kge-0.4.1.tar.gz"
  sha256 "0dc2f9c16b5aed58f2a5bdaed7edef337d17e051b8d25c34f0a61bbc3adfc495"
  license "MIT"

  depends_on "python@3.9" => :recommended

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/kge", "--version"
  end
end
