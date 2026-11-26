# Modo de operação

Modo: supervisionado
Desde: 2026-11-11
Decidido por: usuario
Duelo: não
Dev externo: opencode (plano B: pi) — em tudo o que der para ir por harness externo, inclusive a fila do v1.8.1 (ordem do operador de 2026-11-26: "é para ir pelo harness ext como tudo o q der"). Nas tarefas #2264 e #2270, depois do desenho do arquiteto e dos testes do QA. Cursor segue eventual: só em tarefa crítica (o PM propõe com justificativa escrita na issue; o operador confirma) ou quando o autor pedir. Todo patch de dev externo passa, antes do merge, por uma segunda opinião somente leitura de um harness diferente do que escreveu (hoje, em geral, o Hermes).
Harness por papel: todos os papéis (arquiteto, QA, devs, revisor, cyber, documentador e os demais) são agnósticos de harness e podem ir por opencode, Cursor, codex, agy, grok, pi, zero ou outro, à escolha do operador (ordem de 2026-11-26). Só o adversarial está combinado com o Hermes, para dar diversidade, e o operador pode mudar isso também. Quem audita ou revisa segue somente leitura.
Pausa: não

Este arquivo é a fonte do modo do projeto: uma sessão nova do PM lê **este** arquivo no `main`, não a memória. Só o operador muda o modo ("desliga o modo supervisionado") e só ele muda a linha `Dev externo`.

## Regras vigentes

- **Só o operador mescla**: `gh pr merge <n> --merge`, nunca squash (o squash apaga a ordem dos commits que mostra o TDD). O PM e os agentes abrem a PR e entregam o veredito.
- **Push e abertura de PR** seguem a ordem do operador; o PM mostra o escopo antes de empurrar, quando o tema é novo.
- **Uma PR épica por tema**, com `Closes #N` (uma palavra-chave por linha). `Refs` só quando fechar a issue for de fato impossível, com a linha "Why not Closes". Cada PR reroda o pipeline inteiro: agrupar o trabalho de um tema numa PR só.
- **Commits assinados (SSH)**, sem `Co-Authored-By` nem trailer de sessão de ferramenta (os hooks do repo recusam). `scripts/check-all.sh` verde, lido pela linha `CHECK_ALL_EXIT`, antes de qualquer push.
- **Arquivos de gate** (`.github/workflows/**`, `.github/actions/**`, `scripts/gate_*`, `.pre-commit-config.yaml`) só em PR dedicada, por último, e com o selo do operador. O fluxo está na skill `pedir-selo`: ensaio `attest-kombi <PR> -n` com o clone canônico limpo no branch da PR, comando colado na janela `selos:<repo>` do tmux sem Enter, aviso por todos os canais. O PM nunca roda o selo de verdade e **não faz push depois do pedido** (invalida o selo). O check `SSHSIG attestation when gated` só reavalia em abrir, sincronizar, reabrir ou mudar rótulo: depois do selo, um `gh run rerun` do workflow de atestação resolve, sem push.
- **NUNCA worktree, e nunca cópia ou clone do repositório** (ordem do operador, 19 e 24/nov/2026), em nenhuma pasta. Vale para o PM, subagentes, revisores e devs externos, inclusive o `--worktree`/`-w` de qualquer harness, e vence qualquer skill ou documento que mande o contrário. O trabalho é feito num **branch** no clone canônico (`git switch -c <branch>`); para trocar de branch, a árvore fica limpa antes (commit no branch). Um agente por branch. Antes de trocar o branch, confira que nenhum outro agente está usando o clone.
- **Consolidar e agregar**: antes de criar arquivo, branch ou PR, procurar o que já existe e estender. `/tmp` é memória: só temporário pequeno, apagado por quem criou.
- **Escrita no clone**: o PM tem escrita por ordem do operador (19/nov/2026), sob todas as regras deste arquivo. Nunca `reset --hard` nem descarte de trabalho alheio.
- **Novas funcionalidades nascem Enterprise** (regra pública do projeto); só descem de tier por decisão do operador, com validação.
- **Honestidade comercial**: evidência, não conclusão jurídica; nenhuma capacidade ou desempenho afirmado sem artefato. Este repositório é público: nenhum parceiro, cliente, preço, plano comercial ou vetor sob embargo entra em issue, PR, documento ou commit.
- **Corrigir o que está errado, não só deixar verde**: sem correção frágil, sem teste flaky, sem relaxar uma verificação para passar.
- **Não tocar** em PRs de outros agentes ou autores.

## Documentos: quem responde o quê

| Documento | Responde |
| --- | --- |
| `docs/plans/PLANS_TODO.md` (com `PLANS_HUB.md` e `PLAN_*.md`) | Estratégia, situação dos planos e sequência oficial do backlog (inglês) |
| `docs/plano.md` | Tático e operacional: o que vem agora na versão corrente, em que ordem e com quem |
| `docs/operacao.md` (este) | Como agir: modo, pausa, autorizações e regras; sem estado de tarefas |
| `AGENTS.md` e `.cursor/rules/` | Contrato dos agentes, palavras de sessão e guardrails |
| GitHub | Estado vivo de issues, PRs e CI; vence os documentos |

## Skills por momento

| Momento | Skill |
| --- | --- |
| Abrir sessão, liberar tarefa, fechar rodada | `coordenar-fluxo` |
| Plano, visão e perguntas ao cliente | `planejar` |
| Dev externo | `operar-dev-externo` e `operar-opencode` |
| Segunda opinião somente leitura | `operar-hermes` |
| Revisão de código e de segurança | `revisar-pr`, `revisar-seguranca` |
| Selo de arquivos de gate | `pedir-selo` |
| Auditoria e acompanhamento | `auditar-projeto`, `acompanhar-projeto` |
| Registro das passagens | `registrar-evento` |

## Custo

Cada chamada ao modelo relê a sessão inteira: sessões curtas, uma rodada por vez, estado no GitHub e neste arquivo. Sem subagentes grandes; no máximo dois ao mesmo tempo.
