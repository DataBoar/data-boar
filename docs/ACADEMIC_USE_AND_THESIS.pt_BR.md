# Uso acadêmico e orientação para tese (Data Boar)

**English:** [ACADEMIC_USE_AND_THESIS.md](ACADEMIC_USE_AND_THESIS.md)

Este documento ajuda **estudantes, orientadores e bancas** a usar a documentação e o código **públicos** do Data Boar em **dissertações, teses e relatórios de pesquisa**, sem misturar segredos de produto, dados pessoais ou material comercial exclusivo do operador. É **orientação**, não **aconselhamento jurídico**; confirme requisitos com o **programa de pós-graduação** e, se necessário, com **advogado**.

---

## 1. O que é o Data Boar (ponteiros)

- **Visão de produto e mensagem:** [README.md](../README.md) ([pt-BR](../README.pt_BR.md)) (enquadramento para decisores e compliance).
- **Operação técnica:** [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md) (instalação, CLI, API, conectores, config).
- **Enquadramento de compliance (não substitui parecer jurídico para o seu estudo):** [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md), [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md).
- **Linha de base histórica do repositório e ADRs:** [adr/ADR-0000-project-origin-and-adr-baseline.md](adr/ADR-0000-project-origin-and-adr-baseline.md) *(EN).*

---

## 2. Licença e atribuição

- **Licença do open core (árvore pública):** [LICENSE](../LICENSE) — **BSD 3-Clause** (permissiva; em redistribuições, manter aviso de copyright e texto da licença — veja o arquivo para condições exatas).
- **Enforcement comercial opcional** (tokens em runtime) está em [LICENSING_SPEC.md](LICENSING_SPEC.md) *(EN)*; em desenvolvimento e replicação acadêmica costuma usar-se o modo **`open`** (sem token pago). Veja também [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) *(EN)* para o desenho pretendido do produto.
- **Como citar o software** na tese (adapta ao estilo da instituição):
- **Repositório:** URL Git canônica (ex.: GitHub `FabioLeitao/data-boar` ou sucessor), **hash de commit** ou **tag de release**, e **data de acesso**.
- **Versão:** alinha com [VERSIONING.pt_BR.md](VERSIONING.pt_BR.md) / `pyproject.toml` quando congelares uma linha de reprodução.
- **Licença:** indica **BSD 3-Clause** e aponta para o arquivo **`LICENSE`** na raiz (alguns programas pedem anexo de licenças).

---

## 3. O que normalmente você pode usar no trabalho acadêmico

- **Código-fonte público** e **documentação rastreada** neste repositório para: metodologia, descrição de arquitetura, comparação de heurísticas ou pipelines ao nível de **desenho**, e instruções de reprodutibilidade.
- **Figuras ou citações** de docs, com referência (respeita **direitos de autor** sobre texto expressivo e **marca** no branding — veja [COPYRIGHT_AND_TRADEMARK.pt_BR.md](COPYRIGHT_AND_TRADEMARK.pt_BR.md)).
- **Dados sintéticos ou públicos** para experiências; veja [tests/README.md](../tests/README.md) sobre amostras de texto opcionais (respeita **termos** e **copyright** de terceiros).

---

## 4. O que exige cuidado extra (muitas vezes obrigatório)

- **Dados pessoais (PII):** **não** incluas datasets reais de produção em anexo de tese. Prefer **dados sintéticos**, **corpora públicos** ou amostras **fortemente redigidas**; segue **LGPD** / **GDPR** e o seu comitê de ética, quando aplicável.
- **Confidencialidade de operador e cliente:** **sem** hostnames, **IPs** de LAN, **credenciais** ou cenários **identificáveis** de clientes no texto público da tese, salvo **autorização escrita** e plano de **redação**.
- **`docs/private/`** (e árvores **gitignored** semelhantes): **não** fazem parte do pacote acadêmico público — **não** colar em repositórios institucionais rastreados como se fosse doc pública do produto.
- **Material só comercial** (estudos de precificação, propostas, rate cards): mantém **fora** da entrega pública da tese; guarda segundo política acordada com a instituição (muitas vezes **anexo separado** com controlo de acesso, ou omissão).

---

## 5. Checklist de reprodutibilidade (recomendado para bancas)

1. Indica **commit Git** ou **tag**, versão de **Python** (ex.: 3.12/3.13) e como instalaste dependências (**`uv sync`** / lockfile).
1. Inclui excerto de `config` **sanitizado** baseado em [deploy/config.example.yaml](../deploy/config.example.yaml) — **sem segredos**.
1. Se usaste Docker, cita **tag da imagem** e referência ao **`Dockerfile`** / compose em [DOCKER_SETUP.pt_BR.md](DOCKER_SETUP.pt_BR.md).
1. Registre **`licensing.mode: open`** (ou equivalente) se quem replica **não** deve precisar de token comercial.
1. Liste **testes** ou **scripts** que você executou (alvos `pytest`, flags CLI) para outros verificarem afirmações **sem** seus dados privados.

---

## 6. Instituição, autoria e PI

- Muitas universidades têm regras sobre **autoria de software**, **direitos do orientador** e **PI da empresa** se estiveres empregado durante o mestrado ou doutorado. Esclarece **cedo** com a **secretaria do programa** ou **inovação / transferência de tecnologia**.
- Se fores simultaneamente **mantenedor** e **autor**, explicita na tese **qual é a contribuição científica** (ex.: heurística nova, desenho de avaliação) face à **documentação de produto** escrita para operadores.

---

## 7. Documentos relacionados

- **Portfólio, suplementos PUCRS, extensões PUC-Rio Digital, cadência de estudo:** Use a entrada **Interno e referência** em [docs/README.pt_BR.md](README.pt_BR.md) para abrir `docs/plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md` (este guia **não** usa link direto para `docs/plans/` por política do repositório). Lá, ver **seção 3.3** (suplementos PUCRS), a subseção **PUC-Rio Digital extension courses** (recomendações alinhadas a benefício; confirmar com o **contrato privado** em `docs/private/academic/`) e **seção 3.0** (cadência semanal) — tabelas de plano em inglês.
- [CONTRIBUTING.pt_BR.md](../CONTRIBUTING.pt_BR.md) — higiene do contribuidor (sem segredos no repo público).
- [SECURITY.pt_BR.md](../SECURITY.pt_BR.md) — versões suportadas e reporte de vulnerabilidades.
- [TESTING.pt_BR.md](TESTING.pt_BR.md) — que verificações automáticas existem (útil para capítulos de “validação”).
- [docs/adr/README.pt_BR.md](adr/README.pt_BR.md) — decisões **porquê** registradas após adoção de ADRs.

---

## Aviso

Este arquivo **não** constitui **aconselhamento jurídico**. Licenciamento, proteção de dados e regras de tese dependem de **jurisdição** e **instituição**. Usa este guia para alinhar orientação e assessoria; **não** substitui revisão formal.
