# Data Boar — início rápido (cerca de 5 minutos)

**Público:** DPO, jurídico, compliance ou patrocinador de TI que quer **ver um resultado** antes de ler o manual completo.

**Aprofundar depois:** [docs/USAGE.md](docs/USAGE.md) (operador) · [docs/TECH_GUIDE.md](docs/TECH_GUIDE.md) (integrador) · [docs/pitch/INDEX.pt_BR.md](docs/pitch/INDEX.pt_BR.md) (narrativa por papel)

---

## O que você vai conseguir

Ao final deste roteiro você terá:

1. O motor rodando (Docker **ou** Python local).
2. Uma varredura de demonstração em pasta de teste do repositório.
3. O **dashBOARd** no navegador com achados e mapa de calor.

O Data Boar **não substitui** assessoria jurídica; produz **sinais técnicos** para triagem.

---

## Pré-requisitos (mínimo)

| Caminho | Você precisa de |
| ------- | ---------------- |
| **A — Docker (recomendado com TI)** | [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução |
| **B — Python local (TI no mesmo PC)** | [uv](https://docs.astral.sh/uv/) + Git; Python **3.12+** (o `uv sync` resolve o restante) |

**Sem YAML do zero:** copie um [config de amostra](deploy/samples/config.starter-lgpd-eval.yaml) **ou** gere alvos a partir de planilha — [docs/ops/SCOPE_IMPORT_QUICKSTART.pt_BR.md](docs/ops/SCOPE_IMPORT_QUICKSTART.pt_BR.md).

---

## Caminho A — Docker (menos fricção para não desenvolvedores)

Execute na **raiz do clone** (ajuste o caminho do repositório):

```powershell
cd C:\caminho\para\data-boar
mkdir -Force data | Out-Null
Copy-Item deploy\samples\config.starter-lgpd-eval.yaml data\config.yaml
docker pull fabioleitao/data_boar:latest
docker run -d --name data-boar-quickstart -p 8088:8088 `
  -v "${PWD}/data:/data" `
  -e CONFIG_PATH=/data/config.yaml `
  fabioleitao/data_boar:latest
```

<details>
<summary>Linux / macOS (bash)</summary>

```bash
cd /caminho/para/data-boar
mkdir -p data
cp deploy/samples/config.starter-lgpd-eval.yaml data/config.yaml
docker pull fabioleitao/data_boar:latest
docker run -d --name data-boar-quickstart -p 8088:8088 \
  -v "$PWD/data:/data" \
  -e CONFIG_PATH=/data/config.yaml \
  fabioleitao/data_boar:latest
```

</details>

1. Peça à TI para ajustar os caminhos em `data\config.yaml` (pastas reais **ou** use o [Caminho B](#caminho-b--python-local-para-desenvolvedor--ti-técnico) com a pasta de demo).
2. Abra no navegador: [http://localhost:8088/pt-br/](http://localhost:8088/pt-br/) (ou `/en/`).
3. No dashBOARd, dispare uma varredura (botão de scan) ou siga a ajuda embutida em **Ajuda / Help**.

Detalhes de volume e persistência: [docs/DOCKER_SETUP.pt_BR.md](docs/DOCKER_SETUP.pt_BR.md).

---

## Caminho B — Python local (para desenvolvedor / TI técnico)

Ideal para validar o produto **sem** expor dados reais: usamos a pasta sintética `tests/data/homelab_synthetic/`.

```powershell
cd C:\caminho\para\data-boar
uv sync
```

Crie `quickstart.config.yaml` na raiz do clone com:

```yaml
targets:
  - name: demo-lab
    type: filesystem
    path: tests/data/homelab_synthetic
    recursive: true
```

Suba o dashBOARd e aceite HTTP explícito em laboratório (não use em produção sem TLS):

```powershell
uv run python main.py --web --config quickstart.config.yaml --allow-insecure-http
```

1. Abra [http://127.0.0.1:8088/pt-br/](http://127.0.0.1:8088/pt-br/).
2. Inicie uma varredura pela interface.
3. Confira o relatório Excel / heatmap na pasta de saída configurada (padrão relativo ao config — ver [docs/USAGE.md](docs/USAGE.md)).

**Sucesso:** aparecem achados de exemplo (padrões de documento fictícios). Se a lista estiver vazia, confira se `path` aponta para a pasta correta e se a varredura terminou sem erro no log do terminal.

---

## Próximos passos (5–30 minutos)

| Objetivo | Onde ir |
| -------- | ------- |
| Escopo real (pastas, bancos, shares) | [deploy/samples/README.pt_BR.md](deploy/samples/README.pt_BR.md) + import CSV em [docs/ops/SCOPE_IMPORT_QUICKSTART.pt_BR.md](docs/ops/SCOPE_IMPORT_QUICKSTART.pt_BR.md) |
| Mapa “quem lê o quê” | [docs/AUDIENCE_GUIDE.pt_BR.md](docs/AUDIENCE_GUIDE.pt_BR.md) |
| Marco regulatório (LGPD, GDPR, amostras) | [docs/COMPLIANCE_FRAMEWORKS.pt_BR.md](docs/COMPLIANCE_FRAMEWORKS.pt_BR.md) |
| Referência completa de flags e API | [docs/USAGE.md](docs/USAGE.md) |
| Arquitetura e conectores | [docs/TECH_GUIDE.md](docs/TECH_GUIDE.md) |

---

**Mantenedores:** gate de integridade em [CONTRIBUTING.md](CONTRIBUTING.md).
