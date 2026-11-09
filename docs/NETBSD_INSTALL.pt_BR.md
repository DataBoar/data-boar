# Receita de Instalação NetBSD 11.1

**English:** [NETBSD_INSTALL.md](NETBSD_INSTALL.md)

## Resumo

Validação da instalação do Data Boar 1.8.0 em NetBSD 11.1 amd64. Esta receita documenta os passos comprovados para instalar o Data Boar em sistemas NetBSD usando o gerenciador de pacotes pkgsrc.

## Instalação

O NetBSD usa o sistema de pacotes binários `pkgsrc` via `pkgin`. Os passos principais são:

```bash
# Instalar dependências do Data Boar via pkgin
pkgin install py312-numpy py312-scipy py312-pandas py312-cmake py312-ninja

# Alternativa: usar pkgsrc de fonte se pacotes binários não estiverem disponíveis
# cd /usr/pkgsrc/devel/ninja && make install

# Instalar o Data Boar via pip em ambiente virtual com pacotes do sistema
python -m venv --system-site-packages ~/databoar-venv
pip install data-boar
```

## Resultados Verificados

- **Repositório de pacotes binários pkgsrc**: `.../packages/NetBSD/amd64/11.1/All`
- **Observação sobre CDN**: `cdn.netbsd.org` retorna **503** para pacotes fora do cache; use `ftp.netbsd.org`
- **Observação de rede VM**: Sem IPv6 suportado; use `dhcpcd -4` e `ipv6=off` em QEMU
- **Pacotes binários disponíveis**: `py312-numpy/scipy/pandas/scikit-learn(1.8.0)/cryptography`, `rust`, `py312-torch-2.8.0`
- **Indisponíveis via pkgsrc**: `pymongo`, `py7zr`, `transformers`, `tokenizers`, `safetensors`, `sentence-transformers` (vieram do PyPI)

## Extras Disponíveis via Binário

| Extra/Módulo | Status | Observações |
|---|---|---|
| `core` | ✅ Funciona | Instalação base |
| `--demo` | ✅ Funciona | Modo demo |
| `compressed` | ✅ Funciona | Via instalação pkg |
| `nosql` | ✅ Funciona | Via instalação pkg |
| `dataformats` | ✅ Funciona | Via instalação pkg |
| `dl` | ❌ Não disponível | Requer pacotes PyPI (safetensors, sentence-transformers etc.) |

## Armadilha IPv6

VM sem IPv6 (rede do operador descarta): QEMU `ipv6=off` + `dhcpcd -4`. Sempre teste com IPv4 apenas.

## Workaround para Pacotes Faltantes

Para pacotes indisponíveis via pkgsrc, instale do PyPI dentro do venv com `--system-site-packages`:

```bash
pip install py7zr sentence-transformers
```

Observação: Alguns pacotes podem falhar em compilar sem compilador ou ferramenta Rust disponível na VM.