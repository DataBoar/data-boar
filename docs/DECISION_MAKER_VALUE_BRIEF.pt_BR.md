# Resumo de valor para decisores

**English:** [DECISION_MAKER_VALUE_BRIEF.md](DECISION_MAKER_VALUE_BRIEF.md)

Este resumo ajuda liderança, jurídico, conformidade e segurança a avaliar o Data Boar sem promessas indevidas.

## Posicionamento em uma frase

Data Boar é uma plataforma técnica configurável de descoberta e suporte a evidências que ajuda organizações a localizar e classificar possíveis exposições de dados pessoais e sensíveis em fontes heterogêneas.

## O que é e o que não é

- **É**
  - Um motor de descoberta e mapeamento para inventário de dados e priorização de remediação.
  - Um fluxo de relatório orientado a metadados (achados, norm tags, contexto de tendência) para governança.
  - Uma ponte entre operação de TI e processos de revisão de conformidade/jurídico.
- **Não é**
  - Um mecanismo de decisão jurídica ou aconselhamento legal.
  - Um órgão certificador de ISO, SOC ou conformidade regulatória.
  - Um substituto para DPO, escritório jurídico ou auditoria formal.

## Modelo de responsabilidade compartilhada

- **Data Boar**
  - Executa varreduras configuradas nos alvos aprovados.
  - Produz achados técnicos e artefatos operacionais de evidência.
  - Suporta linguagem alinhada a normas por perfis de configuração.
- **Organização cliente**
  - Define escopo lícito, base legal e aceitação de risco.
  - Aprova credenciais, retenção e governança de acesso.
  - Interpreta os achados para decisões jurídicas/regulatórias.

## Valor por segmento

### Pequenas empresas (TI enxuta)

- Visibilidade rápida de exposição de alto risco com overhead operacional controlado.
- Saídas práticas para priorização imediata de remediação.
- Adequado quando o time precisa evoluir sem plataforma enterprise completa.

### Médio porte (pressão crescente de governança)

- Varreduras repetíveis e evidência de tendência para coordenação entre conformidade e segurança.
- Ponte estruturada entre TI e times jurídico/compliance.
- Adaptação por configuração para crescimento em múltiplas jurisdições.

### Enterprise / setor público

- Suporte técnico de evidências para programas mais amplos de governança e assurance.
- Caminho de integração com controles operacionais mais estritos e ambientes segmentados.
- Modelo compatível com serviços profissionais e evolução por fases.
- **Ciclo de remediação (Enterprise, em breve):** os achados carregam coordenadas precisas — localização do campo, tipo de dado, identificador — para que plugins de remediação de terceiros possam aplicar tokenização, mascaramento ou criptografia de campo no próprio armazenamento; o Data Boar faz uma nova varredura para confirmar. O ciclo completo: "scan once, remediate precisely, prove it".

## Dados de crianças e menores — profundidade deliberada de produto

Exposição ligada a menores é uma **trilha de detecção de primeira classe**, não um detalhe de marketing: limiares de idade configuráveis, **re-amostragem** opcional mais profunda em banco quando a coluna parece DDN ou idade, **cruzamento** com achados de identificador ou saúde na mesma tabela ou caminho de filesystem, e recomendações com **norm tags** no Excel alinhadas ao **LGPD Art. 14** e ao **GDPR Art. 8**. **Amostras YAML** com vocabulário voltado aos EUA (ex.: contexto COPPA) apoiam **linguagem de inventário** para revisão jurídica — **não** fazem checagem de consentimento parental nem verificação legal de idade.

- Guia do operador: [MINOR_DETECTION.pt_BR.md](MINOR_DETECTION.pt_BR.md) ([EN](MINOR_DETECTION.md))
- Mapa por preocupação (bloco de menores é a primeira tabela): [MAP.pt_BR.md](MAP.pt_BR.md) ([EN](MAP.md))

## Perguntas mínimas para compra

Antes de comprar, confirme:

1. Quais domínios e sistemas entram no primeiro escopo de varredura?
2. Qual audiência consome o primeiro pacote de evidências (TI, DPO, jurídico, diretoria)?
3. Qual prazo é esperado para os primeiros achados acionáveis?
4. Quais controles permanecem fora do escopo da ferramenta e exigem dono paralelo?
5. Qual métrica define valor em 30/60/90 dias?

## Expectativa de pacote de evidências

Resultados típicos incluem:

- Achados por fonte e padrão com contexto de sensibilidade.
- Linguagem de recomendação com norm tags para triagem.
- Visibilidade de tendência entre sessões.
- Artefatos operacionais de rastreabilidade.

Esses resultados apoiam governança e preparo de auditoria; isoladamente, não provam conformidade legal.

## Documentação relacionada

- [MINOR_DETECTION.pt_BR.md](MINOR_DETECTION.pt_BR.md) ([EN](MINOR_DETECTION.md)) — limiares, cruzamento, amostras
- [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md) ([EN](COMPLIANCE_AND_LEGAL.md))
- [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) ([EN](COMPLIANCE_FRAMEWORKS.md))
- [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md) ([EN](COMPLIANCE_TECHNICAL_REFERENCE.md))
- [SECURITY.pt_BR.md](SECURITY.pt_BR.md) ([EN](SECURITY.md))
- [README.pt_BR.md](README.pt_BR.md) ([EN](README.md))
- [use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md](use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md) ([EN](use-cases/USE_CASE_SCAN_AND_REMEDIATE.md)) — pipeline de remediação Enterprise com trilha de auditoria (em breve; use-case ilustrativo)
- [use-cases/USE_CASE_TOKENIZED_FINDINGS.pt_BR.md](use-cases/USE_CASE_TOKENIZED_FINDINGS.pt_BR.md) ([EN](use-cases/USE_CASE_TOKENIZED_FINDINGS.md)) — compartilhar relatórios de achados sem expor PII em claro (em breve; use-case ilustrativo)
