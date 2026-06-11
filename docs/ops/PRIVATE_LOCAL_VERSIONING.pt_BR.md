# Versionamento local de `docs/private/` (nunca no GitHub)

**English:** [PRIVATE_LOCAL_VERSIONING.md](PRIVATE_LOCAL_VERSIONING.md)

**Objetivo:** Ter **histórico de revisões** da árvore privada (gitignored)—notas, estimativas, rascunhos de financiamento, “diário de ideias”) **sem** acoplar isso ao repositório **público** do Data Boar nem ao GitHub do produto.

---

## 1. Dá para fazer?

**Sim.** O repositório principal coloca **`docs/private/`** no **`.gitignore`**, então:

- Nada dali entra no commit quando você trabalha no repo do produto.
- Um diretório **`.git` aninhado** dentro de **`docs/private/`** também fica fora do Git pai (mesma regra de ignore). Vira um **repositório Git separado**, com histórico **local** (ou no **seu** remoto de backup), não no `origin` deste projeto.

No Cursor você continua com **um workspace** só: **`data-boar/`** (clone de **FabioLeitao/data-boar**) com **`docs/private/`** dentro—são **dois** históricos Git **só se** você fizer `git init` na pasta privada.

---

## 2. Padrão recomendado: Git aninhado em `docs/private/`

Na raiz do repo (com **`docs/private/`** já existente):

```bash
cd docs/private
git init
git branch -M main
git add .
git commit -m "chore: bootstrap private notes repo"
```

## Remotos (escolha um):

| Opção                          | Quando usar                                                                                                           |
| -----                          | -----------                                                                                                           |
| **Sem remote**                 | Histórico só neste disco; backup = cópia/USB/restic.                                                                  |
| **Repositório bare `file://`** | Outra pasta no disco ou NAS, ex.: `git remote add backup file:///caminho/private-notes.git` e `git push backup main`. |
| **SSH próprio**                | Servidor seu—não GitHub—se quiser histórico fora do PC sem publicar estratégia ligada ao produto.                     |

**Não** configure remote no GitHub (ou público) para essa árvore a menos que você **queira de propósito** esse conteúdo na internet.

---

## 3. Outras ferramentas (Mercurial, Bazaar)

**Dá** (ex.: `hg init` em `docs/private/`), mas você soma **outra** ferramenta e carga mental. Para a maioria, **só Git** basta e alinha com tutoriais de backup. Use **Hg/Bzr** só se você já depende delas em outro lugar.

---

## 4. “Pasta separada que parece junto”

Alternativas:

- **Diretório irmão** (ex. `~/private-data-boar-notes`) com Git próprio e atalhos/sync para `docs/private/`—mais partes móveis.
- **Junção de pasta / symlink** no Windows—funciona em alguns cenários; **quebra** se caminhos ou sync discordarem. Prefira **Git aninhado** em **`docs/private/`** salvo motivo forte.

---

## 5. Backups (ainda locais ou sob seu controle)

- **Disco externo cifrado** ou **restic**/similar para destino que **você** controla.
- **`git bundle create`** para snapshots em um arquivo só, se quiser.
- Se usar **pCloud / `P:`**, trate como **praticidade**, não cofre de segredos; cifragem em repouso é decisão sua.

---

## 6. O que guardar para motivação, financiamento e estimativas

Números, comparativos e narrativa que seriam **estranhos** no GitHub ficam em **`docs/private/operator_economics/`** (e **`commercial/`** quando for lado cliente). Nomes sugeridos (crie localmente; ver **[private.example/economics/README.md](../private.example/economics/README.md)**):

- **Esforço por fase (demo / beta / production):** faixas grosseiras, premissas, quem poderia ajudar—útil para **você** e para **contexto do assistente** em planejamento.
- **Financiamento / orçamento / comparativo de compra:** opções, links, “por que este fornecedor”—continua **privado** se expõe *runway* ou estratégia.
- **Diário P&R / ideias:** entradas datadas (perguntas, respostas, desdobramentos)—tipo **blog privado**; pode linkar no **`author_info/RECENT_OPERATOR_SYNC_INDEX.pt_BR.md`**.

Planos **rastreados** do produto continuam em **`docs/plans/`**; use arquivos privados para números **sensíveis** ou **preliminares** e **promova** só o que for seguro para os planos quando fizer sentido.

---

## 7. Lembretes de segurança

- **`tests/test_confidential_commercial_guard.py`** continua valendo: nunca **`git add -f docs/private/...`** no repo **principal**.
- **Assistentes** podem **`read_file`** Markdown privado quando você pede ajuda de planejamento—mesmo assim **não** colar essas tabelas em arquivos **rastreados** nem em issues.

---

## 8. Documentação relacionada

- [PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md) — layout de `docs/private/`.
- [PRIVATE_STACK_SYNC_RITUAL.pt_BR.md](PRIVATE_STACK_SYNC_RITUAL.pt_BR.md) — **stub** da palavra-chave **`private-stack-sync`** (fecho do Git empilhado em `docs/private/`; sem segredos).
- [OPERATOR_SESSION_CAPTURE_GUIDE.pt_BR.md](OPERATOR_SESSION_CAPTURE_GUIDE.pt_BR.md) — chat → notas duráveis.
- [private.example/README.md](../private.example/README.md) — bootstrap copiável.
