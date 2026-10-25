# Publicações sociais, today-mode e carryover

**English:** [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md)

**Objetivo:** Ligar **checklists datados** (`OPERATOR_TODAY_MODE_*.md`), a **fila de carryover** e o trabalho editorial **privado** em **`docs/private/social_drafts/`**, para posts planejados não ficarem invisíveis, adiamentos terem **data**, e posts manuais ad-hoc deixarem **rastro** no hub e, opcionalmente, em **arquivos** de **evidência**.

**Isto não publica por ti:** é **processo + caminhos**. O assistente segue estas regras quando usas **`today-mode`**, **`carryover-sweep`**, **`eod-sync`** ou **`social-today-check`** (ver **`.cursor/rules/session-mode-keywords.mdc`**).

---

## Fonte de verdade (árvore privada)

| O quê | Onde |
| --- | --- |
| Inventário (L\*/X\*/T\*/IG\*/W\*, URLs, estado) | **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** |
| Grelha do mês (plan vs feito) | **`docs/private/social_drafts/editorial/EDITORIAL_MASTER_CALENDAR_YYYY-MM.pt_BR.md`** (ajusta o mês) |
| Rascunhos Markdown + regra de prefixo | **`docs/private/social_drafts/drafts/`** — ver **Convenção de nomes** no hub |

---

## Manhã (`carryover-sweep` / `operator-day-ritual.ps1 -Mode Morning`)

1. Olhar o **SOCIAL_HUB** por linhas com **Alvo editorial** em **hoje** ou **amanhã** e **Estado** **`draft`**, **`scheduled`** ou **`deferred`** (com nota).
2. Olhar a **linha do calendário** do mês para **hoje** / **amanhã** (se existir **arquivo** do calendário para o mês atual).
3. Se não houver nada, parar — **sem spam**.

**Dica:** o ritual da manhã imprime caminhos para o hub e para qualquer **`EDITORIAL_MASTER_CALENDAR_*.pt_BR.md`** em **`editorial/`** quando existir.

---

## Adiar / carryover

Se um post planeado **não** sair:

1. **SOCIAL_HUB:** **`deferred`** (ou manter **`draft`**) e nova data em **Alvo** ou **URL / notas**.
2. **Renomear** o rascunho com prefixo **`YYYY-MM-DD`** = **nova** data planejada (ver README do hub).
3. **EDITORIAL_MASTER:** ajustar a linha ou carryover para o mês seguinte.
4. **Opcional:** uma linha em **`docs/ops/today-mode/CARRYOVER.md`** só se o adiamento for compromisso **real** entre dias — não para cada micro-ajuste.

---

## Fim do dia (`eod-sync`)

Antes de fechar: se **publicaste** algo hoje, atualiza o **SOCIAL_HUB** (**Estado**, **Publicado em**, **URL**). Se só **agendaste**, **`scheduled`** + nota se fizer sentido.

---

## Posts manuais ad-hoc (blog / Data Boar / qualquer rede)

Quando publicas **sem** rascunho prévio no inventário (ou o assistente fica a saber depois):

1. **SOCIAL_HUB:** linha nova ou atualizada (**id** L\*/X\*/…), **`published`**, data, permalink, nota (**manual / não planeado**).
2. **Evidência (opcional e recomendado):** criar **arquivo** em **`docs/private/social_drafts/drafts/evidence/`** (cria a pasta se não existir). Padrão de nome (uma linha):

   `YYYY-MM-DD_evidence_<rede>_<slug-curto>.md`

   Conteúdo: título, URL **pública**, **locale**, parágrafo do que foi ao ar (colar ou resumo), e cuidado com **PII/comercial** — sem segredos.

3. **Prefixo:** data **real** de publicação (mesma regra dos outros drafts).

Esta pasta segue **gitignored** do `origin` como o resto de **`docs/private/`**; faz commit no **repo privado empilhado** quando usares.

---

## Comportamento do assistente (Cursor)

- Com **`today-mode YYYY-MM-DD`**: depois de abrir o checklist, **opcionalmente** ler hub + calendário e listar linhas **draft** com alvo **nesse dia** ou **no dia seguinte** (se os **arquivos** existirem). **Não** inventar posts; **não** colar URLs em **issues/PRs públicos** sem política de redação.
- Com **`social-today-check`**: mesmo olhar, lembrete **curto** em pt-BR se algo estiver atrasado ou para hoje.
- Se reportares post **novo** manual: oferecer atualizar o **hub** + rascunhar **evidência** em **`drafts/evidence/`** (tu colas o texto).

---

## Ligações

- **`docs/ops/today-mode/README.pt_BR.md`** — índice today-mode
- **`docs/ops/today-mode/CARRYOVER.pt_BR.md`** — fila viva
- **`docs/private/social_drafts/README.md`** (privado) — layout + prefixo
- **Skill:** **`.cursor/skills/operator-social-today-alignment/SKILL.md`**
