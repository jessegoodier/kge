class Kge_kubectl_get_events < Formula
  include Language::Python::Virtualenv

  desc "Kubernetes utility for viewing pod and failed replicaset events"
  homepage "https://pypi.org/project/kge-kubectl-get-events/"
  url "https://files.pythonhosted.org/packages/b9/26/ab3ab6203ea173391a686a301ba9184af5559732dab0ff29c535311f2d93/kge_kubectl_get_events-0.7.0.tar.gz"
  sha256 "4b8d47cb0e1d55eadc06c6f307b8774f4ea25dcff794569527ba42b644a24b85"
  license "MIT"

  depends_on "python@3"

  # Add dependencies
  resource "colorama" do
    url "https://pypi.org/simple/#colorama/"
  end

  resource "kubernetes" do
    url "https://pypi.org/simple/#kubernetes/"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system bin/"kge-kubectl-get-events", "--version"
  end
end
