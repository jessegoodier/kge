class KgeSimple < Formula
  include Language::Python::Virtualenv

  desc "Kubernetes utility for viewing pod and failed replicaset events"
  homepage "https://github.com/jessegoodier/kge"
  url "https://files.pythonhosted.org/packages/10/77/7c4caf3fe915b3a8669923f11ba32de8f9b5c2422819708c3ecda9b7ab18/kge_kubectl_get_events-0.8.9.tar.gz"
  sha256 "22d055eea0b505fde52f3a11c3dec4c2d95bc6380255ab76006043f2b9575e87"
  license "MIT"

  depends_on "python@3.13"
  depends_on "poetry" => :build

  def install
    venv = virtualenv_create(libexec, "python3.13")
    system "poetry", "build", "--format", "wheel"
    system "poetry", "install", "--no-interaction", "--no-cache", "--verbose"
    venv.pip_install Dir["dist/*.whl"].first
    bin.install_symlink libexec/"bin/kge"
  end

  test do
    system bin/"kge", "--version"
  end
end
