# Resolução de problemas (Data Boar)

**English:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

Esta página traz **dicas curtas** para problemas comuns. Para **análise de causa raiz e correções passo a passo**, use os documentos de aprofundamento linkados. Operadores (incluindo consultores e clientes que licenciam o app) podem usar este guia para resolver problemas de conectividade, credenciais e implantação antes da próxima varredura.

---

## Onde ver o que deu errado

- **Relatório Excel — planilha "Scan failures":** Cada alvo com falha tem **Target**, **Reason** (ex.: `unreachable`, `auth_failed`, `timeout`), **Details** (mensagem da exceção) e **Suggested next step** (dica curta gerada pela aplicação). Comece por aqui após uma execução.
- **Dashboard:** Contagem de "Scan failures" e sessões recentes; baixe o relatório da sessão para abrir a planilha Scan failures.
- **Log de auditoria:** `audit_YYYYMMDD.log` (caminho no config ou no diretório de saída dos relatórios). Download em **Reports → sessão → Download log** ou API `GET /logs/{session_id}`. Contém entradas de conexão e falha com nome do alvo e texto do erro.
- **Respostas da API:** `POST /scan` retorna 409 se já houver varredura em andamento; 429 se os limites de taxa forem excedidos. Endpoints de sessão/relatório retornam 404 com mensagem clara quando a sessão ou o relatório não existir.

A aplicação mapeia **reasons** de falha para um **Suggested next step** no relatório (ex.: "Target did not respond. Check network connectivity…"). Se isso não bastar, use os documentos de aprofundamento abaixo.

---

## Dicas rápidas por motivo de falha

| Reason (no relatório)                       | O que verificar primeiro                                                                                                                                                                        | Documento de aprofundamento                                                                                           |
| ----------------------                      | --------------------------                                                                                                                                                                      | -----------------------------                                                                                         |
| **unreachable**                             | Rede do host/container de auditoria até o alvo: DNS, roteamento, firewall, VPN. Para Docker: veja [TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md). | [Conectividade](TROUBLESHOOTING_CONNECTIVITY.pt_BR.md) · [Docker](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md)     |
| **auth_failed** / **authentication_failed** | Credenciais (usuário/senha, token, OAuth client_id/secret). Evite enviar a mesma credencial no header e no body.                                                                                | [Credenciais e autenticação](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md)                                           |
| **permission_denied**                       | O scanner precisa de acesso de leitura ao recurso (share, DB, API). Execute como usuário/conta de serviço com permissão ou ajuste permissões.                                                   | [Conectividade](TROUBLESHOOTING_CONNECTIVITY.pt_BR.md)                                                                |
| **timeout**                                 | Alvo lento ou inacessível; valor de timeout muito baixo. Aumente o timeout no config (por alvo ou global); tente em horário de menor uso.                                                       | [Conectividade](TROUBLESHOOTING_CONNECTIVITY.pt_BR.md)                                                                |
| **error** (genérico)                        | Veja **Details** no relatório. Frequentemente config (host, port, URL ausentes) ou dependência opcional ausente (ex.: `.[shares]` para SMB).                                                    | [Conectividade](TROUBLESHOOTING_CONNECTIVITY.pt_BR.md) · [Credenciais](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md) |

---

## Arquivos `.doc` legados: nome do arquivo vs texto do corpo

Varreduras em filesystem **sempre** usam **caminho e nome do arquivo**. O **texto do corpo** para a extensão `.doc` usa a biblioteca opcional **`mammoth`** (instale o extra **`legacy-doc`**: `pip install -e ".[legacy-doc]"` ou `uv sync --extra legacy-doc`).

**O que você ganha:** O mammoth lê **Office Open XML empacotado em ZIP** (a mesma família de contêiner que `.docx`). Isso cobre alguns `.doc` reais que são OOXML de fato, ou que foram renomeados.

**Limitação:** O `.doc` **binário Word 97-2003** (arquivo composto OLE) **não** é ZIP; o mammoth em geral **não** abre, então a **amostra de conteúdo fica vazia** e só o nome/caminho entra nos achados.

### Extração nativa de corpo em `.doc` OLE/CFBF — decisão won't-fix

O Data Boar **não implementará** extração nativa de corpo para arquivos `.doc` OLE2/CFBF (Compound File Binary Format) via LibreOffice por subprocesso ou conversor similar. Esta é uma **decisão de escopo explícita e permanente**, não uma lacuna temporária.

**Racional:**

| Motivo | Detalhe |
| ------ | ------- |
| **Peso da dependência** | O LibreOffice instala ~400 MB de binários e fontes no ambiente de varredura; inaceitável para um container leve de análise de dados. |
| **Superficie de ataque / vetores RCE** | Chamar uma suite de escritório por subprocesso para analisar documentos binários não confiáveis é uma classe conhecida de risco de RCE. Analisar binários OLE malformados com LibreOffice expõe o host a toda a sua superficie de vulnerabilidade. |
| **Memória e isolamento** | O LibreOffice não foi projetado para invocações headless de alta concorrência; vazamentos de processo e crashes por OOM foram observados em ambientes de varredura em produção. |
| **Prevalência do formato** | Arquivos `.doc` binários Word 97-2003 representam uma fração decrescente dos corpora empresariais; a maioria dos sistemas modernos de gestão de documentos já normaliza para `.docx` ou PDF na ingestão. |

**O que fazer em vez disso:**

- **Converter antes da varredura:** Execute `libreoffice --headless --convert-to docx seu_arquivo.doc` (ou um serviço gerenciado de conversão) nos arquivos **antes** da varredura. O Data Boar lê o `.docx` resultante nativamente.
- **Use a saída `.docx` do seu DMS:** Configure seu Sistema de Gestão de Documentos para exportar em `.docx`/PDF ao alimentar o Data Boar.
- **O caminho do arquivo ainda é varrido:** Mesmo sem conteúdo do corpo, o Data Boar sinaliza o arquivo pelo caminho e nome se houver PII (ex.: `CPF_000000000-00_contrato.doc`).

Esta decisão está registrada no issue do GitHub [#671](https://github.com/DataBoar/data-boar/issues/671). Não é necessário ADR — este é um limite de escopo won't-fix, não uma troca arquitetural.

---

## Docker: conectar a dados remotos a partir do container

Muitas implantações usam a **imagem Docker**. O container precisa conseguir alcançar seus bancos de dados, shares de arquivos (NFS/SMB) e APIs.

- **Bancos remotos:** Use o **IP ou FQDN do host** do servidor de DB no config (não use `localhost` a menos que o DB rode no mesmo container). No host, teste com `psql`, `mysql` ou similar; no container, garanta que a rede do container alcance esse host (geralmente não é preciso host networking; em alguns ambientes use `host.docker.internal`).
- **NFS/SMB a partir do container:** Duas abordagens comuns: (1) **Montar o share no host** e fazer bind mount desse caminho no container (ex.: `-v /mnt/nfs-share:/data/shares`), depois usar um alvo **filesystem** em `/data/shares`; (2) **Usar alvos NFS/SMB** no config e garantir que a rede do container alcance o servidor NFS/SMB (instale `.[shares]` na imagem; abra firewall para portas NFS/SMB). Para passos e armadilhas, veja [TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md).
- **DNS:** Se o config usar hostnames, o container precisa resolvê-los (mesmo DNS do host ou `--dns`). Veja [TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md).

---

## Casos de borda no onboarding via PyPI/pipx (Linux)

Em hosts **Debian/Ubuntu**, **Fedora** e **RHEL/Alma/Rocky/Oracle 10**, o caminho padrão `pipx install data-boar` está sem atrito quando o host já resolve Python >=3.12.

Para os demais caminhos Linux, use a divisão abaixo (sem overclaim):

### RHEL 8 e RHEL 9 (inclui Alma): forçar Python 3.12 no `pipx`

Esses hosts ainda podem resolver `python3` padrão abaixo do piso do pacote e falhar com:

- `ERROR: Ignored ... Requires-Python >=3.12`
- `ERROR: No matching distribution found for data-boar`

Use Python 3.12 de forma explícita:

```bash
sudo dnf install -y python3.12
pipx install --python python3.12 data-boar
```

### Void-glibc vs Void-musl

- **Void-glibc:** hoje passa no caminho padrão (`pipx install data-boar`) porque o PyPI publica wheel compatível `cp314`.
- **Void-musl:** o upstream **não** publica wheel `scikit-learn` musllinux em nenhum `cpXXX`. O passo 1 abaixo ainda exige pasta local de wheels (ou **URL direta de `.whl`** — não a página de release do GitHub). O passo 2 é obrigatório para o stack de ML; em CPU **x86-64-v1** o passo 2 também troca o numpy do PyPI (ver [x86-64-v1 / instalação via wheelhouse](#x86-64-v1--instalação-via-wheelhouse-musl-sem-avx-e-hosts-min-spec)).

### Alpine/musl: wheelhouse ou toolchain de build

Nesse caminho, `scikit-learn` pode cair em compilação via source no musl. Sem toolchain de build, `pipx install data-boar` pode falhar com `metadata-generation-failed`.

Compilar localmente com toolchain (`apk add build-base gfortran openblas-dev`) resolve lacunas musl, mas **não** resolve CPU **x86-64-v1** — wheels numpy/scipy do PyPI ainda dão SIGILL. Em hardware x86 anterior a 2011, use o [caminho wheelhouse](#x86-64-v1--instalação-via-wheelhouse-musl-sem-avx-e-hosts-min-spec) em vez de assumir que compilar = stack binário funcional.

Se não houver wheelhouse e a CPU for moderna, instale pré-requisitos antes:

```bash
apk add build-base gfortran openblas-dev
pipx install data-boar
```

Evolução do wheelhouse: [#929](https://github.com/DataBoar/data-boar/issues/929) e [#1182](https://github.com/DataBoar/data-boar/issues/1182).

### x86-64-v1 / instalação via wheelhouse (musl, sem AVX e hosts min-spec)

Use quando **qualquer** destes casos se aplicar:

- **musl** (Alpine, Void-musl) e você precisa do stack de ML completo sem toolchain Fortran local.
- **CPU x86 anterior a 2011** onde `import numpy` morre com **`Illegal instruction`** (classe Core 2 / Celeron / Pentium — só `ssse3`, sem SSE4.2/POPCNT). O piso é **`x86-64-v1`**, não só “sem AVX”: wheels do PyPI miram **`x86-64-v2`** ou superior; variáveis de ambiente (`NPY_DISABLE_CPU_FEATURES`, `OPENBLAS_CORETYPE`) **não** ajudam porque o crash está na **baseline compilada**, não no despacho em runtime ([#929](https://github.com/DataBoar/data-boar/issues/929)).
- Instalação **air-gapped** ou com egress restrito que precisa resolver offline.

**Release hospedado (verificado):** [wheelhouse-x86-64-v1-2026-07-29](https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-x86-64-v1-2026-07-29) em `DataBoar/data-boar-site` — 41 wheels, `SHA256SUMS` anexo. Texto completo de instalação/verificação também no asset `README.md` do release.

**`boar_fast_filter` não está no PyPI.** O wheel publicado de `data-boar` é `py3-none-any` com **zero** extensões compiladas — toda instalação só-PyPI usa o fallback de pré-filtro em Python puro. Hoje o wheelhouse é o **único** canal do acelerador Rust (`cp38-abi3`, um wheel por libc).

#### `--find-links` adiciona um índice; não prefere

Os nomes de arquivo batem com o PyPI (`numpy-2.5.1-cp312-cp312-musllinux_1_2_x86_64.whl`, etc.), então o pip ainda pode escolher o wheel **upstream** no passo 1. A instalação real tem **dois passos forçados** após o download (mais inject do acelerador):

- `--find-links` aceita **pasta local**, **URL direta de `.whl`** ou **página HTML de links** — **não** a página de **release** do GitHub. Com ~40 wheels, baixe para uma pasta primeiro.

```bash
TAG=wheelhouse-x86-64-v1-2026-07-29
mkdir -p ~/wheelhouse-v1
gh release download "$TAG" --repo DataBoar/data-boar-site \
  --pattern '*musllinux*' --pattern '*-none-any.whl' --dir ~/wheelhouse-v1
# hosts glibc: troque *musllinux* por *manylinux*
# sem gh: baixe os mesmos assets na página do release (navegador ou curl -LO)

# armadilha tmpfs — veja abaixo antes de qualquer passo pip que possa compilar
export TMPDIR="${TMPDIR:-/var/tmp/data-boar-build}"
mkdir -p "$TMPDIR"

pipx install data-boar --pip-args="--find-links $HOME/wheelhouse-v1"
pipx runpip data-boar install --no-index --find-links $HOME/wheelhouse-v1 \
  --force-reinstall numpy scipy scikit-learn pandas
pipx inject data-boar boar_fast_filter --pip-args="--no-index --find-links $HOME/wheelhouse-v1"
```

**`--find-links` com um único `.whl`** (só uma célula musllinux faltando) pode destravar o passo 1, mas **não** substitui o numpy do PyPI em CPU v1 — ainda precisa do `--force-reinstall` offline.

#### `TMPDIR` em tmpfs (hosts min-spec)

Se a instalação falhar com `[Errno 28] No space left on device` com disco livre na raiz, confira se `/tmp` é **tmpfs** pequeno (padrão: metade da RAM). Build de `scikit-learn` pode não caber mesmo com centenas de GB livres no disco. Aponte o scratch do pip para armazenamento real **antes** do passo 1:

```bash
export TMPDIR=/var/tmp/data-boar-build && mkdir -p "$TMPDIR"
```

**Interação com `--demo`:** o relatório do demo vai para **`$TMPDIR/data_boar_demo`**. Se você definiu `TMPDIR` na instalação, procure o relatório lá — não só em `/tmp`.

#### Verificar que a troca pegou

```bash
python -c "from core import detector; print(detector._ML_AVAILABLE)"   # deve imprimir True
python -c "
import glob, os, numpy
so = glob.glob(os.path.join(numpy.__path__[0], '_core', '_multiarray_umath*.so'))[0]
print(os.path.getsize(so), 'bytes')
"
# este wheelhouse: ~5–5,3 MB; numpy PyPI na mesma tag: ~10,8 MB (SIGILL em v1)
objdump -d "$(python -c 'import glob,os,numpy;print(glob.glob(os.path.join(numpy.__path__[0],"_core","_multiarray_umath*.so"))[0])')" \
  | grep -c popcnt   # deve imprimir 0
```

**Paridade de campo (1.7.4.post10, `--demo`):** **26 achados**, `_ML_AVAILABLE=True` — mesma contagem dos caminhos Debian/Fedora/Alma glibc quando o harness espera o relatório (ver matriz). Em metal: Intel Celeron 900, Alpine/musl, caminho wheelhouse offline.

#### Armadilhas de automação com `--demo`

- **`data-boar --demo` não encerra** após o scan — sobe a API em **`127.0.0.1:8088`** e fica em **LISTEN**. Espere o **relatório** em `$TMPDIR/data_boar_demo`, não o fim do processo.
- Se você mudou `TMPDIR` na instalação (contorno tmpfs), o relatório do demo segue **`$TMPDIR`** — não procure só em `/tmp/data_boar_demo`.

### Hosts sem AVX (ponteiro)

Não assuma caminho PyPI sem atrito. Use a [instalação wheelhouse x86-64-v1](#x86-64-v1--instalação-via-wheelhouse-musl-sem-avx-e-hosts-min-spec) ou Docker.

### RHEL 7 / CentOS 7 (EOL)

Trate instalação nativa via `pipx` como fora de escopo para os builds atuais (repositórios EOL e piso de Python inalcançável). Use Docker.

---

## O Data Boar é útil para sua organização?

- **Com consultor treinado:** Um consultor pode instalar, configurar e ajustar o Data Boar na sua rede; definir credenciais e alvos; executar varreduras e interpretar relatórios. É a forma de menor risco quando a maturidade de TI/conformidade/DPO ainda está crescendo.
- **Só licença (autoatendimento):** Você pode rodar o app sozinho: siga [TECH_GUIDE](TECH_GUIDE.pt_BR.md), [USAGE](USAGE.pt_BR.md) e [deploy/DEPLOY](deploy/DEPLOY.pt_BR.md). Use este guia de resolução de problemas e os documentos de aprofundamento quando tiver falhas de conectividade ou credenciais. Para ambientes complexos (muitas fontes, firewall rígido, SSO/OAuth), ainda se recomenda suporte de consultoria.
- **Docker:** A maioria das implantações usa o container; a conexão com DBs remotos e com NFS/SMB está documentada no deploy e nos documentos de troubleshooting acima.

---

## Documentação de aprofundamento (causa raiz e passos de correção)

| Tópico                         | Descrição                                                                                        | English                                                                            | Português (pt-BR)                                                                              |
| --------                       | -----------                                                                                      | ---------                                                                          | -------------------                                                                            |
| **Conectividade**              | Rede, DNS, firewall, timeouts; DB/API/share inacessível; permission_denied                       | [TROUBLESHOOTING_CONNECTIVITY.md](TROUBLESHOOTING_CONNECTIVITY.md)                 | [TROUBLESHOOTING_CONNECTIVITY.pt_BR.md](TROUBLESHOOTING_CONNECTIVITY.pt_BR.md)                 |
| **Credenciais e autenticação** | API key no header vs body; Basic/Bearer/OAuth; credenciais conflitantes; lockouts                | [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md) | [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md) |
| **Implantação Docker**         | Rodar em container; NFS/SMB a partir do container; DB remoto a partir do container; DNS; volumes | [TROUBLESHOOTING_DOCKER_DEPLOYMENT.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.md)   | [TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md)   |

**Índice da documentação:** [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
