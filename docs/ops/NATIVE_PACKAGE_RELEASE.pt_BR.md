# Pacotes nativos na Release do GitHub do produto (air-gap)

**English:** [NATIVE_PACKAGE_RELEASE.md](NATIVE_PACKAGE_RELEASE.md)

**Issue:** [#1408](https://github.com/DataBoar/data-boar/issues/1408) · **Plano:** `docs/plans/PLAN_NATIVE_PACKAGES.md` · **ADR:** [0084](../adr/ADR-0084-native-package-embedded-cpython-by-channel.md), [0089](../adr/ADR-0089-native-package-signed-repository-hosting-keys-and-community-boundary.md)

Este é o caminho **offline / air-gap**: baixe o `.deb` / `.rpm` / `.apk` / `.pkg.tar.zst` do produto **na mesma GitHub Release** dos SBOMs. O **repositório assinado** ([#1405](https://github.com/DataBoar/data-boar/issues/1405)) é o canal do dia a dia e **consome estes mesmos arquivos** — não pode reconstruí-los.

Os wheels da camada 1 vêm do wheelhouse hospedado ([#1182](https://github.com/DataBoar/data-boar/issues/1182)), não de resolução livre da PyPI. O `.deb` da PoC artesanal documentada em #1408 **não** é artefato publicável (não assinado, sem reprodutibilidade, camada 1 não homologada).

Os assets aparecem numa GitHub Release **`v*`** depois que `native-packages.yml` roda em `release: published`. Eles **não** estão em toda tag antiga.

## Convenção de nome (não renomeie)

Cada gerenciador faz parse do nome. Um `.deb` só com hífens e sem arch **quebra** `apt` / `reprepro` / `aptly`.

```text
data-boar_<versão>_amd64.deb                  deb
data-boar-<versão>-<release>.x86_64.rpm       rpm
data-boar-<versão>-r<rel>.apk                 apk
data-boar-<versão>-<rel>-x86_64.pkg.tar.zst   pacman
```

O payload atual do CI é **x86-64 glibc** (smokes debian / Rocky). musl / arm64 ficam para fatias posteriores.

## Verificação offline

```bash
TAG=v1.8.0   # use a tag real da release — não invente
mkdir -p ~/data-boar-native && cd ~/data-boar-native
gh release download "$TAG" --repo DataBoar/data-boar \
  --pattern 'data-boar*' --pattern 'SHA256SUMS*' --pattern 'release-manifest.json'

sha256sum -c SHA256SUMS

# Quando SHA256SUMS.asc existir (chave de empacotamento do #1405):
# gpg --verify SHA256SUMS.asc SHA256SUMS

# Confirme que o release-manifest lista os mesmos hashes:
python3 -c "import json; print(json.load(open('release-manifest.json'))['native_packages'])"
```

Instale um gerenciador (exemplo Debian/Ubuntu):

```bash
sudo apt-get install -y ./data-boar_*_amd64.deb
data-boar --version
```

Checagens após instalar (os mesmos gates do smoke do CI):

```bash
test -f /usr/lib/data-boar/python3.14t/lib/python3.14t/EXTERNALLY-MANAGED
/usr/lib/data-boar/python3.14t/bin/python3.14t -c \
  'import sys, sqlalchemy; assert sys._is_gil_enabled() is False'
```

O wrapper `/usr/bin/data-boar` define `DISABLE_SQLALCHEMY_CEXT=1`. **Não** rode `pip install` dentro de `/usr/lib/data-boar/python3.14t` — o PEP 668 bloqueia isso de propósito.

A camada 1 (numpy / scipy / scikit-learn / pandas / `boar_fast_filter`) é **reinstalada à força a partir do wheelhouse hospedado** (`apply_wheelhouse_v1.sh --no-index`). Esse é o contrato do #1182 — não a resolução livre da PyPI.

## Assinatura do SHA256SUMS

O `SHA256SUMS` sempre vai na Release. O `SHA256SUMS.asc` destacado só é escrito quando o secret `NATIVE_PACKAGE_GPG_PRIVATE_KEY` existe (cerimônia da chave no [#1405](https://github.com/DataBoar/data-boar/issues/1405) / ADR-0089). O pipeline **não** inventa assinatura. Os bytes dos pacotes são os mesmos antes e depois da chave.

## Os mesmos arquivos no repositório assinado

O `#1405` / ADR-0089 indexa **estes** assets da Release. Copie ou baixe; não rode `nfpm package` de novo para o repositório público. Paridade é igualdade de hash (`SHA256SUMS` ↔ `native_packages[]` no `release-manifest.json` ↔ índice apt/dnf/apk/pacman).

## Relacionado

- [packaging/nfpm/README.md](../../packaging/nfpm/README.md) — gerador + build local
- [RELEASE_INTEGRITY.md](../RELEASE_INTEGRITY.md) — SBOM + `files[]` de licenciamento (distinto de `native_packages[]`)
- [INTEGRITY_HUB.pt_BR.md](INTEGRITY_HUB.pt_BR.md)
