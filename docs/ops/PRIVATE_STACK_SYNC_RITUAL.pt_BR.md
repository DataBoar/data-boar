# Repo privado empilhado — ritual de fim de sessão (operador)

**English:** [PRIVATE_STACK_SYNC_RITUAL.md](PRIVATE_STACK_SYNC_RITUAL.md)

**Objetivo:** Fecho **calmo e repetível** para o **Git aninhado** em **`docs/private/`** (nunca no `origin` público do GitHub), no **espírito** do ritual **`eod-sync`** do repositório público — mas **só** para histórico privado e backups.

**Palavra-chave de sessão (só em inglês):** **`private-stack-sync`** — ver **`.cursor/rules/session-mode-keywords.mdc`**.

---

## O que não é

- **Não** substitui **`check-all`**, **`preview-commit`** ou higiene do **`main`** público.
- **Não** é lugar para **passwords**, **passphrases de volume**, **keyfiles** ou **caminhos de LAN** em arquivos tracked — ficam em notas **gitignored** ou no cofre.

---

## Fluxo típico (alto nível)

1. Quando a árvore privada tiver alterações que queiras registar, garante um estado **honesto** para commit (mesma ideia que “commit limpo” no `main`).
2. Na **raiz do repo do produto**, corre **`scripts/private-git-sync.ps1`** (Windows) ou **`scripts/private-git-sync.sh --push`** (Linux/macOS); opcional **`-Push`** / **`--push`** se a política enviar o repo empilhado para remotes **fora do GitHub**. Os **bare mirrors lab** usam a lista canônica no script (**mini-bt, latitude, t14, alpine-emachines**); **pi3b fica de fora** (SD fragil).
3. Se usares **armazenamento local cifrado** para essa árvore, segue a disciplina **montar → trabalhar → desmontar** descrita em **`docs/ops/PRIVATE_LOCAL_VERSIONING.md`** e nos teus runbooks **privados** de homelab (não duplicados aqui).

### Secrets homelab (`-Push`)

Com **`-Push`**, o script **(a)** faz push Git para **`lab-*`** e para o **bare** `notes-sync.git` no VeraCrypt, **(b)** copia arquivos secretos listados (ex.: **`.env.bitwarden.local`**) para **`working/homelab/`** no volume com verificação de hash, e **(c)** espelha para **pCloud** só se **`P:`** estiver montado, com **retries limitados** no robocopy e **`/XF`** para esses nomes **não** irem para a nuvem de sync. Novos env só-homelab: acrescente o nome do arquivo na lista do script.

### Expectativa do operador (genérico — sem letras de unidade nem caminhos)

Durante o trabalho na árvore privada, **espera-se** uma **unidade montada pelo VeraCrypt** para manter o fluxo de escrita e de **sync/backup** coerente. Se essa montagem **faltar quando era esperada**, trate como **anomalia** e recupere com runbooks **privados** e segredos no **cofre** — **nunca** cole credenciais de volume no chat nem em arquivos **tracked**.

### Assistentes — espelhos de evidência (padrão)

Quando o operador pedir **conferir alinhamento**, **drift**, **sync do histórico privado** ou higiene que claramente envolva **`docs/private/`**, trate **todos os espelhos não-GitHub alcançáveis** como **o mesmo trabalho** — remotos SSH **`lab-*`** **e** um **bare `notes-sync.git` no volume VeraCrypt** quando esse caminho existir na estação (**`scripts/private-git-sync.ps1 -Push`** sonda **`Z:`** primeiro, depois **`Y:`**, quando a raiz dessas unidades existir). **Não** perguntar em redundância “quer também push pro backup?”; **relatar** falhas concretas (montagem em falta, SSH, **`safe.directory`** / *dubious ownership*). Regra canônica: **`.cursor/rules/operator-evidence-backup-no-rhetorical-asks.mdc`** · **[ADR 0040](../adr/ADR-0040-assistant-private-stack-evidence-mirrors-default.md)** (texto EN).

---

## Referências

- **`docs/ops/OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md`** ([EN](OPERATOR_AGENT_COLD_START_LADDER.md)) — escada de arranque (inclui linha do stack privado no router).
- **`docs/ops/PRIVATE_LOCAL_VERSIONING.md`**
- **`scripts/private-git-sync.ps1`**
- **`docs/PRIVATE_OPERATOR_NOTES.md`**
- **Skill:** **`.cursor/skills/stacked-private-sync/SKILL.md`**
