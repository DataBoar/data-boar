# Primer: forense digital e evidência (KT de integrador)

**English:** [FORENSICS_AND_EVIDENCE_PRIMER.md](FORENSICS_AND_EVIDENCE_PRIMER.md)

Esta nota é para **integradores, CISOs e engenheiros de compliance** que ouvem “forensic-grade” num
**scanner de descoberta** e precisam de um **modelo mental comum**. **Não** é livro de ciência
forense, **não** substitui **laudo pericial** oficial e **não** é aconselhamento jurídico.

**Teto de posicionamento:** [ADR-0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)
(evidência e inventário, **não** motor de conclusão jurídica). Página jurídica:
[COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md). Glossário:
[GLOSSARY.pt_BR.md](../GLOSSARY.pt_BR.md) (§2 `scan_manifest`, §9 termos de evidência).

**Não duplicar:** o pitch DPO, as notas live/offline do TECH_GUIDE e a tagline do README ficam
nesses arquivos — este primer **linka**; não os reescreve.

---

## 1. O que é forense digital (wording do produto)

**Forense digital** é a prática técnica de **identificar, coletar, preservar, analisar e
interpretar** artefatos digitais para que os achados possam ser **defendidos** em auditoria,
incidente ou processo. Inspiração (não reproduzida): [ISO/IEC 27037:2012](https://www.iso.org/standard/44381.html);
[NIST SP 800-86](https://csrc.nist.gov/publications/detail/sp/800-86/final) (2006).

O papel do Data Boar nesse mundo é **estreito**: **descoberta não destrutiva, só metadados**, de
dados pessoais e sensíveis nos **alvos configurados**, mais **artefatos de sessão** que você anexa
ao *seu* pacote de evidência.

---

## 2. Ciclo de vida da evidência (seis etapas)

Um ciclo comum de seis etapas (NIST SP 800-86; [ISO/IEC 27043:2015](https://www.iso.org/standard/60943.html)
para linguagem de processo de investigação — compre as normas para o texto oficial):

| Etapa | O que significa aqui | Mapeamento Data Boar |
| ----- | -------------------- | -------------------- |
| Identificação | Decidir **o que** pode guardar dado relevante | **Alvos** configurados + política de amostragem |
| Coleta | Obter artefatos **sem** alteração desnecessária | Conectores **somente leitura**; o scan não reescreve linhas na origem |
| Preservação | Manter o material **estável e atribuível** | UUID de sessão, janela UTC, `scan_manifest_*.yaml`, SQLite da sessão |
| Análise | Interpretar **o que casou** | Pilha de detecção + `norm_tag`; **não** caracterização jurídica |
| Documentação | Registrar método, limites e resultados | Excel + Markdown executivo + manifest + bullets de trilha de auditoria |
| Apresentação | Entregar o pacote a DPO/assessoria/IR | Artefatos são **insumos**; a assessoria apresenta conclusões |

SVG: [data_boar_evidence_lifecycle.svg](../assets/diagrams/data_boar_evidence_lifecycle.svg).

---

## 3. Distinções-chave

| Contraste | Recuperação operacional | Postura forensic-grade |
| --------- | ----------------------- | ---------------------- |
| Objetivo | Restaurar serviço / achar o vazamento rápido | **Inventário** defensável de *onde* o dado sensível estava |
| Risco se for descuidado | Indisponibilidade maior | Evidência contaminada ou inexplicada |
| Documentação | Tickets, runbooks | Manifest + hashes de **escopo/config**, timestamps, versão da ferramenta |

- **Coleta ≠ aquisição ≠ preservação.** Amostrar um sistema ao vivo não é imagem de disco; gravar
  YAML não é lacrar um envelope de evidência. A ISO/IEC 27037 traça essas linhas — este produto
  **não** faz *imaging* forense.
- **Live vs offline.** A sessão Data Boar em geral lê sistemas **ao vivo** (amostras delimitadas).
  Aquisição **offline** (imagem com bloqueio de escrita) é outra disciplina, com outro risco de
  contaminação. Comportamento do motor: [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md).

SVG: [data_boar_operational_vs_forensic.svg](../assets/diagrams/data_boar_operational_vs_forensic.svg).

---

## 4. Triagem de volatilidade (lacuna)

Quando o dado some (RAM, logs que rotacionam, contêineres efêmeros), o respondente **documenta uma
ordem de prioridade**. A [ISO/IEC 27037](https://www.iso.org/standard/44381.html) trata volatilidade
como preocupação de coleta.

**Lacuna de produto:** **não** existe campo `volatility_class` em `plugin_schema.yaml` (nem
equivalente) nesta árvore hoje. **Não** invente metadado de plugin. Até haver issue dedicada, trate
volatilidade como **runbook de IR/operador**, não schema entregue.

---

## 5. Integridade e hash

Um **hash** (em geral SHA-256) mostra que uma sequência de bytes não mudou **desde que foi
hasheada**. **Não** é **cadeia de custódia** completa. Custódia ainda precisa de **quem**, **quando**
(fuso), **qual ferramenta e versão**, **quais identificadores** e **onde** o artefato está guardado.

**O que o produto registra hoje** (`report/scan_evidence.py`): `scan_manifest_*.yaml` com
produto/versão, horário UTC, **id de sessão**, **`config_scope_hash`**, janela do scan, amostragem/
timeouts e **contagens** de achados — **metadados**, sem PII bruto. Isso apoia **inventário
repetível**. **Não** é lacre assinado de evidência.

**ed25519** neste repositório serve à verificação de **JWT de licença** e à **atestação do
inventário de ADRs** — **não** assina cada manifest de scan. Não afirme que o YAML está assinado
via SSH.

---

## 6. Marco normativo (só ponteiros)

| Norma | Ano / id | Escopo (linguagem simples) | URL |
| ----- | -------- | -------------------------- | --- |
| ISO/IEC 27037 | 2012 | Identificação, coleta, aquisição, preservação | [ISO 44381](https://www.iso.org/standard/44381.html) |
| ISO/IEC 27041 | — | Adequação e suficiência dos métodos | [ISO 44405](https://www.iso.org/standard/44405.html) |
| ISO/IEC 27042 | — | Análise e interpretação técnica | [ISO 44406](https://www.iso.org/standard/44406.html) |
| ISO/IEC 27043 | 2015 | Princípios e processos de investigação | [ISO 60943](https://www.iso.org/standard/60943.html) |
| ISO/IEC 27050-1 | — | Conceitos de e-discovery / ESI | [ISO 78525](https://www.iso.org/standard/78525.html) |
| NIST SP 800-86 | 2006 | Integração de técnicas forenses na resposta a incidentes | [NIST SP 800-86](https://csrc.nist.gov/publications/detail/sp/800-86/final) |
| Guia ENISA de primeiro respondente | — | Orientação de campo | [ENISA](https://www.enisa.europa.eu/publications/electronic-evidence-a-basic-guide-for-first-responders) |
| CPP Arts. 158-A–158-F | Lei 13.964/2019 | Cadeia de custódia no processo penal brasileiro | [Planalto CPP](https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm) |

SVG (mapa de família, **não** figura ISO): [data_boar_isoiec_forensics_family.svg](../assets/diagrams/data_boar_isoiec_forensics_family.svg).

Esta página **não** cita o texto dessas normas.

---

## 7. Ética, privacidade e governança

- **Minimização:** colete só o que o **escopo autorizado** exige (LGPD arts. 6–7 como deveres
  **da organização** — o scanner não decide licitude).
- **Controle de acesso:** achados e manifests ainda são metadados **sensíveis**; trate o diretório
  de relatórios como qualquer share de compliance.
- **Incerteza (*visum et repetum*):** separe **casamentos observados** de **interpretações**.
  Declare limites (cifra, amostragem, alvos inalcançáveis) no relatório — Safe-Hold quando a
  evidência for insuficiente.

ISO/IEC 27041 + LGPD: leia os textos oficiais; este primer não substitui nenhum dos dois.

---

## 8. Posicionamento do Data Boar

O motor implementa **descoberta de PII em postura forensic-grade** no sentido de
**inventário de conformidade**: leituras não destrutivas, achados só com metadados, **scan
manifest** de como a sessão foi delimitada, registros de coleta no schema de plugin e `norm_tag`
como **rótulo de análise** — não achado de juízo.

**Não** substitui laudo pericial oficial. Assessoria e peritos acreditados continuam donos das
conclusões jurídicas. Ver [ADR-0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md).

**Relacionados (ecos — leia lá, não copie aqui):**

- Pitch (DPO/jurídico): [PITCH_DPO.pt_BR.md](../pitch/PITCH_DPO.pt_BR.md)
- Cliente técnico / CISO: [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md)
- Página de compliance: [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md)
- Uma linha de produto: [README.pt_BR.md](../../README.pt_BR.md)

A expansão de **checklist de primeiro respondente** está na issue GitHub **#747**.
