class Kge < Formula
  include Language::Python::Virtualenv

  desc "Kubernetes utility for viewing pod and failed replicaset events"
  homepage "https://github.com/jessegoodier/kge-kubectl-get-events"
  url "https://github.com/jessegoodier/kge-kubectl-get-events/archive/refs/tags/v0.5.1.tar.gz"
  sha256 "" # You'll need to add the SHA256 of your release tarball
  license "MIT"

  depends_on "python@3.11"

  resource "kubernetes" do
    url "https://files.pythonhosted.org/packages/3b/05/cc2b4d8b7bc5479d93a858849dbd5a3c4c784a356e1f1f16965c1c4f4c6/kubernetes-28.1.0.tar.gz"
    sha256 "5854b0c508e8d217ca205591384ab58389abdae608576f9b8e4b0c133a264e3a"
  end

  resource "colorama" do
    url "https://files.pythonhosted.org/packages/d8/53/6f443c9a4a8358a93a6792e2acffb9d9d5cb0a5cfd8802644b7b1c9a02e4/colorama-0.4.6.tar.gz"
    sha256 "08695f5cb7ed6e0531a20572697297273c47b8cae5a63ffc6d6ed5c201be6e44"
  end

  resource "six" do
    url "https://files.pythonhosted.org/packages/71/39/171f1c67cd00715f190ba0b100d606d440a28c93c7714febeca8b79af85e/six-1.16.0.tar.gz"
    sha256 "1e61c37477a1626458e36f7b1d82aa5c9b094fa4802892072e49de9c60c4c926"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/kge", "--help"
  end
end 