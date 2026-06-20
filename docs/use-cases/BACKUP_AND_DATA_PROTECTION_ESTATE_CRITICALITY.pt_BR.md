# Storyboard de caso de uso — parque de backup / proteção de dados, camada de criticidade

**English:** [BACKUP_AND_DATA_PROTECTION_ESTATE_CRITICALITY.md](BACKUP_AND_DATA_PROTECTION_ESTATE_CRITICALITY.md)

Storyboard em documentação para organizações que já operam uma **plataforma corporativa de backup, recuperação e proteção de dados** e precisam de uma **camada de criticidade / sensibilidade** sobre ela. **Não** é produto de backup/DR, **não** garante recuperabilidade e **não** certifica nenhum fornecedor de proteção de dados.

## Elenco (papéis genéricos)

- **Organização:** Equipe enterprise ou mid-market que opera uma **plataforma de snapshots imutáveis / ciber-resiliência / backup** (cópias de DR, arquivos de retenção longa) entre armazenamento primário e secundário.
- **Titulares:** Funcionários, clientes e parceiros cujos registros vivem dentro do parque protegido (bancos, compartilhamentos, e-mail, dados de aplicação) — e, por extensão, **cada cópia** que a plataforma de proteção espalha.
- **Sistemas:** Compartilhamentos/bancos de produção que são **fontes** do parque de backup, cópias **restauradas/montadas somente leitura**, catálogos de exportação e os próprios inventários/relatórios da plataforma de proteção.

## Storyboard (fluxo)

1. **Proteção sem criticidade** — a plataforma responde “está tudo recuperável?”, mas o **checklist de maturidade** dela mesma faz a pergunta mais difícil: “você tem visibilidade sobre **quais** dados são mais críticos ou mais sensíveis?” Essa linha fica em branco.
2. **A cópia cega** — a proteção espalha os dados em snapshots, sites de DR e camadas de retenção longa; registros sensíveis e críticos agora estão **multiplicados** pelo parque **sem rótulo de criticidade**.
3. **Boar fareja (com escopo, somente leitura)** — aponte o Data Boar para **cópias restauradas/montadas** ou compartilhamentos/bancos de origem em acesso **somente leitura**; densidade de PII, categorias sensíveis, menores e sequências tipo documento nacional aparecem no mapa de calor do relatório.
4. **Camada de criticidade** — os achados viram a **camada de criticidade/sensibilidade** que falta à plataforma de proteção: quais compartilhamentos, tabelas e caminhos concentram dado regulado e onde retenção e imutabilidade mais importam.
5. **Momento humano** — os donos decidem camadas de retenção, retenção legal (legal hold) e escopo de acesso; **assessoria** interpreta. O produto **não** decide classes de criticidade, **não** faz backup/restore e **não** afirma recuperabilidade.

## Como o Data Boar ajuda sem decidir

- **Responde ao gap do checklist** que a própria plataforma de proteção levanta (“quais dados são mais críticos?”) com **evidência técnica**, não com promessa de recuperabilidade.
- **Prioriza** onde o dado sensível se concentra para que retenção, imutabilidade e gasto de DR possam **seguir a criticidade** em vez de tratar toda cópia igual.
- **Não** faz backup, restauração, replicação nem certifica recuperabilidade; ele **mapeia**, não protege.

## Oportunidade para parceiros

Parceiros que já vendem ou operam **plataformas corporativas de backup / proteção de dados** acoplam o Data Boar como a **camada de descoberta de criticidade e sensibilidade** que fecha o gap “você sabe o que é mais crítico?” na **própria avaliação de maturidade do fornecedor**. Vendido como **oficina de descoberta de escopo fixo** sobre a base instalada e depois repassado ao TI/DPO para decisões de retenção e acesso. O argumento se escreve sozinho: a plataforma **faz** a pergunta; o Data Boar é a **resposta**.

## Alinhamento de produto (maintainers)

Priorize superfícies que ingerem **cópias restauradas/montadas e catálogos de exportação** como raízes de varredura (filesystem + compactados + amostragem SQL em montagens somente leitura) e **relatórios de criticidade/sensibilidade** (mapa de calor, camadas de gravidade, dicas de jurisdição). Mantenha o posicionamento como **camada de evidência**, não de proteção. **Não** coloque links de sequenciamento desta página voltada a compradores para `docs/plans/`; use a seção **Internal and reference** do [docs/README.pt_BR.md](../README.pt_BR.md) como entrada para maintainers.

**Sinais fortes neste vertical:** `file_scan`, tratamento de arquivos compactados, conectores SQL opcionais, mapa de calor / saídas de compliance, [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md), [ADDING_CONNECTORS.pt_BR.md](../ADDING_CONNECTORS.pt_BR.md).

## Documentação relacionada

- [use-cases/README.pt_BR.md](README.pt_BR.md) ([EN](README.md))
- [SERVICE_TIERS_SCOPE_TEMPLATE.pt_BR.md](../ops/SERVICE_TIERS_SCOPE_TEMPLATE.pt_BR.md) ([EN](../ops/SERVICE_TIERS_SCOPE_TEMPLATE.md))
- [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](../DECISION_MAKER_VALUE_BRIEF.pt_BR.md) ([EN](../DECISION_MAKER_VALUE_BRIEF.md))
- [USAGE.pt_BR.md](../USAGE.pt_BR.md) ([EN](../USAGE.md))
