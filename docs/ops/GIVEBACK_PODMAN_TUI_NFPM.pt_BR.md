# Give-back: pacotes nfpm para `podman-tui` (upstream)

**English:** [GIVEBACK_PODMAN_TUI_NFPM.md](GIVEBACK_PODMAN_TUI_NFPM.md)

**Issue:** [#1424](https://github.com/DataBoar/data-boar/issues/1424) · **Relacionado:** pacotes nativos neste repo ([packaging/nfpm/README.md](../../packaging/nfpm/README.md), [#1403](https://github.com/DataBoar/data-boar/issues/1403)).

Isto **não** é um pacote Data Boar. O `containers/podman-tui` publica **zips** nas GitHub Releases. Quem usa distro ainda extrai na mão. O mesmo **nfpm** que usamos aqui pode emitir **deb / rpm / apk / archlinux** a partir do zip Linux **mais** arquivos que só existem na **árvore git** (licença, man, completions).

## O que este repo entrega

| Caminho | Papel |
| ------- | ----- |
| [`giveback/podman-tui/nfpm.yaml.example`](giveback/podman-tui/nfpm.yaml.example) | Config nfpm corrigida (licença + `Maintainer: Nome <email>`) |
| Esta página | Notas de contribuição (DCO; não anexar `.deb` não oficial como produto) |

**Não** anexe `.deb` / `.rpm` construídos localmente a um Release do Data Boar. O upstream precisa construir e **assinar** os próprios artefatos.

## Defeitos do PoC não oficial (não repetir)

1. **Sem arquivo de licença no pacote** — o zip traz só o binário. A política Debian pede `/usr/share/doc/podman-tui/copyright` (copie `LICENSE` do git).
2. **`Maintainer: unofficial build`** — inválido. Use `Nome Completo <email@domínio>` (quem vai manter o packaging no upstream).
3. **Sem man page / completions** — inclua **se** a árvore upstream gerar; não invente documentação.

## Layout sugerido no upstream

1. Faça fork de [containers/podman-tui](https://github.com/containers/podman-tui).
1. Adicione `nfpm.yaml` (comece pelo exemplo daqui). Staging:

   - `LICENSE` → `/usr/share/doc/podman-tui/copyright`
   - binário do zip linux_amd64 (ou `go build`) → `/usr/bin/podman-tui`
1. Estenda `.github/workflows/releaes.yml` (o nome do arquivo é o do upstream) para o job de release rodar `nfpm package` em `deb`, `rpm`, `apk` e `archlinux` e fazer `gh release upload`.
1. Leia **DCO / sign-off** da org `containers/` **antes** de abrir o PR. Commits precisam de `Signed-off-by:`.
1. Cole a URL do PR em [#1424](https://github.com/DataBoar/data-boar/issues/1424).

## Lições para o nfpm do Data Boar (#1403)

- Sempre embarque o **texto da licença** em `contents:`, não só o campo `license:` no YAML.
- `maintainer:` precisa ser um par real `Nome <email>`.
- Zips de release **não** trazem docs completos; puxe man/completions do git.

## Conferir um zip linux oficial (exemplo)

Use o arquivo de checksum **daquela GitHub Release**, não um hash copiado do chat:

```bash
# Troque TAG pela release que você está empacotando (não invente tags).
gh release download TAG --repo containers/podman-tui --pattern '*linux_amd64.zip*' --pattern '*sha256*'
sha256sum -c sha256sum   # ou o nome de arquivo que o upstream realmente publica
```
