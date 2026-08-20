# Homebrew formula for Data Boar (#1425).
# Own tap (DataBoar/homebrew-databoar) — not homebrew-core.
# Host interpreter: Homebrew python@3.13 + pip into a venv.
# Does NOT embed CPython (unlike Linux nfpm / Void xbps channel-a packages).
#
# Bump url + sha256 after each PyPI publish:
#   uv run python scripts/homebrew_formula_bump.py --write
class DataBoar < Formula
  include Language::Python::Virtualenv

  desc "Discover personal and sensitive data across files, databases, and APIs"
  homepage "https://github.com/DataBoar/data-boar"
  url "https://files.pythonhosted.org/packages/ad/ad/ea0ff6e770702ffe24bc374209e73dd9812d42bb7cc13e6c3eab29c776ec/data_boar-1.7.4.post12.tar.gz"
  sha256 "3e67e81d2e1d381780dc21240e6dfbb596fe8b3a32700e7aa2386daabdc17ec0"
  license "BSD-3-Clause"

  livecheck do
    url "https://pypi.org/pypi/data-boar/json"
    strategy :json do |json|
      json["info"]["version"]
    end
  end

  depends_on "python@3.13"

  def install
    virtualenv_create(libexec, "python3.13")
    python = libexec/"bin/python"
    # std_pip_args is --no-deps --no-build-isolation --no-binary=:all: (resource
    # model). This tap lets pip fetch hatchling for the sdist plus runtime wheels.
    system "python3.13", "-m", "pip", "--python", python, "install", "--verbose", "."
    bin.install_symlink libexec/"bin/data-boar"
  end

  def caveats
    <<~EOS
      Base install only (PyPI extras are not bundled). Connector extras, for example:

        #{opt_libexec}/bin/pip install "data-boar[sql-community]"

      This tap uses Homebrew's Python, not an embedded interpreter.
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/data-boar --version")

    log = testpath/"demo.log"
    pid = spawn(bin/"data-boar", "--demo", [:out, :err] => log.to_s)
    begin
      tmp = ENV.fetch("TMPDIR", Dir.tmpdir)
      demo_db = File.join(tmp, "data_boar_demo", "audit_results.db")
      90.times do
        break if File.exist?(demo_db)

        sleep 2
      end
      assert_path_exists demo_db, "demo workspace DB missing; see #{log}"
    ensure
      begin
        Process.kill("TERM", pid)
        Process.wait(pid)
      rescue Errno::ESRCH, Errno::ECHILD
        nil
      end
    end
  end
end
