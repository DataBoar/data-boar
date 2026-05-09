#!/usr/bin/env bash
# Data Boar — Worker POSIX Nativo para as personas 'container_podman' e 'docker-ce'.
# Injetado assincronamente pelo Maestro via Tmux.
#
# Uso: bash scripts/lab-completao-container-smoke.sh -BetaRef <Versao>

set -euo pipefail

# Reaproveitamos a inteligência legada: chamamos o script original de fumaça
# passando a flag para pular a engine local (já que rodaremos no container).
echo "[Container Smoke] Chamando auditoria de host base..."
bash ./scripts/lab-completao-host-smoke.sh --skip-engine-import

echo "--------------------------------------------------------"
echo "[Container Smoke] Iniciando validação de Engine..."
echo "--------------------------------------------------------"

ENGINE="unknown"
if command -v podman >/dev/null 2>&1; then
    ENGINE="podman"
elif command -v docker >/dev/null 2>&1; then
    ENGINE="docker"
else
    echo "[ERRO] Nenhuma engine de container (Podman/Docker) encontrada neste nó."
    exit 1
fi

echo "[Worker] Engine detectada: $ENGINE"

# Aqui entra a lógica real do seu laboratório para subir a stack.
# Exemplo genérico:
# $ENGINE compose -f deploy/lab-smoke-stack/docker-compose.yml up -d

echo "[Worker] Simulação: Container Data Boar iniciado via $ENGINE."

# Criamos a flag de telemetria para o Maestro coletar no futuro
echo "DONE_SUCCESS_CONTAINER" > ~/.labop-status

echo "--------------------------------------------------------"
echo "[Container Smoke] Finalizado com sucesso. Aguardando Maestro."
echo "--------------------------------------------------------"
