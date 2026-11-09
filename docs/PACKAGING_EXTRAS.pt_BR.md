# Extras Opcionais em Pacotes Nativos

**English:** [PACKAGING_EXTRAS.md](PACKAGING_EXTRAS.md)

## Resumo

Documentação da receita suportada para extras opcionais quando instalar o Data Boar via pacotes nativos (.rpm, .deb, .apk, .pkg.tar.zst). O pacote nativo contém apenas o Python embutido; extras opicionais requerem um venv com `--system-site-packages` sobre o Python embutido.

## Receita Suportada

A abordagem documentada é criar um venv sobre o Python embutido e instalar extras ali:

```bash
# Criar venv com site packages do sistema sobre o Python embutido
python3 -m venv --system-site-packages ~/databoar-xvenv

# Ativar o venv
source ~/databoar-xvenv/bin/activate

# Instalar Data Boar extras com status documentado
pip install "data-boar[nosql]"       # instala pymongo, redis
pip install "data-boar[dataformats]" # instala pyarrow, fastavro, dbfread
pip install "data-boar[compressed]"  # pode falhar: dependência brotli
pip install "data-boar[dl]"          # pode falhar: safetensors, Rust build
```

## Tabela Extra × Status (Evidência de AlmaLinux 9.8, data-boar-1.8.0.x86_64.rpm)

|| Extra | Resultado no venv | Dependências Sistema |
||---|---|---|
|| `nosql` (pymongo 4.19.0, redis 8.1.0) | ✅ Instala e importa | — |
|| `dataformats` (pyarrow 26.0.1, fastavro 1.13.1, dbfread 2.0.7) | ✅ Instala e importa | — |
|| `mssql` (pymssql 2.3.13) | ✅ Instala, ❌ importa falha | `libsybdb.so.5` (biblioteca FreeTDS; dnf/EPEL não testado) |
|| `compressed` (py7zr) | ❌ Falha | `brotli` falha em build de fonte (sem cp314t wheel; sem gcc/cmake no VM) |
|| `dl` (sentence-transformers) | ❌ Falha | `safetensors` falha em build de fonte (sem Rust no VM) |

**Não testado**: `richmedia`, `shares`, `detection-fuzzy`, `bigdata`

## Dependências Sistema por Extra

|| Extra | Dependência Sistema | Método de Instalação |
||---|---|---|
|| `mssql` | FreeTDS (`libsybdb.so.5`) | dnf/EPEL ou compilar de fonte |
|| `compressed` | brotli development | gcc/cmake para build de fonte, ou wheel pré-compilado |
|| `dl` | toolchain Rust | `dnf install rust` ou build de fonte |

## Cobertura de Formato

Atualmente documentado e testado em: **AlmaLinux 9.8 (formato RPM)**

Ainda não testado: `.deb` (Debian/Ubuntu), `.apk` (Alpine), `.pkg.tar.zst` (Arch)

**Decisão requerida** (veja PLAN_PACKAGING_EXTRAS.md): Publicar subpackages como assets de release, manter receita venv-only, ou ambos. Estratégia para extras `compressed` e `dl` (wheels cp314t ou documentar prerequisito de compilador).

## Executar Scans do Venv

Para confirmar que um scan usa os módulos do venv (não apenas import funciona):

```bash
# Ativar venv
source ~/databoar-xvenv/bin/activate

# Verificar módulos são importáveis
python -c "import pymongo; import pyarrow; import py7zr"  # verificar cada extra

# Executar scan do Data Boar
data-boar scan -- --demo
```

Registre o comando exato usado e verifique se o scan identifica os módulos extras.