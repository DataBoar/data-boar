# Gordon (Docker AI) — como usamos sem regressões

**English:** [GORDON_DOCKER_AI_USAGE.md](GORDON_DOCKER_AI_USAGE.md)

Finalidade: usar o assistente “Gordon” (Docker) para acelerar trabalho de Docker/Compose/Dockerfile **sem** vazar segredos, sem copiar detalhes de homelab para docs rastreados, e sem introduzir regressões.

Este arquivo é um guia de fluxo: a saída do Gordon é um **insumo**, não uma política automática.

## Para que o Gordon é melhor (alto ROI)

- **Troubleshooting** de Docker Desktop / BuildKit / Compose com passos repetíveis.
- Sugestões de **Dockerfile** para caching e hardening (multi-stage, non-root).
- **Compose** overrides para dev/lab (profiles, volumes, healthchecks).
- Comandos de validação **pré-push / pós-push** para tags no Docker Hub (sem UI).

## Linhas vermelhas (nunca colar no Gordon)

- Tokens, PATs, senhas, chaves privadas.
- Hostnames reais, subnets RFC1918 e inventário do homelab (isso é `docs/private/`).
- Qualquer coisa que você não colaria num issue público.

## Padrão de prompt token-aware

Faça **uma** pergunta estreita por vez. Prefira saídas que viram artefatos que o repo controla:

- “Me dê um checklist mínimo de reprodução.”
- “Me dê um diff pequeno de Dockerfile e explique impacto no cache.”
- “Me dê um compose override para `/data` + healthcheck.”
- “Me dê comandos de validação pós-push.”

Evite prompts do tipo “tudo sobre Docker”.

## Transformar saída do Gordon em trabalho no repo (formato aceito)

1. Extraia um **artefato concreto** que a gente consegue manter:
   - um script em `scripts/`,
   - uma mudança de doc em `docs/`,
   - ou um teste de regressão em `tests/`.
1. Prefira wrappers do repo para manter o transcript curto:
   - Gates de qualidade: `.\scripts\check-all.ps1`, `.\scripts\lint-only.ps1`, `.\scripts\quick-test.ps1`
   - Higiene/build Docker: `.\scripts\docker-lab-build.ps1`, `.\scripts\docker-hub-pull.ps1`, `.\scripts\docker-prune-local.ps1`
1. Validar **no regression**:
   - só docs: `.\scripts\lint-only.ps1`
   - caso contrário: `.\scripts\check-all.ps1`

## Relacionado

- [Docker setup (MCP, build, push)](../DOCKER_SETUP.pt_BR.md) · [EN](../DOCKER_SETUP.md)
- [Limpeza de branches e Docker](BRANCH_AND_DOCKER_CLEANUP.pt_BR.md) · [EN](BRANCH_AND_DOCKER_CLEANUP.md)
- Guardrail do Cursor: `.cursor/rules/gordon-docker-ai-token-aware.mdc`
