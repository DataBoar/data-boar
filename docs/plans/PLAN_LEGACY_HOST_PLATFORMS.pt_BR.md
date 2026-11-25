# PLANO: Plataformas de host legadas (Linux s390x, AIX, HP-UX, z/OS)

**Status:** Em andamento (classificação documentada; **nada testado localmente**; receita QEMU s390x pendente)
**Data:** 2026-11-25
**Prioridade:** P3
**GitHub:** [#2183](https://github.com/DataBoar/data-boar/issues/2183)
**Relaciona-se com:** [#1666](https://github.com/DataBoar/data-boar/issues/1666) (caminho indireto do mainframe), [#2179](https://github.com/DataBoar/data-boar/issues/2179) (BSD), [#1182](https://github.com/DataBoar/data-boar/issues/1182) (wheelhouse), [OS_COMPATIBILITY_TESTING_MATRIX.pt_BR.md](../ops/OS_COMPATIBILITY_TESTING_MATRIX.pt_BR.md), [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md)

---
<!-- plans-hub-summary: Fronteira host × alvo das plataformas legadas (Linux s390x, AIX, HP-UX, z/OS) em três classes de evidência; nada testado localmente; receita QEMU s390x pendente; evidência futura de wheels via release no data-boar-site + índice PEP 503 simple/ (mesmo padrão do #1182). -->

## Contexto

AIX, HP-UX e o mainframe (IBM Z) continuam presentes em bancos, seguradoras e outros setores regulados com bancos de dados e processamento legados. O repositório não tinha plano sobre **rodar o Data Boar como host** nessas plataformas. A [#1666](https://github.com/DataBoar/data-boar/issues/1666) já define o caminho **indireto** para o mainframe: não se trata de rodar o Boar no mainframe; o dado chega ao Data Soup por export controlado e somente leitura. Este plano registra a fronteira **host × alvo** das plataformas legadas.

## Três classes

Cada plataforma cai em **uma** classe, com evidência:

1. **Host validável em VM:** o Data Boar roda e é testado em máquina virtual, de forma reproduzível.
2. **Host só com hardware ou licença do fabricante:** não validável em emulação aberta; sem promessa de suporte sem evidência.
3. **Apenas alvo (ingrediente do Data Soup):** o Data Boar não roda ali; o dado chega por export (SFTP/FTPS/NFS/MQ, degrau 1 da #1666) a um host suportado.

## Estado conhecido (relatos de terceiros e metadados; **nada testado localmente**)

| Plataforma | Classe | Base (não verificada localmente) | Falta verificar |
| --- | --- | --- | --- |
| **Linux s390x (IBM Z / LinuxONE)** | candidata à **1** | `qemu-system-s390x` existe nos repositórios Debian/Ubuntu e as distribuições publicam imagens oficiais s390x. A emulação por TCG é lenta (sem medição confiável). Valor técnico: arquitetura **big-endian**, que pode revelar suposições de endianness em wheels nativas e na extensão Rust. | URL, tamanho e hash das imagens; wheels s390x da pilha (numpy, scipy, scikit-learn, cryptography); a receita QEMU validada abaixo. |
| **AIX (POWER)** | candidata à **2** | Relatos de 2024 dizem que o QEMU `pseries` **não** inicializa o AIX 7.3; a mídia depende de licenciamento da IBM. | Disponibilidade de Python 3.12+ e de toolchain no AIX antes de qualquer promessa. |
| **HP-UX (PA-RISC / Itanium)** | candidata à **2 ou 3** | O QEMU emula PA-RISC (`B160L`, `C3700`) com relatos mistos para o HP-UX 11.11 e falhas relatadas no 11.23/11.31; sem fonte para Itanium. Mídia licenciada. | Se existe algum caminho reproduzível; até lá, nenhuma alegação de host. |
| **z/OS** | **3** (alvo) | Como na #1666. Python no z/OS existe como produto do fabricante; rodar o Boar ali não é objetivo deste plano. | Nada do lado do host; a ingestão segue a #1666. |

## Receita QEMU do Linux s390x (pendente de aceite)

**Não feita.** Aceite deste passo (issue [#2183](https://github.com/DataBoar/data-boar/issues/2183)): instalação, ambiente Python, **`uv run python main.py --demo`** sem tracebacks, os findings esperados e a lista de **wheels que precisaram de build local** (nome do pacote, versão, comando de build), tudo registrado aqui com datas. Até lá, o s390x segue **candidato à classe 1, não verificado**.

### Evidência de wheels e de instalação (após um QEMU bem-sucedido)

Quando o QEMU fechar, **registrar neste plano** (e, se fizer sentido, arquivo datado em `docs/ops/evidence/`): URL/digest da imagem do guest; versões de Python e `uv`; resultado do demo; a **lista de wheels com build local**.

**Publicar os binários** com o mesmo contrato do wheelhouse x86-64-v1 comprovado ([#1182](https://github.com/DataBoar/data-boar/issues/1182), [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md)):

1. **GitHub Release** em **`DataBoar/data-boar-site`** (tag versionada, assets `.whl`, **`SHA256SUMS`**).
2. Índice **PEP 503 `simple/`** em **`https://databoar.com.br/simple/`** (rebuild no repositório do site via `scripts/build-wheelhouse-index.py` — sem duplicar aqui).
3. Caminho de instalação do operador documentado como no wheelhouse de hoje: [TROUBLESHOOTING.pt_BR.md](../TROUBLESHOOTING.pt_BR.md) (instalação x86-64-v1 / wheelhouse) — `pip install` / `pipx` com `--extra-index-url https://databoar.com.br/simple/` ou `--find-links` offline após `gh release download`.

**Hoje:** o índice `simple/` publicado traz células **x86_64 / arm64** (e correlatas) da tag **`wheelhouse-x86-64-v1-2026-07-29`** — **ainda não** há fatia s390x. Só planejamento; não é alegação de suporte.

## Plataformas de classe 3

Para o z/OS (e o HP-UX, se terminar na classe 3), o caminho é a ingestão da #1666: export a um host suportado. O Data Boar **não** é declarado suportado como host ali.

## Fora de escopo

Implementação de conectores (#1666, #1362); qualquer alegação de suporte sem evidência; compra de mídia licenciada sem decisão do operador.

Evidência, não conclusão jurídica ou de suporte.