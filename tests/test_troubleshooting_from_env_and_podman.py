"""#494: troubleshooting covers unset *_from_env and Podman hostnames (docs contract)."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"


def test_credentials_troubleshooting_covers_pass_from_env() -> None:
    en = (DOCS / "TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md").read_text(encoding="utf-8")
    pt = (DOCS / "TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md").read_text(
        encoding="utf-8"
    )
    for text in (en, pt):
        assert "## 7." in text
        assert "pass_from_env" in text
        assert "api_key_from_env" in text
        assert "--validate-config" in text
        assert "UserWarning" in text
        assert "OPERATOR_CREDENTIALS_FROM_ENV" in text
        assert "OPERATOR_SECRETS_BITWARDEN" in text
        assert "docs/plans/" not in text


def test_docker_troubleshooting_covers_podman_host_alias() -> None:
    en = (DOCS / "ops" / "TROUBLESHOOTING_DOCKER_DEPLOYMENT.md").read_text(
        encoding="utf-8"
    )
    pt = (DOCS / "ops" / "TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md").read_text(
        encoding="utf-8"
    )
    for text in (en, pt):
        assert "## 6." in text
        assert "host.containers.internal" in text
        assert "host.docker.internal" in text
        assert "distroless" in text
        assert "slirp4netns" in text
        assert "HEALTHCHECK" in text
        assert "127.0.0.1:8088/health" in text
        assert "/usr/local/bin/python3.14" in text
        # Public docs must not paste real lab-op hostnames.
        assert "LAB-NODE-" not in text


def test_troubleshooting_hub_mentions_podman_and_from_env() -> None:
    en = (DOCS / "TROUBLESHOOTING.md").read_text(encoding="utf-8")
    pt = (DOCS / "TROUBLESHOOTING.pt_BR.md").read_text(encoding="utf-8")
    for text in (en, pt):
        assert "Podman" in text
        assert "host.containers.internal" in text
        assert "*_from_env" in text
        assert "unhealthy" in text
        assert "Audit already in progress" in text
        assert "LAB-NODE-" not in text
