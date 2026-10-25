#!/bin/bash
# scripts/lab-completao-container-smoke.sh
# Inspirado na arquitetura FabioLeitao/bash_localiza_danfe_por_id_de_upload

set -euo pipefail

# 1. Mapeamento de Binários (SRE Best Practice de Fabio Leitao)
ECHO=$(command -v echo || echo "")
BASH=$(command -v bash || ${ECHO} "")
ZSH=$(command -v zsh || ${ECHO} "")
DASH=$(command -v dash || ${ECHO} "")
DOCKER=$(command -v docker || ${ECHO} "")
PODMAN=$(command -v podman || ${ECHO} "")
HOSTNAME=$(command -v hostname || ${ECHO} "")
DATE=$(command -v date || ${ECHO} "")
TEE=$(command -v tee || ${ECHO} "")

# 2. Configurações de Caminhos[cite: 11]
PASTA_LOG="${HOME}/log"
ARQUIVO_LOG="${PASTA_LOG}/lab-completao-container.log"
STATUS_FILE="${HOME}/.labop-status"

# Função de Log padronizada e resiliente[cite: 11]
do_log_() {
    local LEVEL=$1
    shift
    local MSG=$*
    local TS=$(${DATE} +"%Y-%m-%d %T")
    [ ! -d "${PASTA_LOG}" ] && mkdir -p "${PASTA_LOG}"
    ${ECHO} "${TS} - [${LEVEL}] - ${MSG}" | ${TEE} -a "${ARQUIVO_LOG}"
}

# 3. Lógica de Execução
do_log_ INFO "Iniciando validação de Engine no host $(${HOSTNAME})..."

# Reaproveita a inteligência legada chamando o auditor de host[cite: 14]
# O redirecionamento aqui garante que o log do host-smoke caia no log do container-smoke
${BASH} ./scripts/lab-completao-host-smoke.sh --skip-engine-import >> "${ARQUIVO_LOG}" 2>&1

ENGINE="none"
if [ -x "$PODMAN" ]; then
    ENGINE="podman"
elif [ -x "$DOCKER" ]; then
    ENGINE="docker"
fi

if [ "$ENGINE" == "none" ]; then
    do_log_ ERROR "Nenhuma engine de container (Docker/Podman) encontrada!"
    ${ECHO} "FAILED_NO_ENGINE at $(${DATE} +'%H:%M:%S')" > "${STATUS_FILE}"
    exit 1
fi

do_log_ OK "Engine detectada: ${ENGINE}"
#do_log_ INFO "Simulação: Container Data Boar iniciado via ${ENGINE}."
do_log_ INFO "Iniciando: Container Data Boar RC na porta 9002 via ${ENGINE}..."

# NOVO: Limpa resíduos da execução anterior (Evita o Fatal Error)
${ENGINE} rm -f data-boar-rc 2>/dev/null || true

# Execução real via Podman/Docker usando o volume já sincronizado pelo Maestro
# --scan-compressed, --scan-stego e --content-type-check ativados via benchmark-rc.yaml
${ENGINE} run -d \
  --name data-boar-rc \
  -p 9002:8080 \
  -v "$(pwd):/app:ro" \
  -w /app \
  ghcr.io/fabioleitao/data-boar:1.7.4-rc \
  uv run data-boar scan --config tests/config/benchmark-rc.yaml --allow-insecure-http

# 4. Finalização e Telemetria
FINAL_TS=$(${DATE} +"%H:%M:%S")
${ECHO} "DONE_SUCCESS_CONTAINER at ${FINAL_TS}" > "${STATUS_FILE}"
do_log_ OK "Finalizado com sucesso. Status persistido em ${STATUS_FILE}."
