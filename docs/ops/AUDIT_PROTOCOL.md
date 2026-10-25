# Protocolo de Auditoria de Integridade

Este documento rege a conformidade entre o código e a promessa técnica do Data Boar.

## Rigor de Tradução (LCM)

As traduções para PT-BR devem seguir o **Linguistic Category Model** de alto impacto:

- **Evitar:** "O script permite você..." (Tradução direta).
- **Adotar:** "O script expõe a funcionalidade...", "A ferramenta assegura o rastro...".

## Gestão de Performance

Qualquer queda na eficiência do `boar_fast_filter` deve disparar um **ADR de Regressão**.

## Ponte PyO3 (integridade de memória)

O repositório mantém testes de propriedade em ``tests/security/test_mem_integrity.py`` (Hypothesis)
contra ``boar_fast_filter.FastFilter``. Quando a extensão Rust estiver instalada no ambiente,
a suíte executa os exemplos; sem a extensão, o pytest marca os casos como skip (mesmo contrato
que ``tests/test_rust_bridge.py``).

**Gate local:** ``scripts/pre-commit-and-tests.ps1`` / ``.sh`` executam esse arquivo **em primeiro lugar**
e depois o resto da suíte com ``--deselect tests/security/test_mem_integrity.py`` (evita correr os
mesmos exemplos Hypothesis duas vezes). O ``check-all`` herda este fluxo.

### Perfil de memory safety (expectativa honesta)

| Risco (estilo C/C++) | Cobertura no Data Boar hoje |
| --- | --- |
| **Integer underflow / overflow** nos contadores FFI | O crate ``boar_fast_filter`` usa **Rust seguro** e APIs estáveis (``Vec<String>``, índices ``usize``). Os testes Hypothesis limitam o tamanho do batch no Python e convertem ``val`` com ``abs`` antes de construir listas — não há API exposta tipo ``set_limit`` bruto. |
| **Out-of-bounds reads** na ponte | O fuzz alimenta **strings grandes** (payload binário → latin-1) e batches com até **200** linhas, exercitando PyO3 + regex no Rust. Não substitui **Miri**, **ASan** nem fuzzing de binário nativo. |
| **Use-after-free** | Não há suite dedicada a UAF; o modelo **ownership** do Rust no motor elimina UAF no mesmo estilo que C manual, desde que o limite PyO3 não introduza ``unsafe`` incorreto (hoje o crate evita ``unsafe`` no caminho exposto). |
| **Buffer overflow** (stack/heap clássico) | O mesmo que acima: **sem ``unsafe``** no caminho típico + testes Rust em ``cargo test`` no **Rust guard** do ``check-all``. O Python **não** valida overflows de buffer nativos além do que o runtime e o PyO3 já impõem. |

## Bandit no CI (gate estrito)

O ``[tool.bandit]`` em ``pyproject.toml`` fixa baseline (**level** / **confidence** MEDIUM,
``recursive``, ``aggregate``) e exclusões; o workflow ``.github/workflows/ci.yml`` executa
``uv run bandit -r . -c pyproject.toml -ll -ii`` no job ``bandit`` (com ``--group dev``). O merge
falha se o scan reportar achados dentro dos filtros do CLI.

## Contrato de Bancada (Adam Savage)

- Ferramenta que não funciona não permanece na bancada.
- Scripts órfãos ou quebrados devem ser removidos ou corrigidos antes de encerrar a tarefa.

## Registro de Ritual e Contrato

Toda alteração de ritual operacional ou contrato de execução deve ser registrada neste arquivo
antes do fechamento da sessão.

## Warning de Integridade (Doutrina NASA)

Quando o Founder solicitar uma ação que viole a doutrina de integridade (por exemplo, pular
testes obrigatórios), o agente deve emitir um **Warning de Integridade** antes de executar.
