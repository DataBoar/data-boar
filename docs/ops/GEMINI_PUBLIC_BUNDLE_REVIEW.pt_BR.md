# Pacote para revisão por LLM externa (Gemini) — fluxo seguro

**English:** [GEMINI_PUBLIC_BUNDLE_REVIEW.md](GEMINI_PUBLIC_BUNDLE_REVIEW.md)

**Depois de um incidente com `cat`:** passos de recuperação e o script meta Windows `**scripts/recovery-doc-bundle-sanity.ps1`** — **[DOC_BUNDLE_RECOVERY_PLAYBOOK.pt_BR.md](DOC_BUNDLE_RECOVERY_PLAYBOOK.pt_BR.md)** ([EN](DOC_BUNDLE_RECOVERY_PLAYBOOK.md)).

## Autoridade (Gemini vs Git + testes)

Revisão por LLM externa (ex.: Gemini sobre a saída do `**export_public_gemini_bundle.py`**) é **triagem em lote opcional** — não um relatório de auditoria isolado nem substituto de **histórico `git`**, **CI** ou **pytest**. Trate como outros **insumos externos** (ex.: digests estilo Corporate-Entity-C / WRB): úteis para **priorizar**, sempre abaixo de checagens reproduzíveis. No repositório: `**--verify`** na exportação do pacote, helpers `**audit_concat_***` quando usar, `**recovery-doc-bundle-sanity.ps1**` e o **playbook de recuperação** quando o pacote correr mal.

**Depois de cada execução:** registre sugestões em **[plans/PLAN_GEMINI_FEEDBACK_TRIAGE.md](../plans/PLAN_GEMINI_FEEDBACK_TRIAGE.md)** (to-dos opcionais, não autoritativos) antes de promover qualquer coisa para **[PLANS_TODO.md](../plans/PLANS_TODO.md)** ou uma issue.

Este runbook evita erros do tipo `**cat *.md` manual**: o pacote vem só de `**git ls-files`**, **exclui** `**docs/private/`** e envolve cada arquivo assim:

```text
--- FILE: caminho/relativo/ao/repo ---
<conteúdo exato do arquivo>

```

## Gerar o pacote (recomendado)

Na raiz do repositório:

```bash
uv run python scripts/export_public_gemini_bundle.py \
  --output docs/private/gemini_bundles/public_bundle_$(date -I).txt \
  --compliance-yaml \
  --verify

```

**Windows (PowerShell):** não cole o bloco acima — `$(date -I)` é **bash**; no PowerShell o comando falha ou gera caminho errado (ex.: `**public_bundle_.txt`**). Use data explícita:

```powershell
uv run python scripts/export_public_gemini_bundle.py `

  --output "docs/private/gemini_bundles/public_bundle_$(Get-Date -Format 'yyyy-MM-dd').txt" `

  --compliance-yaml `

  --verify

```

(Dentro de **aspas duplas**, `$(Get-Date -Format 'yyyy-MM-dd')` expande para a data ISO.)

Atalho em Linux/macOS:

```bash
./scripts/export_public_gemini_bundle.sh -o /tmp/public_bundle.txt --compliance-yaml --verify

```

**Destino:** guarde o arquivo sob `**docs/private/...`** (gitignored) para não correr risco de commit.

## Prompt sugerido para o Gemini (copiar/colar)

**Quatro frentes numa só:** antes costumávamos pedir em separado (EN + infra, pt-BR, YAML de compliance, raciocínio profundo)—ver **[PLAN_GEMINI_FEEDBACK_TRIAGE.md](../plans/PLAN_GEMINI_FEEDBACK_TRIAGE.md)** §6. Um anexo, uma resposta.

Anexe **só** o pacote; não misture notas privadas. Mantenha o **texto do prompt curto**; o orçamento do modelo deve ir para os arquivos.

### Erro **13**, `RESOURCE_EXHAUSTED`, ou timeouts (móvel / API sobrecarregada)

- **Encurte o prompt:** use o bloco **compacto** abaixo.
- **Reduza o pacote:** `uv run python scripts/export_public_gemini_bundle.py --dry-run` (contagem); depois `**--no-workflows`** ou menos flags — ver [Flags](#gerar-o-pacote-recomendado).
- **Limite a saída:** peça no máximo N achados por seção (variante compacta).
- Tente de novo **fora de horas de pico**; anexos grandes + respostas longas estouram quota/contexto.

### Prompt completo (predefinição)

**Linha de papel:** usamos **uma frase** (revisor técnico + domínio) em vez de um parágrafo longo “és um especialista…”. Para este uso, **âmbito + formato de saída + FILE:** costumam valer mais que um título pomposo. Se quiser zero “roleplay”, apaga a primeira frase e mantém só “Você revisa…”.

```text
Você é revisor de documentação técnica de um produto open source sensível a segurança e conformidade (Data Boar — detecção de sensibilidade estilo LGPD). Revise apenas o anexo; cada arquivo vem assim:
--- FILE: <caminho> ---
<corpo>

O anexo é a única base de evidência. Não assuma outros arquivos. Não invente comportamento — na dúvida: “confirmar no código/testes”. Código e testes implementados prevalecem sobre a documentação quando divergirem.

Cubra estas quatro frentes numa única resposta (nesta ordem):
(A) EN + workflows + onboarding: contradições, postura de segurança, footguns de CI/Docker, promessas incoerentes com um deploy típico.
(B) Pares pt-BR (*.pt_BR.md): tom pouco natural ou com traços de pt-PT, desalinhamento EN↔pt no sentido técnico (não tradução literária).
(C) docs/compliance-samples/*.yaml: footguns de padrões/overrides, risco de falsos positivos, manutenção — não parecer jurídico.
(D) Transversal: principais riscos “profundos” (confusão do operador, buraco de overrides, inundação de FP numéricos) e perguntas em aberto.

Severidade: P0 (bloqueia ou engana em segurança), P1 (corrigir em breve), P2 (melhoria). Opcional: urgência Hot / Warm / Cold (Hot = verificar em dias se for verdade).

Saída (use exatamente estes títulos; cada bullet preferencialmente uma linha + FILE:caminho):
## Resumo executivo (máx. 7 bullets)
## (A) EN + infra + CI
## (B) Locale pt-BR
## (C) Amostras YAML de compliance
## (D) Transversal / perguntas em aberto
## P0
## P1
## P2

```

### Prompt compacto (API sobrecarregada ou pacote enorme)

```text
Mesmo formato de anexo (--- FILE: ---). Data Boar = scanner estilo LGPD; só triagem.

Numa única resposta, no máximo **8** achados no total, cada um: `- [P0|P1|P2] FILE:caminho — uma frase`.

Secções (muito curtas):
## Resumo (3 bullets)
## Achados (máx. 8, com FILE:)
## Perguntas em aberto (máx. 3)

Sem prosa longa. Não repetir o conteúdo dos arquivos.

```

## Automação relacionada

- Pacotes antigos sem marcadores: `scripts/audit_concatenated_markdown.py` (divisão por H1 ou `--cat-order` por bytes).
- **Heurística de “peças do puzzle” (janela deslizante):** `scripts/audit_concat_sliding_window.py` indexa **todas** as janelas de *N* linhas nos `*.md` / `*.yaml` / `*.yml` rastreados e marca quais linhas do **blob concatenado** (bundle de export) coincidem com **alguma** janela do repositório. Trechos **sem cobertura** podem ser cola entre arquivos, edição manual ou texto que **já não existe** no disco — **não** provam perda (linhas genéricas e limites de janela geram ruído). Exemplo:

  ```bash
  uv run python scripts/audit_concat_sliding_window.py \
    -i docs/private/mess_concatenated_gemini_sanity_check/sobre-data-boar.md \
    --window 25 --strip-bundle-markers --show-sample-matches 15

  ```

  Opcional: `--rstrip-lines` se houver diferença só de espaços no fim da linha; `--include-private-corpus` só se quiser incluir `docs/private/**` no corpus. `--fail-if-uncovered-pct-above 0` sai com código ≠ 0 se restar **alguma** linha sem cobertura (gate rígido; em blobs reais costuma ser barulhento demais).
  **Várias janelas:** `--sweep-windows 12,15,18,22,25,30` imprime uma tabela comparativa (repetir com `--rstrip-lines` para comparar barreiras de whitespace). Ver **[DOC_BUNDLE_RECOVERY_PLAYBOOK.pt_BR.md](DOC_BUNDLE_RECOVERY_PLAYBOOK.pt_BR.md)** § Várias passagens.
- Política de notificação: [OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md](OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md).

