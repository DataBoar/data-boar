# Pitch DPO e jurídico — litígio, custódia e assessoria (Brasil)

**English:** [PITCH_DPO_AND_LEGAL.md](PITCH_DPO_AND_LEGAL.md) · **Índice:** [INDEX.pt_BR.md](INDEX.pt_BR.md)

**Público:** DPOs em modo incidente, litigantes, oficiais de compliance e sócios de escritório que precisam de **artefatos de inventário defensáveis** — não outro panorama de operação de privacidade.

**Companheiro, não duplicata:** linguagem de programa (base legal, DSAR, menores, sinais multinacionais) está em [PITCH_DPO.pt_BR.md](PITCH_DPO.pt_BR.md). Esta página é o ângulo de **litígio e cadeia de custódia**. Primer técnico canônico: [FORENSICS_AND_EVIDENCE_PRIMER.pt_BR.md](../primers/FORENSICS_AND_EVIDENCE_PRIMER.pt_BR.md). Teto jurídico não técnico: [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md).

---

## O problema (gancho de abertura)

Um funcionário é desligado. Segurança suspeita que uma caixa de e-mail ou um compartilhamento foi copiado para conta pessoal. O notebook ainda está na mesa. Alguém de TI reinicia a máquina “para impedir mais dano”, entra com a própria conta, abre pastas na mão, cola capturas de tela no chamado e não registra **quem** mexeu no equipamento, **quando**, nem **com qual ferramenta**.

O que essa sequência faz de fato: rastros voláteis desaparecem, a estação vira **peça contaminada**, e a assessoria herda uma história que não sobrevive a um questionamento sério — administrativo ou penal. O vazamento pode ser verdadeiro. O **pacote de prova** já está quebrado.

**O que o Data Boar pode contribuir antes desse reboot** (se os estoques relevantes forem **alvos configurados**): uma passagem de descoberta **não destrutiva, somente leitura**; um `scan_manifest_*.yaml` com versão do produto, id de sessão, janela UTC, amostragem/timeouts e um **hash do escopo configurado**; Excel e Markdown executivo opcional com **contagens**, não PII em massa. Isso é **evidência de inventário que você anexa** ao *seu* pacote. **Não** é captura de RAM, imagem de disco nem hold de caixa de e-mail. Não reinicie primeiro se a missão ainda é “onde dados pessoais estavam nestes sistemas?”.

---

## O que DPOs e advogados precisam saber

- **LGPD / ANPD.** Trabalho administrativo com a [Autoridade Nacional de Proteção de Dados (ANPD)](https://www.gov.br/anpd/pt-br) espera **inventário documentado** de dados pessoais — não um slide de boas intenções. O Data Boar produz **artefatos de sessão repetíveis** para o escritório mostrar *o que foi varrido, quando e com quais limites*. **Não** decide notificabilidade nem redige o protocolo.
- **Processo penal (CPP).** A Lei 13.964/2019 inseriu um quadro **legal de cadeia de custódia** para evidência digital (arts. **158-A** a **158-F**). Texto oficial: [Código de Processo Penal (Planalto)](https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm). Este produto **não** implementa esse estatuto. Um manifesto de varredura pode **entrar** no pacote de custódia (quem/o quê/quando/versão da ferramenta/hash de escopo); **não** substitui lacre, perito habilitado nem as regras do juízo.
- **ISO/IEC 27037:2012.** Linguagem internacional de identificação, coleta e preservação de evidência digital ([catálogo ISO](https://www.iso.org/standard/44381.html)). Compre a norma para o texto oficial. O Data Boar cobre **coleta delimitada + documentação**, não imageamento forense.
- **Conceitos de e-discovery.** ISO/IEC 27050-1 aponta linguagem de processo de ESI ([ISO 78647](https://www.iso.org/standard/78647.html)) — o hold e a produção continuam **do seu lado**.

**Integridade (honesta):** hashes da classe SHA-256 neste produto descrevem **escopo configurado / bytes do artefato desde o hash**. **Não** são cadeia de custódia jurídica completa. **ed25519** neste repositório assina **JWTs de licença** e **atestação do inventário de ADRs** — **não** cada `scan_manifest`. Não diga em juízo que o YAML está assinado por SSH. O §5 do primer é a fonte da verdade.

---

## O que o Data Boar não é

Conforme o **[ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)** (evidência e inventário, **não** motor de conclusão jurídica):

- **Não** substitui laudo pericial oficial.
- **Não** é motor de parecer jurídico (sem “violação”, sem “precisa notificar”, sem juízo de admissibilidade).
- **Não** é suíte DFIR, write-blocker nem lacre de peça em juízo.

**O que oferece:** artefatos de inventário de **grau forense** (achados só de metadados, trilha de sessão, manifesto) para **apoio a compliance** e **pasta da assessoria**. O [ADR 0027](../adr/ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md) é o limite documental das faixas comerciais (open core vs Pro/Enterprise nos docs públicos de licença — **sem** preço de cliente nesta página).

Responsabilidade compartilhada: [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](../DECISION_MAKER_VALUE_BRIEF.pt_BR.md). Saídas e manifestos: [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md).

---

## Diferenciais (scanner genérico vs este produto)

| Aspecto                    | Scanner genérico típico                  | Data Boar                                                                                                         |
| -------                    | -----------------------                  | ---------                                                                                                         |
| Cadeia de custódia         | Em geral nenhuma além de um CSV          | `scan_manifest` + id de sessão + janela UTC + **hash de escopo** — **insumo** de custódia, não lacre              |
| Alinhamento jurídico       | Em geral não declarado                   | **Ponteiros** aos arts. 158-A–F do CPP e à ISO/IEC 27037 — **linguagem de alinhamento**, não certificado jurídico |
| Postura de admissibilidade | Conveniência operacional                 | **Grau de apoio a evidência**: método e limites documentados; a assessoria argumenta admissibilidade              |
| Trilha de auditoria        | Muitas vezes um log que ninguém reproduz | SQLite da sessão + artefatos de relatório + bullets de auditoria — **repetível**, não “imutável via SSH”          |

---

## Públicos nesta página

### DPO

Use este deck quando o relógio é **incidente** ou conversa com a **ANPD**: preservar **inventário de onde dados semelhantes a PII estavam**, com limites de amostragem por escrito. Mantenha [PITCH_DPO.pt_BR.md](PITCH_DPO.pt_BR.md) para direitos do dia a dia e menores.

### Advogado (litigante)

**Locais e classes** de PII como **indicadores técnicos** para estratégia — não ESI pronto para produção. Combine com sua carta de hold e, quando evidência digital penal/administrativa estiver em jogo, com o **seu** rito de custódia do CPP. O processo de e-discovery continua ISO/IEC 27050-1 **do seu lado**.

### Oficial de compliance

A história **ISO/IEC 27001 + 27701 + LGPD** é **governança + linguagem de PIMS + lei brasileira** — o Data Boar é **insumo de evidência** para essa tríade, não certificação. Veja [PITCH_COMPLIANCE_OFFICER.pt_BR.md](PITCH_COMPLIANCE_OFFICER.pt_BR.md) para responsabilidade e DD de M&A.

### Sócio de escritório

**Enquadramento comercial:** menos incidentes do tipo “olhamos e tiramos print”; primeiro pacote mais rápido para o workshop DPO/CISO; menos risco de **contaminação autoinfligida**. ROI é **redução de risco e tempo até inventário defensável**, não vitória prometida em juízo. Clientes nomeados e honorários ficam fora desta página pública ([ADR 0027](../adr/ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md)).

---

## Próximo passo

- **Privacidade operacional (DSAR, menores):** [PITCH_DPO.pt_BR.md](PITCH_DPO.pt_BR.md)
- **Responsabilidade empresarial:** [PITCH_COMPLIANCE_OFFICER.pt_BR.md](PITCH_COMPLIANCE_OFFICER.pt_BR.md)
- **Evidência de segurança:** [PITCH_CISO.pt_BR.md](PITCH_CISO.pt_BR.md)
- **Primer do integrador:** [FORENSICS_AND_EVIDENCE_PRIMER.pt_BR.md](../primers/FORENSICS_AND_EVIDENCE_PRIMER.pt_BR.md)
- **Página jurídica (não reimprimir aqui):** [COMPLIANCE_AND_LEGAL.pt_BR.md](../COMPLIANCE_AND_LEGAL.pt_BR.md)
