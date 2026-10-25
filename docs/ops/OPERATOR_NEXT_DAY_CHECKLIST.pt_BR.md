# Sugestão de dia — lab-op + produto (checklist reutilizável)

**English:** [OPERATOR_NEXT_DAY_CHECKLIST.md](OPERATOR_NEXT_DAY_CHECKLIST.md)

**Objetivo:** Ordem sugerida para um **dia inteiro** de trabalho seu (operador), misturando **manutenção leve**, **homelab** e **uma** fatia de produto — sem depender do agente para SSH, GitHub ou hardware. Ajuste horários à tua energia; risca o que não for para hoje.

**Contexto mais largo:** [OPERATOR_MANUAL_ACTIONS.pt_BR.md](OPERATOR_MANUAL_ACTIONS.pt_BR.md) · [PLANS_TODO.md](../plans/PLANS_TODO.md) § “Resume next session”.

**Foco de um dia (datado):** ver **[today-mode/README.pt_BR.md](today-mode/README.pt_BR.md)** (checklists indexados). Exemplo atual: [OPERATOR_TODAY_MODE_2026-04-02.pt_BR.md](today-mode/OPERATOR_TODAY_MODE_2026-04-02.pt_BR.md) ([EN](today-mode/OPERATOR_TODAY_MODE_2026-04-02.md)). **Delta WRB (exemplo):** [WRB_DELTA_SNAPSHOT_2026-04-16.pt_BR.md](WRB_DELTA_SNAPSHOT_2026-04-16.pt_BR.md). **Versão de trabalho atual `1.6.8`** vs publish em [today-mode/PUBLISHED_SYNC.pt_BR.md](today-mode/PUBLISHED_SYNC.pt_BR.md).

---

## Manhã (≈ 2–3 h) — segurança + desbloqueios

| #  | Atividade                                                                                                                                                                    | Critério “feito”                                                      |
| -  | ---------                                                                                                                                                                    | ----------------                                                      |
| M1 | **Band A (–1):** abrir GitHub → **Security → Dependabot** — contar alertas ou fechar **um** com PR/`pyproject` + `uv lock` + `requirements.txt` + `check-all`                | Um alerta tratado **ou** registro “nada crítico hoje” em nota privada |
| M2 | **Band A (–1b):** se fizeste push de imagem recente — `docker scout quickview` na tag que usas                                                                               | Screenshot ou nota em `docs/private/` se houver CVE a seguir          |
| M3 | **LAB-OP — `<lab-host-2>` / SBC secundário:** resolver `git status` no script `homelab-host-report.sh` **ou** correr `lab-op-sync-and-collect.ps1 -SkipGitPull` só para relatório | Log novo em `docs/private/homelab/reports/` **ou** pull limpo         |
| M4 | **ThinkPad LAB-NODE-01 + LMDE 7:** continuar [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) (mapa §0–§8) até checklist §8 verde **ou** marcar onde paraste | Seção atual documentada numa linha em nota privada                    |

Nota: se não tiver LAB-NODE-01 à mão, troca M4 por mais uma linha de Band A ou M3.

---

## Tarde (≈ 3–4 h) — validação ou comunicação externa

| #  | Atividade                                                                                                                                                                                             | Critério “feito”                                                                     |
| -  | ---------                                                                                                                                                                                             | ----------------                                                                     |
| T1 | **Ordem –1L:** em **um** host lab, [HOMELAB_VALIDATION.pt_BR.md](HOMELAB_VALIDATION.pt_BR.md) §1.1–1.2 (mínimo) **+** §2 sintético **ou** §1.3–1.5 Docker se já tiver contentores a funcionar       | Nota datada com pass/fail; saídas em `docs/private/` se quiser revisão pelo agente |
| T2 | **Corporate-Entity-C (opcional):** se quiser fechar o loop com revisores — enviar e-mail com caminhos de [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md) e referência a `Corporate-Entity-C_ANALISE_2026-03-18.md` | Mensagem enviada **ou** rascunho guardado + data para enviar                         |
| T3 | **Leitura só (sem instalar):** percorrer [PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md) §1 e decidir **A ou B** + **C ou D** para o futuro             | Uma frase no teu runbook privado                                                     |

---

## Fim de tarde / noite leve (≤ 1 h)

| #  | Atividade                                                                                                                                                             | Critério “feito”                                |
| -  | ---------                                                                                                                                                             | ----------------                                |
| N1 | Atualizar **`docs/private/WHAT_TO_SHARE_WITH_AGENT.md`** (estado homelab, bloqueios, próximo alvo)                                                                    | Arquivo salvo                                   |
| N2 | Se o **Task Scheduler SNMP** estiver ativo — abrir última linha do `snmp_LAB-ROUTER-01_probe_*.log` em `reports/`                                                              | Olhar “OK”/erros; nada a fazer se estiver verde |
| N3 | **Uma** fatia produto **só** se sobrar energia: ver tabela “What to start next” em [PLANS_TODO.md](../plans/PLANS_TODO.md) (ex.: FN reduction, strong crypto Phase 1) | Issue/branch nomeados para a manhã seguinte     |

---

## Ritual curto de abertura e fechamento (anti-caos)

- **Abertura (5 min):** rodar `carryover-sweep` (ou `.\scripts\operator-day-ritual.ps1 -Mode Morning`) e escolher apenas uma frente principal do dia.
- **Fechamento (5-10 min):** rodar `eod-sync` (ou `.\scripts\operator-day-ritual.ps1 -Mode Eod`) e registrar no `CARRYOVER` o que ficou pendente com data.
- **Regra simples:** se não está no today-mode datado ou no carryover, não existe para amanhã.

---

## O que o agente **não** faz por ti (lembrar)

- SSH aos hosts, `sudo` no LAB-NODE-01, abrir browser no GitHub com a tua conta.
- Enviar e-mail à Corporate-Entity-C — só pode preparar texto.
- Decidir RAM disponível no portátil para Grafana/Graylog — documentas **tu** depois de medir.

---

**Dica:** no início do dia seguinte no chat, você pode escrever: *“Seguir OPERATOR_NEXT_DAY_CHECKLIST.pt_BR.md; feito M1–M3, bloqueio em M4 por X.”*
