# Pós-mortem do sprint: discovery Pro+, pré-filtro Rust, throttling SRE

**English:** [SPRINT_GREAT_LEAP_POSTMORTEM.md](SPRINT_GREAT_LEAP_POSTMORTEM.md)

Esta nota separa **evidência verificada** de **metas aspiracionais de laboratório**. Somente linhas verificadas devem ir para material voltado a cliente.

## Verificado nesta sessão do repositório (com evidência)

Fonte: [LAB_LESSONS_LEARNED.md](LAB_LESSONS_LEARNED.md) (hub; snapshot datado: [lab_lessons_learned/LAB_LESSONS_LEARNED_2026_04_25.md](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_04_25.md)), `tests/benchmarks/official_benchmark_200k.json`, arquivo de checkpoint do teste de kill.

| Tópico | Resultado |
| ------ | --------- |
| Extensão Rust `boar_fast_filter` | Compilada e importável na `.venv` do projeto (PyO3 ajustado para CPython 3.13). |
| Benchmark oficial (200k linhas, 8 workers) | OpenCore `0,252242s`, caminho Pro `0,439419s`, `speedup_vs_opencore = 0,574` (Pro tem **0,574x a velocidade** do OpenCore neste perfil, isto é, ~`1,74x` o tempo de relógio — Pro **mais lento**). |
| Checkpoint + retomada após kill | `last_processed_id` avançou de `104000` até o fim da tabela; segunda execução completou com contagem de achados consistente. |
| Throttling | `BoarThrottler` aumentou concorrência em direção ao máximo configurado durante o scan. |

## Não verificado aqui (não alegar sem run reproduzível no lab)

Os números abaixo são **exemplos de meta** para uma campanha futura em lab-op. **Não** foram registrados como resultados medidos nesta sessão.

| Alegação | Status |
| -------- | ------ |
| 1.000.000 linhas mock end-to-end | Não executado nesta passagem de documentação. |
| OpenCore ~420s vs Pro+ ~28s (~15x) | Não medido; contradiz o artefato atual de benchmark oficial. |
| “100% de redução de falsos positivos” em sequências numéricas aleatórias | Não medido como estudo controlado; Luhn só filtra candidatos que não passam Mod 10. |
| `completao` completo verde na lab-op | Não concluído end-to-end nesta sessão do assistente. |

## Conclusões técnicas (honestas)

- **Checkpointing e throttling** são os ganhos mais sólidos capturados aqui para postura “missão crítica”.
- **Marketing de performance** precisa de perfil de benchmark alinhado à carga real (tamanho de chunk, custo de ML downstream, I/O realista) antes de citar speedups.
- **Direção vs razão (não inverta duas vezes).** O campo `speedup_vs_opencore = 0,574` no JSON e a frase do operador **"0,574x mais lento"** apontam para o **mesmo** resultado (Pro mais lento); a razão guardada é `tempo_OpenCore / tempo_Pro`. O Pro leva cerca de **`1 / 0,574 ≈ 1,74x`** o tempo de relógio do OpenCore neste perfil. O guard de regressão [`tests/test_official_benchmark_200k_evidence.py`](../../tests/test_official_benchmark_200k_evidence.py) trava essa direção e a paridade OpenCore ↔ Pro de achados (`100.000` em cada caminho), para que copy executiva ou manifestos não se descolem do artefato gravado em silêncio.

## Próximos passos de verificação

1. Rodar de novo `tests/benchmarks/run_official_bench.py` em escala após ajuste de chunking e workers; arquivar JSON em `tests/benchmarks/`.
2. Rodar `completao` completo na lab-op e anexar logs em relatórios privados conforme runbook.
3. Se a autodefesa de integridade for requisito de produto, implementar conforme `INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md` com ADR.
