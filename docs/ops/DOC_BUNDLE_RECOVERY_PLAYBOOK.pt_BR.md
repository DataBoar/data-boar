# Playbook de recuperação de pacotes de documentação (depois de um `cat` / cópia manual)

**English:** [DOC_BUNDLE_RECOVERY_PLAYBOOK.md](DOC_BUNDLE_RECOVERY_PLAYBOOK.md)

**Âmbito:** Concatenaste, moveste ou duplicaste Markdown/YAML por engano (Explorador, `cat`, etc.) e queres **confirmar que nada rastreado se perdeu** e **voltar a um fluxo seguro**. Texto **procedural** para operador / maintainer — não é documentação do usuário do produto.

**Não substitui** os gates normais de entrega (**`.\scripts\check-all.ps1`**, pre-commit, pytest completo). Usa este playbook **após** incidentes com **árvore local** ou **bundles ad hoc**, não para a qualidade habitual de PR.

---

## Base sem culpa

1. **Git continua a fonte da verdade** para tudo o que está **rastreado**. Compara com `origin/main` (ou a tag de release).
1. **Heurísticas** (divisão por H1, janelas deslizantes, prefixos) **reduzem incerteza** e apontam suspeitos; **não provam** perda nem integridade absoluta.
1. **Prevenção:** pacotes para LLM só via **`scripts/export_public_gemini_bundle.py`** (com **`--verify`**), não com globs soltos no shell — ver **[GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md](GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md)**.

---

## Ordem de recuperação (sequência sugerida)

| Passo | Objetivo                                                   | Comando / ação                                                                                                                                                                                                                                         |
| ----- | --------                                                   | ---------------                                                                                                                                                                                                                                        |
| 1     | Parar o dano                                               | Não gravar em massa sobre arquivos rastreados. Copiar blobs suspeitos só para **`docs/private/...`** (gitignored).                                                                                                                                     |
| 2     | Sincronizar refs                                           | `git fetch origin` e comparar: `git status -sb`, `git diff --name-only origin/main`.                                                                                                                                                                   |
| 3     | Restaurar caminhos rastreados                              | Por caminho: `git restore caminho` ou `git restore --source=origin/main -- caminho`. Exemplo para árvore: `git restore --source=origin/main -- docs/` (**cuidado:** descarta alterações **locais** nesse caminho).                                     |
| 4     | Gerar de novo um bundle **bom** (opcional)                 | `uv run python scripts/export_public_gemini_bundle.py --output docs/private/gemini_bundles/recovery_$(date -I).txt --compliance-yaml --verify`                                                                                                         |
| 5     | Forense no **teu** blob                                    | Se guardaste um concatenado, corre o **script meta** abaixo ou as ferramentas Python (passos 6–7).                                                                                                                                                     |
| 6     | Divisão fiél ao byte (melhor com **ordem exata** de `cat`) | `uv run python scripts/audit_concatenated_markdown.py -i blob.md --cat-order order.txt` — gera **`order.txt`** com `--emit-order-glob` (ver `--help` e doc GEMINI).                                                                                    |
| 7     | Sem headers / ordem desconhecida                           | **Janela deslizante:** `uv run python scripts/audit_concat_sliding_window.py -i blob.md --window 25` e **`--strip-bundle-markers`** se existirem linhas `--- FILE: ... ---`. **H1:** `uv run python scripts/audit_concatenated_markdown.py -i blob.md` |

**PowerShell (passo 4):** o trecho `$(date -I)` é só para **bash**. No Windows use `--output "docs/private/gemini_bundles/recovery_$(Get-Date -Format 'yyyy-MM-dd').txt"` — ver **[GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md](GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md)**.

---

## Script meta (Windows, um comando)

Na raiz do repositório:

```powershell
# Só sanidade das ferramentas (pytest de compilação dos três scripts Python)
.\scripts\recovery-doc-bundle-sanity.ps1

# Passagem forense completa num blob guardado (ajusta o caminho)
.\scripts\recovery-doc-bundle-sanity.ps1 -BundlePath "docs\private\mess_concatenated_gemini_sanity_check\sobre-data-boar.md" -Headerless -SlidingWindow 25

# Incluir auditoria H1 por chunks (saída longa no terminal)
.\scripts\recovery-doc-bundle-sanity.ps1 -BundlePath "docs\private\...\blob.md" -IncludeH1Audit
```

**Parâmetros:** **`Get-Help .\scripts\recovery-doc-bundle-sanity.ps1`**. Habitual: **`-BundlePath`**, **`-Headerless`** (equivale a **`--strip-bundle-markers`** na etapa de janelas), **`-SlidingWindow`**, **`-SkipPytest`**, **`-IncludeH1Audit`**, **`-DryRun`**.

---

## Várias passagens com `--sweep-windows` (ruído vs sinal)

**Janelas menores** costumam **aumentar** a percentagem coberta (menos blocos de gap). **Janelas maiores** são mais exigentes e podem “partir” a cobertura nos limites entre arquivos. Corre **duas** tabelas quando tiveres dúvida: sem e com **`--rstrip-lines`**. Se forem **iguais**, espaços no fim da linha não eram o problema; se `rstrip` **encolher** os gaps, havia só deriva de whitespace.

```bash
uv run python scripts/audit_concat_sliding_window.py -i docs/private/.../blob.md \
  --strip-bundle-markers --sweep-windows 12,15,18,22,25,30
uv run python scripts/audit_concat_sliding_window.py -i docs/private/.../blob.md \
  --strip-bundle-markers --rstrip-lines --sweep-windows 12,15,18,22,25,30
```

**Heurística:** intervalos de gap que **persistem** em vários tamanhos de janela merecem revisão manual com mais prioridade do que picos que só aparecem numa janela grande (muitas vezes ruído de fronteira). Cerca de **cinco** tamanhos entre **12 e 30** costumam bastar antes de ganhos marginais.

---

## Balde “final round” (“boss level”) — vestígios restaurados a mais

Quando aparecem **mais** cópias recuperadas depois (“undelete”, Explorador, backup), **não** as espalhes: coloca-as em **`docs/private/mess_concatenated_gemini_sanity_check/final_round_bucket/`** (gitignored, mesmo ramo que a primeira pasta sanity). Há um **`README.md`** local nessa pasta com os mesmos comandos.

**Fluxo:** copiar o(s) blob(s) para lá → correr **`--sweep-windows`** (e opcionalmente **`recovery-doc-bundle-sanity.ps1`**) **por arquivo** novo → comparar tabelas de gaps com o blob da primeira passagem se ajudar. **Git + `main`** mandam; esta pasta é só **confiança / arqueologia**.

**Trava ao perfeccionismo:** se `git status` está limpo face a `origin/main`, a primeira passagem já mostrou **~99%+** cobertura, e o blob novo **não** reclama substituir conteúdo rastreado, **declara vitória** e segue em frente.

### Concat + mapa de nomes (muitos arquivos soltos)

Quando o balde é um monte de `.md` / `.yaml` / `.htm` / `.html` vindos do browser ou restore, usa **`scripts/build_final_round_bucket_concat.py`**: gera um único blob com marcadores `--- FILE: … ---`, opcionalmente mostra **alinhamento por nome de arquivo** com a árvore rastreada (sem `docs/private/`), e pode disparar o **sweep** de janelas num comando.

```bash
# Pistas de nome: homónimo exato, stem normalizado (ex.: "Arquivo (1).htm"), ou sem par rastreado
uv run python scripts/build_final_round_bucket_concat.py --map-names

# Gravar concat por omissão em .../final_round_bucket/_concat_for_sliding_window.md
uv run python scripts/build_final_round_bucket_concat.py

# Gerar + tabela compacta de sweep (12–30, como na seção multi-passagem)
uv run python scripts/build_final_round_bucket_concat.py --sweep --quiet-gaps

# Com normalização de whitespace à direita em corpus + entrada
uv run python scripts/build_final_round_bucket_concat.py --sweep --quiet-gaps --rstrip-lines
```

Opções: **`--bucket`**, **`--output`**, **`--repo-root`**, **`--sweep-windows`**, **`--dry-run`**. HTML é convertido para linhas aproximadas (tags removidas) — não é fiel byte a byte ao Markdown.

---

## Como ler os resultados

- **“% coberto”** da janela deslizante perto de **100%** num blob que deveria espelhar o **`main` atual**: bom sinal de alinhamento; lacunas pequenas costumam ser **limites entre arquivos**, **deriva** desde o snapshot ou **cola** — rever os trechos impressos, não só a percentagem.
- **H1 sem match exato:** ainda pode recuperar-se via Git ou **dica de prefixo**; o chunk pode ser **edição antiga** ou texto que não é doc.
- Se **`export_public_gemini_bundle.py --verify`** falhar: a árvore **divergiu** do que foi escrito no bundle — regerar ou corrigir arquivos antes de confiar no pacote.

---

## Lições aprendidas (resumo)

- Preferir export com **`git ls-files`** e **`--verify`** em vez de **`cat *.md`** para anexos a LLM.
- Manter **uma** cópia “sanity” sob **`docs/private/`**; não colocar caminhos de LAN nem segredos em docs **rastreados**.
- Depois do incidente, correr **`recovery-doc-bundle-sanity.ps1`** ou os scripts individuais para **registar confiança** (estilo SRE), sem tratar heurísticas como prova criptográfica.

---

## Ligações relacionadas

- **[GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md](GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md)** — geração segura do pacote, prompts, lista de ferramentas.
- **`scripts/audit_concatenated_markdown.py`**, **`scripts/audit_concat_sliding_window.py`**, **`scripts/export_public_gemini_bundle.py`**, **`scripts/build_final_round_bucket_concat.py`** — flags e comportamento.
- **[COMMIT_AND_PR.pt_BR.md](COMMIT_AND_PR.pt_BR.md)** — hábito normal depois da árvore limpa.
