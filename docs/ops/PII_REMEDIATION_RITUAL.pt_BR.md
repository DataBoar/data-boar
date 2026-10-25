# Ritual de remediação de PII — árvore pública (sob demanda)

**English:** [PII_REMEDIATION_RITUAL.md](PII_REMEDIATION_RITUAL.md)

Este documento é o **ritual sob demanda** para **mantenedor / operador** quando decidirem que é hora de **rever literais pessoais ou sensíveis** que possam ter entrado por engano na **árvore rastreada** e na **higiene do histórico Git** relacionada —**não** é um cron automático. **Esperança não é plano:** combina **guards rápidos**, **greps baratos**, **lista de seeds privada** e **classificação explícita** para que distração não reabra a mesma classe de vazamento.

**Cadência canônica e gate SAFE:** [PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md) (Partes I–III: corridas curta / média / longa, visibilidade fork vs clone, kit de reescrita de histórico). Este ritual **estreita** como executar uma passagem **focada** **sem gastar tokens** com trabalho duplicado.

**Palavra-chave de sessão (token em inglês):** escreva **`pii-remediation-ritual`** no chat para o assistente alinhar a sessão a este fluxo (mesma convenção que **`pii-fresh-audit`**, **`private-stack-sync`** — ver **`.cursor/rules/session-mode-keywords.mdc`** e **`AGENTS.md`**).

---

## Quando rodar (julgamento, não automação)

Exemplos de gatilho:

- Depois de uma sessão **densa de docs ou scripts** em que caminhos reais, e-mails literais ou nomes de terceiros possam ter entrado.
- Antes de um merge de **alta visibilidade** (revisão de parceiro, imprensa, novo colaborador com acesso só ao clone).
- Quando **`tests/test_pii_guard.py`** ou **`pii_history_guard.py`** **falharem** no **`main`**.
- Quando o **arquivo de seeds privado** mudar e quiseres um **inventário no HEAD** antes de confiar só no pickaxe de histórico.

**Não** substitui **`pii-fresh-audit`** (clone temporário completo + guards de histórico)—usa isso para **confiança nível release** no Windows; usa **este ritual** para **trabalho cirúrgico no HEAD + classificação** e ponteiros para ferramentas de longo prazo.

---

## Pacote privado (fonte da verdade para “o que caçar”)

Arranque a partir de **[`docs/private.example/security_audit/README.md`](../private.example/security_audit/README.md)**:

| Artefato | Papel |
| --------- | ----- |
| **`docs/private/security_audit/PII_LOCAL_SEEDS.txt`** | Um literal por linha para **`git grep -F`** (HEAD) e **`git log -S`** (histórico). Fora do GitHub público. |
| **`docs/private/security_audit/PII_CONTEXT_DECISIONS_LOG.pt_BR.md`** (ou equivalente) | **ACEITÁVEL** vs **VAZAMENTO** por seed/contexto—evita reabrir o mesmo hit em toda sessão. |

**Regra prática:** identidade **pública de upstream** (URLs canónicas org/repo no GitHub) pode ser **ACEITÁVEL** como verdade do produto; **literais de correio**, **segmentos de caminho de perfil**, **URLs internas do empregador** e **nomes de colaboradores não públicos** em docs de operador são quase sempre **VAZAMENTO** até trocarem por placeholders ou **`docs/private/`**.

---

## Ordem de execução conscientes de token (sinal mais barato primeiro)

Na **raiz do repositório** no computador com o clone em que trabalha (normalmente o **PC Windows principal** para helpers PowerShell).

1. **Guard rápido alinhado ao CI (segundos):**

   ```bash
   uv run pytest tests/test_pii_guard.py tests/test_talent_ps1_tracked_no_inline_pool.py tests/test_talent_public_script_placeholders.py -q
   ```

   Apanha **literais e padrões** definidos em código na **árvore rastreada**—**não** a lista completa de seeds privados.

2. **Varredura HEAD com seeds privados (minutos):** Para cada linha não comentada em **`PII_LOCAL_SEEDS.txt`**, rode **`git grep -n -F "<linha>" HEAD`** (ou um ciclo local pequeno). Classifique cada hit com o **log de decisões**; só depois edite **arquivos rastreados**. **Nota:** **`scripts/run-pii-local-seeds-pickaxe.ps1`** roda **`git log --all -S`** por seed (histórico), não **HEAD**—use-o para **inventário pickaxe**, não como única verificação de HEAD.

3. **Inventário de histórico (opcional, mais pesado):** `.\scripts\run-pii-local-seeds-pickaxe.ps1` (use **`-Limit N`** para smoke). Com os resultados decida se **`git filter-repo`** / **`scripts/run-pii-history-rewrite.ps1`** entra no âmbito—**nunca** no **clone canônico L-series** sem plano explícito do operador; ver **`docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**.

4. **Clone fresco + gate de histórico completo (nível release, Windows):** Palavra-chave **`pii-fresh-audit`** → **`scripts/pii-fresh-clone-audit.ps1`** conforme **`docs/ops/PII_FRESH_CLONE_AUDIT.pt_BR.md`**.

5. **Verificação de segmento de usuário Windows:** **`scripts/new-b2-verify.ps1`** (opcional **`-TargetUserSegment`**) clona em **`%TEMP%`** e, para segmentos **fora da allowlist**, roda **`git log -S`** e **`git grep` em lotes** (saída em arquivo UTF-8). Sem segmento ou com **`fabio`**, pula sondas de identidade pública do mantenedor (ver **`PII_CONTEXT_DECISIONS_LOG`**). Em histórico enorme use **`-MaxRefsToScan N`**.

**Lab-op:** opcional **`ssh`** a um host Linux para **`clean-slate.sh`** / **`pii_history_guard.py`** conforme **[PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md)** §H—no clone de lab, **`docs/private/`** **continua sendo** o **local** para **seeds reais**; **não** há atalho para copiar **`PII_LOCAL_SEEDS.txt`** para esse host.

---

## Impedir novos vazamentos (padrões em que a equipe confia)

- **Regras:** **`.cursor/rules/public-tracked-pii-zero-tolerance.mdc`**, **`private-pii-never-public.mdc`**, **`clean-slate-pii-self-audit.mdc`**.
- **Política de contribuição:** **`CONTRIBUTING.pt_BR.md`** → *Repositório público: identificadores de terceiros e histórico Git*; pool de talento em JSON **gitignored** fundido em runtime (**`scripts/talent.ps1`**).
- **Pré-merge:** **`.\scripts\check-all.ps1`** (inclui guards do repositório); **`safe-commit`** só como **fotografia**, não como gate completo.
- **Padrão de automação:** quando uma classe de erro repete, **acrescenta teste ou script** (estreito, rápido) em vez de esperar que o próximo autor lembre — ver **`AGENTS.md`** (*Proactive anti-regression automation*).

---

## Depois das edições

- Volta a correr o passo **1** (pytest guards) no mínimo.
- **`git status`**: confirma que **`docs/private/`** e **`.env`** **não** estão preparados para commit.
- Atualiza o **log de decisões privado** com data + seed + classificação para o próximo ritual sair mais barato.

---

## Ligações relacionadas

- [PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md) — cadência, checklist SAFE, Linux **`clean-slate`**, avisos de reescrita de histórico.
- [PII_FRESH_CLONE_AUDIT.pt_BR.md](PII_FRESH_CLONE_AUDIT.pt_BR.md) — auditoria Windows one-shot em clone fresco.
- [PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md](PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md) — o que **não** correr no clone canônico de dev.
- [TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md](TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md) — preferir scripts do repositório em vez de shell ad hoc; narrativa mais longa em [TOKEN_AWARE_USAGE.md](../plans/TOKEN_AWARE_USAGE.md).
- [CURSOR_AGENT_POLICY_HUB.pt_BR.md](CURSOR_AGENT_POLICY_HUB.pt_BR.md) — índice rápido para agentes (linha PII).
