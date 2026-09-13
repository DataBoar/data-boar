# Nota de fonte — projetos e guias OWASP

**English:** [OWASP.md](OWASP.md)

Links principais:

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

Por que a fonte ajuda:

- Baseline de segurança de aplicação amplamente adotada.
- Checklists acionáveis para autenticação, sessão, transporte, validação e logging.

Como consumimos:

- Como checklist estruturado para revisão e triagem de backlog.
- Preferir fatias estreitas e testáveis (exemplo: um controle mapeado a um teste ou workflow).

Cuidados:

- Não forçar orientação genérica de web em módulos que não são web.
- Manter o escopo proporcional ao estágio atual do roadmap.

## Guia OWASP de segurança e privacidade em IA — OWASP AI Exchange

- Primário: [visão geral de segurança em IA da OWASP](https://owaspai.org/docs/ai_security_overview/)
- Relevância: o Exchange **documenta** ataques de privacidade em IA (inferência de pertinência / *membership inference*, inversão de modelo, vazamento de dados de treinamento) e discute mitigações como minimizar dados e ofuscar dados de treinamento. O Data Boar pode apoiar um **inventário preventivo** de PII em repositórios candidatos a treino e sistemas relacionados. **Não** é detector de membership inference nem de inversão de modelo, e **não** é “o” controle dessa classe de ataques.
- Como consumir: usar como referência de **posicionamento** ao varrer conjuntos de treinamento ou data lakes que possam alimentar modelos. **Não** substitui o threat model do produto, uma avaliação de sistema de IA nem engenharia de privacidade acreditada.
- Cuidados: só **inspiração / alinhamento** — não é certificação OWASP, não é conformidade com o EU AI Act, não substitui [ADR-0025](../../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) (inventário vs conclusão jurídica).
