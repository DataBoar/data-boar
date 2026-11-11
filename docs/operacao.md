# Modo de operação

Modo: supervisionado
Desde: 2026-11-11
Decidido por: usuario
Duelo: não
Dev externo: Cursor, eventual — só em tarefa crítica (o PM propõe com justificativa escrita na issue; o operador confirma) ou quando o autor pedir; o padrão é o backend-dev-senior.
Pausa: não

Este arquivo é a fonte do modo do projeto: uma sessão nova do PM lê **este** arquivo no `main`, não a memória. Só o operador muda o modo ("desliga o modo supervisionado") e só ele muda a linha `Dev externo`.

## Regras vigentes

- **Só o operador mescla**: `gh pr merge <n> --merge`, nunca squash (o squash apaga a ordem dos commits que mostra o TDD). O PM e os agentes abrem a PR e entregam o veredito.
- **Push e abertura de PR** seguem a ordem do operador; o PM mostra o escopo antes de empurrar, quando o tema é novo.
- **Uma PR épica por tema**, com `Closes #N` (uma palavra-chave por linha). `Refs` só quando fechar a issue for de fato impossível, com a linha "Why not Closes". Cada PR reroda o pipeline inteiro: agrupar o trabalho de um tema numa PR só.
- **Commits assinados (SSH)**, sem `Co-Authored-By` nem trailer de sessão de ferramenta (os hooks do repo recusam). `scripts/check-all.sh` verde, lido pela linha `CHECK_ALL_EXIT`, antes de qualquer push.
- **Arquivos de gate** (`.github/workflows/**`, `.github/actions/**`, `scripts/gate_*`, `.pre-commit-config.yaml`) só em PR dedicada, por último, e com o selo do operador. O fluxo está na skill `pedir-selo`: ensaio `attest-kombi <PR> -r <worktree> -n`, comando colado na janela `selos:<repo>` do tmux sem Enter, aviso por todos os canais. O PM nunca roda o selo de verdade e **não faz push depois do pedido** (invalida o selo). O check `SSHSIG attestation when gated` só reavalia em abrir, sincronizar, reabrir ou mudar rótulo: depois do selo, um `gh run rerun` do workflow de atestação resolve, sem push.
- **Worktrees fora do `/tmp`** (que é memória): `~/Projects/dev/data-boar-wt-<tema>`. O clone principal é read-only para o PM: `git fetch` e leitura, nunca `reset`, `pull` ou commit.
- **Novas funcionalidades nascem Enterprise** (regra pública do projeto); só descem de tier por decisão do operador, com validação.
- **Honestidade comercial**: evidência, não conclusão jurídica; nenhuma capacidade ou desempenho afirmado sem artefato. Este repositório é público: nenhum parceiro, cliente, preço, plano comercial ou vetor sob embargo entra em issue, PR, documento ou commit.
- **Corrigir o que está errado, não só deixar verde**: sem correção frágil, sem teste flaky, sem relaxar uma verificação para passar.
- **Não tocar** em PRs de outros agentes ou autores.

## Estado do fluxo (2026-11-11)

| Item | Situação |
| --- | --- |
| #2174 (badge do SBOM) | Selada; checks verdes. Falta o merge do operador |
| #2219 (RoPA, SARIF/SIEM e hub multi-instância) | Aberta, CI verde. Merge do operador |
| #2221 (wheel cp314t, diagnóstico e plano do wheelhouse) | Aberta; CI sendo corrigido |
| #2220 (endurecimento do apt nos workflows) | Aberta; PR de gate dedicada, por último |
| #2190, #2191, #2192 (dependabot de workflows) | Aguardam a decisão do operador: selar ou fechar |

## Decisões pendentes do operador

Nenhuma bloqueia o fluxo; o PM segue com o que não depende delas.

| Assunto | Situação |
| --- | --- |
| Alvo do delta de wheels do wheelhouse | Reconstruir para a tag `v1.8.0` ou para o `main`? Recomendação: a tag, pelo conjunto testado; reconstruir para o `main` quando a 1.8.1 for cortada |
| Remoção de worktrees e branches já mesclados e dos stashes | Inventário feito, nada removido. Backup com `git bundle` antes de qualquer remoção |
| Branches antigos sem PR | O operador marca "PR" ou "descartar" |
| Pins do dependabot desde o GA | Cerca de 40 mudaram no `main`; afeta o alvo do wheelhouse |

## Custo

Cada chamada ao modelo relê a sessão inteira: sessões curtas, uma rodada por vez, estado no GitHub e neste arquivo. Sem subagentes grandes; no máximo dois ao mesmo tempo.
