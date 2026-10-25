# GitHub issues: item canônico versus encerramento de duplicata (eco)

**English:** [GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.md](GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.md)

**Objetivo:** Quando várias issues descrevem o mesmo recorte (duplicatas acidentais, ecos sem querer, ou auditorias que abrem tickets sobrepostos), manter **uma issue canônica** para rastreamento, entregar **PRs finos** que a referenciem e **fechar duplicatas somente depois** do merge e do CI verde — com **evidência** na thread da duplicata.

**Alinhamento:** [COMMIT_AND_PR.pt_BR.md](COMMIT_AND_PR.pt_BR.md), [CONTRIBUTING.md](../../CONTRIBUTING.md), [PLANS_TODO.md](../plans/PLANS_TODO.md) (nota de varredura de issues), **`.cursor/rules/git-pr-sync-before-advice.mdc`**, **`.cursor/rules/execution-priority-and-pr-batching.mdc`**, **`.cursor/rules/agent-autonomous-merge-and-lab-ops.mdc`**.

## 1. Escolher a issue canônica

- Preferir a issue que melhor casa com o **escopo** e o **menor número** quando dois títulos forem o mesmo trabalho — salvo se a issue mais nova **substitui** o escopo (aí tratar a análise mais nova como canônica e fechar a antiga como duplicata ou não planejada, com justificativa).
- Registrar a decisão em **`PLANS_TODO.md`** apenas quando afetar ordenação (uma linha basta); não colar narrativas longas em planos rastreados.

## 2. Trabalho e PR

- Branch + commits: **um agrupamento por assunto por commit** quando possível; referenciar a issue **canônica** no título ou corpo do PR (`Closes #NNN` / `Fixes #NNN` para o `NNN` canônico).
- Rodar **`check-all`** (ou **`lint-only`** para **só** documentação) antes do push; ver **COMMIT_AND_PR.pt_BR.md**.

## 3. Critério antes de fechar qualquer coisa

**Não** fechar issues só com base em *done* local.

1. **`git push`** e PR **aberta** (ou atualizada).
2. **`gh pr checks <PR>`** verde **e** branch protection atendida (mesma intenção que **`pr-merge-when-green.ps1`**).
3. **Merge** em `main` quando apropriado (humano ou merge scriptado conforme regras do projeto).

## 4. Fechar a issue canônica

- Se o corpo do PR usou **`Closes #NNN`**, o GitHub pode já ter fechado **`NNN`** no merge — conferir com **`gh issue view NNN`**.
- Se seguiu aberta: **`gh issue close NNN -r completed -c "Shipped in https://github.com/OWNER/REPO/pull/PRNO (merge …)."`** (ajustar URL e SHA do commit se útil).

## 5. Fechar duplicata / eco (depois de confirmar que é igual)

Somente após o passo **3** (merge + checks verdes no PR que integra):

1. Confirmar que a duplicata é o **mesmo recorte** que a canônica (título + corpo); se não for, **não** usar fechamento como duplicata — tratar à parte.
2. Fechar com o vínculo **`duplicate`** do GitHub e um **comentário de evidência** (URL do PR; SHA opcional):

   ```bash
   gh issue close DUPLICATE --duplicate-of CANONICAL \
     --comment "Resolved via https://github.com/OWNER/REPO/pull/PRNO — mesmo escopo que #CANONICAL."
   ```

   O **`gh`** aplica **`--duplicate-of`** ao relacionamento de duplicata; o **`--comment`** deixa rastro público auditável.

3. Se **não** estiver satisfeito de que é o mesmo: fechar como **`not planned`** ou deixar aberta com comentário — **não** marcar **`duplicate-of`** de forma incorreta.

## 6. O que evitar

- Não fechar issues em massa sem **merge do PR + CI verde** para a correção que vale para o item canônico.
- Não colocar segredos, hostnames privados ou PII não relacionado em comentários de encerramento — **link do PR + referência cruzada de issue** basta.

## 7. Referência rápida (copiar e colar)

Substituir `OWNER`, `REPO`, números e URLs:

```bash
gh pr checks <PR-NUMBER>
# após o merge
gh issue view <CANONICAL>
gh issue close <DUPLICATE> --duplicate-of <CANONICAL> --comment "Resolved via https://github.com/OWNER/REPO/pull/<PR-NUMBER> — mesmo escopo que #<CANONICAL>."
```
