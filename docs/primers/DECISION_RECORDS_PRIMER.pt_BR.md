# Primer de registros de decisão — ADR → MADR → UMADR

**English:** [DECISION_RECORDS_PRIMER.md](DECISION_RECORDS_PRIMER.md)

Este primer é para **novos colaboradores, mantenedores e auditores** que veem arquivos
`docs/adr/ADR-NNNN-*.md` e perguntam: *o que é um ADR, por que o formato é tão rígido e o que
significa o "U" de UMADR?* Ele ancora vocabulário; as regras vinculantes vivem nos próprios ADRs.

**Relacionado:** [GLOSSARY.pt_BR.md](../GLOSSARY.pt_BR.md) (§6) · [índice de ADRs](../adr/README.md) · [docs/hubs/INDEX.md](../hubs/INDEX.md)

---

## 1. Por que registrar decisões

O código mostra **o que** o sistema faz; raramente mostra **por que** um caminho foi escolhido em
vez das alternativas. Seis meses depois o "porquê" se perde, e alguém rediscute um trade-off já
resolvido ou reverte em silêncio uma restrição deliberada. Um **registro de decisão** captura o
**contexto**, a **decisão** e as **consequências** para que o raciocínio sobreviva às pessoas que
estavam na sala.

---

## 2. ADR — Architectural Decision Record (a origem)

- **Criado por Michael Nygard** no post de 2011 *"Documenting Architecture Decisions."*
- **Ideia:** um arquivo Markdown curto e imutável por decisão, numerado em sequência
  (`ADR-0001`, `ADR-0002`, …), versionado **ao lado do código**.
- **Seções centrais:** *Contexto* (forças em jogo), *Decisão* (o que escolhemos), *Consequências*
  (o que fica mais fácil ou mais difícil), além de um *Status*.
- **Imutável por convenção:** você **não** reescreve a história — você **substitui** um ADR antigo
  por um novo. A trilha de decisões substituídas é, por si só, valiosa.

---

## 3. MADR — Markdown Any Decision Records (o template)

- **MADR** é um **template e convenção abertos** amplamente usados para escrever ADRs em Markdown
  (o "Any" generaliza de *arquitetural* para *qualquer* decisão significativa).
- Padroniza o cabeçalho e as seções (título, status, contexto/problema, opções consideradas,
  resultado da decisão, prós/contras) para que os registros sejam **consistentes e amigáveis a
  ferramentas** entre projetos.
- É um **padrão de comunidade**, não um produto — você adota e adapta.

---

## 4. UMADR — o padrão deste repositório (o "U" é de **hUman** / **yoU**)

O Data Boar usa **UMADR (Unified MADR)**, definido no
[ADR-0045](../adr/ADR-0045-adr-metadata-and-format-standardization.md). Ele estende o MADR com a
disciplina que este projeto precisa:

- **Human-in-the-Loop (o "U"):** uma decisão só é real quando um **decisor humano** a ratifica.
  Os agentes rascunham; o operador decide. Isso é governança, não cerimônia.
- **Bloco de metadados:** `Date (UTC)`, `Authors`, `Deciders` — explícitos e auditáveis.
- **Data de gênese imutável + Status history:** a data original nunca muda; cada transição
  (Proposed → Accepted → Amended → …) é **acrescentada** como uma linha datada. A história é
  append-only.
- **Enum de status estendido:** `Proposed`, `Accepted`, `Amended`, `Deprecated`, `Superseded` e
  `Quarantined` (um estado transitório para uma decisão cujo objeto fica entre colchetes até uma
  resolução explícita).
- **Inventário criptográfico:** o [ADR-0056](../adr/ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md)
  faz hash de cada ADR em `docs/adr/INVENTORY.txt` e o atesta com uma assinatura SSH
  (`INVENTORY.txt.sig` + `allowed_signers`). O hash **late** (a CI detecta adulteração); a
  assinatura **morde** (só o dono pode reatestar).

---

## 5. Ciclo de vida em resumo

```text
Proposed ──ratifica──► Accepted ──muda──► Amended (mesma decisão, refinada)
                          │
                          ├──► Deprecated  (não mais recomendado)
                          ├──► Superseded  (substituído por ADR-NNNN)
                          └──► Quarantined (transitório; resolve para um dos acima)
```

`Quarantined` nomeia o "entre estados" com honestidade, em vez de deixar uma decisão fingindo estar
resolvida.

---

## 6. Como escrevemos um ADR aqui

1. **Esqueleto:** `pwsh ./scripts/new-adr.ps1 -Title "..." -Summary "..."` (escolhe o próximo
   `NNNN` automaticamente). Preencha *Contexto / Decisão / Consequências*.
1. **Índice:** adicione a linha em [`docs/adr/README.md`](../adr/README.md).
1. **Inventário:** regenere `docs/adr/INVENTORY.txt` (`inv-adr`) para o hash bater; a CI exige isso.
1. **Humano ratifica:** o operador move `Proposed → Accepted` e o commit é assinado.

> Os próprios primers também são governados: sua taxonomia e seu lar são definidos pelo
> [ADR-0070](../adr/ADR-0070-primer-taxonomy-and-home.md), que emenda o
> [ADR-0058](../adr/ADR-0058-primer-hub-registration-ritual.md).

---

## 7. Leitura adicional

- Michael Nygard, *Documenting Architecture Decisions* (2011) — o post original sobre ADR.
- Projeto **MADR** — o template/convenção Markdown sobre o qual este repositório se apoia.
- [ADR-0045](../adr/ADR-0045-adr-metadata-and-format-standardization.md) — a constituição UMADR.
- [índice de ADRs](../adr/README.md) — todas as decisões aceitas neste repositório.
