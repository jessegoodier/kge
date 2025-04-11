class Kge < Formula
  include Language::Python::Virtualenv

  desc "kubernetes utility for viewing pod and failed replicaset events"
  homepage "https://github.com/jessegoodier/kge"
  url "https://github.com/jessegoodier/kge/raw/refs/heads/main/archive/refs/tags/kge-0.4.0.tar.gz"
  sha256 "3b9a5179c64edb5456d8d6d2252675df07f042710324bd24846f829dc43e9c94"
  license "MIT"

  depends_on "python@3.9"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/kge", "--version"
  end
end 