#!/bin/bash

# Script de automação para instalação de drivers de sistema
# Foco: Auditoria de Dados (Ubuntu/Debian)

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # Sem cor

echo -e "${GREEN}### Iniciando configuração do ambiente de Auditoria ###${NC}"

# Verificar se é root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Por favor, execute como root ou usando sudo.${NC}"
  exit 1
fi

echo -e "${GREEN}1. Atualizando repositórios...${NC}"
apt-get update && apt-get upgrade -y

echo -e "${GREEN}2. Instalando ferramentas de compilação básicas...${NC}"
apt-get install -y build-essential python3-dev libffi-dev pkg-config libssl-dev libmagic1

echo -e "${GREEN}3. Instalando drivers para Bancos de Dados Comuns...${NC}"
# Postgres
apt-get install -y libpq-dev
# MariaDB / MySQL
apt-get install -y libmariadb-dev-compat libmariadb-dev default-libmysqlclient-dev
# SQLite
apt-get install -y sqlite3 libsqlite3-dev

echo -e "${GREEN}4. Configurando drivers para Microsoft SQL Server (MSSQL)...${NC}"
if ! command -v sqlcmd &>/dev/null; then
  curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor >/usr/share/keyrings/microsoft-archive-keyring.gpg
  curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
  # Detectar versão para o repositório correto
  CODENAME=$(lsb_release -cs)
  REPO_VERSION=$(lsb_release -rs)
  echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-archive-keyring.gpg] https://packages.microsoft.com/ubuntu/${REPO_VERSION}/prod ${CODENAME} main" >/etc/apt/sources.list.d/mssql-release.list
  apt-get update
  ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev
else
  echo "Drivers MSSQL já detectados."
fi

echo -e "${GREEN}5. Instalando dependências para Oracle e IBM DB2 (Bibliotecas de suporte)...${NC}"
# Oracle Instant Client requer libaio1
apt-get install -y libaio1

echo -e "${GREEN}6. Instalando dependências para extração de arquivos (PDF/Docx/Imagens)...${NC}"
# Dependências para processamento de documentos e imagens se necessário
apt-get install -y libxml2-dev libxslt1-dev zlib1g-dev

echo -e "${GREEN}7. Verificando instalação do gerenciador 'uv'...${NC}"
if ! command -v uv &>/dev/null; then
  echo "Instalando o gerenciador uv (pinned tarball + sha256, #1905)..."
  UV_VERSION="0.11.2"
  UV_SHA256="7ac2ca0449c8d68dae9b99e635cd3bc9b22a4cb1de64b7c43716398447d42981"
  UV_TARBALL="uv-x86_64-unknown-linux-gnu.tar.gz"
  UV_URL="https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/${UV_TARBALL}"
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "${tmpdir}"' EXIT
  MAX_RETRIES=5
  for i in $(seq 1 "${MAX_RETRIES}"); do
    if curl --fail --show-error --location --retry 3 --retry-delay 5 --retry-connrefused \
      "${UV_URL}" -o "${tmpdir}/${UV_TARBALL}"; then
      break
    fi
    echo "Download attempt ${i} failed; sleeping $((i * 5))s before retry..."
    sleep $((i * 5))
    if [ "${i}" -eq "${MAX_RETRIES}" ]; then
      echo -e "${RED}Failed to download ${UV_TARBALL} after ${MAX_RETRIES} attempts${NC}" >&2
      exit 1
    fi
  done
  echo "${UV_SHA256}  ${tmpdir}/${UV_TARBALL}" | sha256sum -c -
  tar -xzf "${tmpdir}/${UV_TARBALL}" -C "${tmpdir}"
  UV_BIN="$(find "${tmpdir}" -type f -name uv -perm -u+x | head -1)"
  if [ -z "${UV_BIN}" ] || [ ! -x "${UV_BIN}" ]; then
    echo -e "${RED}uv binary missing from tarball after checksum${NC}" >&2
    exit 1
  fi
  install -m 0755 "${UV_BIN}" /usr/local/bin/uv
  uv --version
else
  echo "Gerenciador uv já está instalado."
fi

echo -e "${GREEN}### Instalação Concluída com Sucesso! ###${NC}"
echo -e "Agora você pode executar: ${GREEN}uv pip install -r requirements.txt${NC}"
