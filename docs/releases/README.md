# Release notes and how to publish a GitHub release

Each release has a markdown file here (e.g. `1.3.1.md`, `1.5.4.md`) with the release notes. A short rolling summary lives at the repo root in **[CHANGELOG.md](../../CHANGELOG.md)**.

## Get ready for a PR (version bump + release note)

When preparing a release (e.g. 1.5.4):

1. Bump version everywhere per [VERSIONING.md](../VERSIONING.md): `pyproject.toml`, `core/about.py`, man pages, DEPLOY, TECH_GUIDE, README (EN + pt-BR), docs/README (EN + pt-BR).
1. Add a new file here (e.g. `1.5.4.md`) with highlights, changes, Docker build/push commands, and **After merging the release PR** (tag, push image, `gh release create`).
1. Run the full test suite: `uv run pytest -v -W error`.
1. Open a PR with your branch; after merge, follow the “After merging” steps in the release note to tag, push the Docker image, and create the GitHub release.

## After you push the code to GitHub

To publish **v1.3.1** (or the version you just bumped) as a GitHub release with the same version number and the prepared notes:

1. **Create and push the tag** (if not already pushed with the commit):

   ```bash
   git tag v1.3.1
   git push origin v1.3.1
   ```

1. **Create the release** using GitHub CLI:

   ```bash
   gh release create v1.3.1 --notes-file docs/releases/1.3.1.md --title "1.3.1"
   ```

   **Pre-releases (`-beta`, `-rc`):** add `--prerelease` and **do not** expect **`latest`** Docker Hub tags to move unless you explicitly publish candidate images. Example: `gh release create v1.7.4-rc --prerelease --notes-file docs/releases/1.7.4-rc.md`.

   Or in the GitHub web UI: **Releases** → **Draft a new release** → choose tag `v1.3.1`, set title to `1.3.1`, and paste the contents of `docs/releases/1.3.1.md` into the description. For RCs, tick **Set as a pre-release** and leave **Set as the latest release** **off** unless you truly want the RC to become the repo’s **Latest** pointer.

The release will then be visible on the repository’s Releases page and the Docker image with the same version tag is already on Docker Hub.
