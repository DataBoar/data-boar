# Pacotes nativos xbps no Void (#1404)

**English:** [VOID_XBPS_PACKAGING.md](VOID_XBPS_PACKAGING.md)

O nfpm **não** gera xbps. O canal nativo Enterprise (ADR-0084) entrega um overlay de `void-packages` em [`packaging/void/`](../../packaging/void/README.md). A validação é **Podman Void** (imagens glibc e musl) — não metal de lab.

Submissão a montante no `void-packages` fica **fora de escopo** aqui.

## Instalação por distro (Void)

Depois de `./xbps-src pkg data-boar` num clone de void-packages com este overlay:

```bash
sudo xbps-install --repository=hostdir/binpkgs data-boar
sudo ln -s /etc/sv/data-boar /var/service/data-boar
```

O serviço é **runit** (`/etc/sv/data-boar/run`). Ele executa o `cp314t` embutido com `--web` via **`chpst -u databoar`** (`system_accounts` no xbps, não root). O produto **não** chama `systemctl`. Um unit systemd opcional fica em `packaging/init/data-boar.service` (`DynamicUser=yes`) para outros empacotadores e **não** é obrigatório.

Pacotes de distro da camada 2: `openssl zlib libffi tesseract-ocr`. Sem `Depends: python3`.

Os extras de conector (`data-boar-mssql`, …) seguem o mesmo mapa do nfpm e o `EXTRAS_MANIFEST`.

## Gerar o overlay (maintainers)

```bash
uv run python scripts/generate_void_xbps_packages.py --write
uv run python scripts/generate_void_xbps_packages.py --check
```

```bash
# Só parse (glibc, depois musl):
bash scripts/void-xbps-podman-validate.sh --show
bash scripts/void-xbps-podman-validate.sh --show --libc musl

# Pacote completo (staging glibc do mesmo populate do nfpm):
bash scripts/native-nfpm-populate-staging.sh
bash scripts/void-xbps-podman-validate.sh --build
```

O `--build` musl exige staging populado para musl. **Não** reutilize bytes glibc em musl.

O validador e os jobs de CI `xbps-src show` instalam `bash` (shebang), `util-linux` (`getopt` + `runuser`, confirmado com `xbps-query -o /usr/bin/getopt`) e `shadow` (`useradd`), e rodam `./xbps-src` como usuário `builder` não-root — `xbps-src` recusa root.

## Paridade de achados

Instale o `.xbps` e rode o mesmo corpus de referência do install-smoke deb/rpm/apk. A contagem de achados precisa coincidir. O launcher é a mesma árvore embutida + wheelhouse (`/usr/lib/data-boar/.../python3.14t -m data_boar`).

## Cláusula comercial

O `cp314t` embutido **não** libera Enterprise. Os gates continuam os tetos de worker (#551) e `pro_prefilter_accel`.

Ver também: [OS_COMPATIBILITY_TESTING_MATRIX.pt_BR.md](OS_COMPATIBILITY_TESTING_MATRIX.pt_BR.md) (notas `pipx` / wheelhouse no Void) · [USAGE.pt_BR.md](../USAGE.pt_BR.md) (instalação + gerenciadores de processo).
