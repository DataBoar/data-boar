# Fatos canônicos do produto (anti-invenção)

**English:** [CANONICAL_PRODUCT_FACTS.md](CANONICAL_PRODUCT_FACTS.md)

Fonte da verdade enxuta para humanos e agentes de código. Prefira **links** a repetir guias longos. Não é texto de marketing.

**Relacionado:** [QUICKSTART.pt_BR.md](../QUICKSTART.pt_BR.md) · [USAGE.pt_BR.md](USAGE.pt_BR.md) · site [windows.html](https://databoar.com.br/windows.html) · issue [#1470](https://github.com/DataBoar/data-boar/issues/1470) · guard `tests/test_canonical_product_facts.py`

---

## 1. Identidade oficial

| Item | Valor canônico |
| ---- | -------------- |
| Nome do produto | Data Boar |
| CLI / executável | `data-boar` |
| Pacote PyPI | `data-boar` |
| **Repositório GitHub** | [https://github.com/DataBoar/data-boar](https://github.com/DataBoar/data-boar) |
| Site institucional | [https://databoar.com.br](https://databoar.com.br) (também [data-boar.com](https://data-boar.com)) |
| Página Windows non-tech | [https://databoar.com.br/windows.html](https://databoar.com.br/windows.html) |
| **Imagem Docker Hub** (só caminho opcional) | [`fabioleitao/data_boar`](https://hub.docker.com/r/fabioleitao/data_boar) — **namespace da imagem ≠ org do GitHub** |

**Não é canônico como repositório GitHub:** o caminho legado no namespace pessoal que ainda redireciona (org + slug acima é a casa atual). Não cite o path pessoal antigo como atual.

---

## 2. Happy-path — Windows / non-tech

1. Prefira o guia do site: [windows.html](https://databoar.com.br/windows.html).
2. Instalação nativa (até existir MSI/winget do produto): `pipx install data-boar`.
3. Execute: `data-boar`.
4. Primeiro contato seguro (demo sintética, sem dados reais): `data-boar --demo`.
5. **Docker é opcional** — caminho avançado / TI. **Não é obrigatório** no caminho nativo Windows. Não apresente Docker como único caminho ou padrão para quem não é de TI.
6. Aprofunde no repo depois do demo: [QUICKSTART.pt_BR.md](../QUICKSTART.pt_BR.md) → [USAGE.pt_BR.md](USAGE.pt_BR.md). Narrativa de negócio fica no **site**; este repo fica no **como rodar**.

**macOS:** `brew tap DataBoar/databoar && brew install data-boar` (tap próprio, Python do Homebrew + pip; não são os pacotes Linux com CPython embarcado). Detalhes: [ops/HOMEBREW_TAP.pt_BR.md](ops/HOMEBREW_TAP.pt_BR.md).

---

## 3. Contrato do produto (doutrina)

- **Deterministic-first / zero-LLM-default** no caminho central de detecção.
- **Local-first** — varredura na máquina do operador; sem mandato de nuvem.
- **HITL** para merge, publish e decisões de alto blast radius.
- **Evidência ≠ conclusão jurídica** — saídas são sinais técnicos para triagem, não certificação nem parecer legal.
- **Overclaim-safe** — sem cobertura universal; sem “certificamos LGPD/conformidade”.
- **Site = negócio**; **repo = técnico**. Link; não duplique páginas longas de marketing aqui.

---

## 4. Fatos de capacidade frequentemente alucinados

| Afirmação inventada ou stale | Fato |
| ---------------------------- | ---- |
| Chave de config `pastas_para_varrer` | **Não existe** (fabricada). Chave YAML real dos alvos: **`targets:`**. |
| CLI `databoarscan --path` | **Não existe**. Use **`data-boar`**. |
| Docker obrigatório / único caminho non-tech | **Falso**. Docker é **opcional**. |
| Arquivos cifrados / protegidos por senha são pulados em silêncio | **Falso**. Via [#828](https://github.com/DataBoar/data-boar/issues/828) gravam **`scan_failures`** com razões `encrypted_no_password` / `wrong_password` — **reportados, não dropados**. Fonte: `core/archives.py` (`iter_archive_members`, `classify_zip_member_read_failure`). |
| Casa GitHub atual é o path legado no namespace pessoal | **Stale**. Canônico: **`DataBoar/data-boar`**. |

---

## 5. Para agentes — não invente

1. Leia **este arquivo** antes de afirmar instalação, CLI, chaves de config ou URLs de identidade.
2. Prefira links para [windows.html](https://databoar.com.br/windows.html), [QUICKSTART.pt_BR.md](../QUICKSTART.pt_BR.md) e [USAGE.pt_BR.md](USAGE.pt_BR.md) a nomes inventados de YAML ou CLI.
3. Nunca invente certificações, resultados jurídicos ou cobertura “universal” de descoberta.
4. Se não souber → diga **desconhecido**; não preencha lacunas com ficção plausível.
5. Mantenha **`fabioleitao/data_boar`** rotulado como **imagem Docker Hub**, nunca como repositório GitHub.

---

## 6. Guard de regressão leve

Pytest offline: `tests/test_canonical_product_facts.py` (esta fatia ancora o guard **nestes arquivos FACTS**). Polícia ampla de README/QUICKSTART é fatia **posterior** em [#1470](https://github.com/DataBoar/data-boar/issues/1470).
