# Plan: Completão Orchestration Resilience (Plan-V)

**Status:** Pending
**Date:** 2026-05-03
**Authors:** Fabio Leitao
**Priority:** H0

*   **Status:** In Progress 🚧
*   **Owner:** Fabio Leitao (Performance Engineer III)
*   **Philosophy:** #SREGuardaEvidencias
*   **Target:** `scripts/lab-completao-orchestrate-hybrid-v173-plano-v.ps1`

---

## 🐗 Contexto e Justificativa
O "nascimento" do orquestrador Plano-V revelou instabilidades críticas no ciclo de deploy remoto. A transição de um script linear para um orquestrador resiliente exige que o ambiente (WORKSTATION, LAB-NODE-01 e LAB-NODE-02) esteja em perfeita sincronia binária e lógica, evitando o "silêncio operacional" e falhas de encoding que paralisam a automação.

## 🎯 Objetivos
1.  Eliminar a necessidade de intervenção manual nos nós remotos (Git Pull).
2.  Garantir compatibilidade ASCII total para ambientes legados (PS 5.1).
3.  Prover telemetria em tempo real para evitar a percepção de "script travado".
4.  Implementar gestão de ciclo de vida de imagens Docker/Podman para evitar o uso de código *stale*.

---

## 🛠️ To-Do List: Fatias de Evolução

### Fase 1: Higiene Binária e Portabilidade (Baseline)
*   [x] **ASCII-Safe Enforcement:** Limpeza de caracteres non-ASCII via hex-codes (`\xe3`, `\xe7`) para evitar quebra no PowerShell 5.1.
*   [x] **Nuclear Byte Strip:** Implementar rotina via `perl` para garantir que o script permaneça nos limites 0-127 do ASCII.
*   [x] **Audit Pass:** Garantir que o portão de qualidade (`audit.ps1`) valide 100% da suíte antes de iniciar a orquestração.

### Fase 2: Code Parity (Sincronização Automática)
*   [ ] **Auto-Git Pull Remoto:** Adicionar bloco SSH para disparar `git pull origin main` em cada nó do inventário antes do deploy.
*   [ ] **Lock-File Verification:** Validar se o Hash do commit local coincide com o remoto antes de disparar o container.
*   [ ] **Pre-flight Privilege Check:** Testar conectividade `sudo` (narrow sudoers) antes da fase de montagem para evitar prompts de senha invisíveis.

### Fase 3: Observability & Feedback (Echoes)
*   [ ] **Injeção de Verbosidade:** Adicionar `Write-Host` em cada etapa do handshake (SCP de config, Pull de imagem, Run container).
*   [ ] **Log Streaming:** Capturar a saída do container remoto (`podman logs -f` ou `docker logs -f`) e espelhar no console do orquestrador local.
*   [ ] **Tmux Integration:** Lógica para detectar sessão `completao` ativa e injetar o comando nela, permitindo reconexão manual se o orquestrador cair.

### Fase 4: Image & Lifecycle Management
*   [ ] **Stale Image Detector:** Comparar a data da imagem local com o último commit na pasta `rust/`.
*   [ ] **Force Pull Logic:** Garantir que a tag `1.7.4-rc` (ou a linha de trabalho atual em `pyproject.toml`) seja atualizada se a versão local tiver mais de 24h ou se houver mudanças no binário.
*   [ ] **Host Hygiene Guard:** Implementar check de memória no host (WORKSTATION) para alertar sobre vazamentos de sistema (ex: `gpsvc` leak) antes de iniciar benchmarks sensíveis.

---

## 🚀 Critérios de Aceite (Done-Done)
- [ ] Orquestração completa (WORKSTATION -> LAB-NODE-01/LAB-NODE-02) sem nenhum comando manual via SSH.
- [ ] Telemetria magenta do Rust 1.7.4-rc aparecendo no console local.
- [ ] Zero falhas no `test_powershell_scripts_ascii_safe`.
- [ ] Evidências de performance colhidas com ambiente comprovadamente limpo (RAM < 50%).

---

**SRE Statement:** "Se o orquestrador não consegue curar o ambiente, ele é apenas um script com mais responsabilidades."
