# Receita de Instalação FreeBSD 15.1

**English:** [FREEBSD_INSTALL.md](FREEBSD_INSTALL.md)

## Resumo

Validação da instalação do Data Boar 1.8.0 em FreeBSD 15.1 amd64 em VM KVM (4 vCPU, 5 GB de RAM). Esta receita documenta os passos comprovados para instalar o Data Boar em sistemas FreeBSD.

## Instalação

O passo chave é instalar pacotes nativos **antes** de tentar a instalação via pip:

```bash
# Instalar pacotes do sistema primeiro
pkg install cmake ninja

# Depois instalar o Data Boar via pip em ambiente virtual com pacotes do sistema
python -m venv --system-site-packages ~/databoar-venv
pip install data-boar
```

## Resultados Verificados

- **52 de 67 dependências** resolvidas via `pkg` (gerenciador de pacotes do FreeBSD)
- **Fora do intervalo de pins**: `pandas>=3.0.3`, `starlette==1.9.0`, `fastapi>=0.143` e outras
- **3 wheels geradas**: `freebsd_15_1_release_p6_amd64` com checksums SHA256
- **Tempo total de build**: ~1h30m para compilação sdist

## Problemas Conhecidos e Workarounds

| Extra/Módulo | Status | Observações |
|---|---|---|
| `compressed` | ✅ Funciona | Via instalação pkg |
| `nosql` | ✅ Funciona | Via instalação pkg |
| `dataformats` | ✅ Funciona | Via instalação pkg |
| `shares` | ✅ Funciona | Via instalação pkg |
| `dl` (torch) | ✅ Funciona | Via pkg (py312-torch) |
| `py312-py7zr` | ❌ Falha | Versão pkg 0.22.0 reprova 7 testes; use pip 1.1.4 |
| `grpcio` | ✅ Funciona | Use py312-grpcio do pkg |
| `pymssql` | ⚠ Apenas compilador | Requer biblioteca FreeTDS |

## Benchmark do Prefiltro Rust

Benchmark isolado do prefiltre Rust em VM FreeBSD (200k linhas, 2 aquecimentos + 5 medições):

- **8.59× de speedup** vs baseline Python-only
- `host_profile: freebsd-amd64`, KVM `-cpu host`
- Perfil `official_pro_v1` mostra 0.574× (Pro mais lento)
- Atualmente pin artifact como `linux-x86_64` (4.69×); pendente re-pin com `freebsd-amd64`

## Armadilha IPv6/CDN (testes em VM)

Ao testar em VM com rede que filtra IPv6:

- `cdn.netbsd.org` retorna **503** para pacotes fora do cache
- Use `ftp.netbsd.org` em vez disso
- Rede descarta IPv6 silenciosamente; use `dhcpcd -4` e `ipv6=off`

## Observação de Desempenho

Números publicados devem carregar o aviso de perfil freebsd-amd64: host único, perfil novo, pin artifact após correção de commit e aplicação do perfil.