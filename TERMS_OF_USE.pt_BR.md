# Termos de uso e política de uso aceitável — Data Boar

**English:** [TERMS_OF_USE.md](TERMS_OF_USE.md)

_Atualizado em: 2026-05-20_

## 1. Licença de código aberto

O código-fonte do Data Boar está disponível sob a licença indicada no arquivo
`LICENSE` neste repositório. Seus direitos de usar, modificar e distribuir o
software são regidos por essa licença.

Este documento complementa a licença do software com orientações de uso
específicas à natureza desta ferramenta.

## 2. O que você pode fazer (edição Community)

Com a edição Community (open-core) você pode:

- Executar o Data Boar em sistemas e dados **dos quais você é titular ou está autorizado a varrer**
- Usar resultados de varredura em relatórios de conformidade, auditorias e avaliações internas
- Modificar e estender o código-fonte nos termos da licença do projeto
- Implantar o Data Boar internamente sem custo, inclusive em organização comercial

## 3. O que você não pode fazer (todos os níveis)

Independentemente do nível de licença, você **não** pode usar o Data Boar para:

- **Varrer sistemas ou dados sem autorização** do titular do sistema ou do controlador de dados aplicável
- **Fazer vigilância encoberta de colaboradores** — varrer dispositivos pessoais ou dados pessoais de empregados sem o conhecimento deles e sem base legal válida
- **Contornar obrigações legais** — usar o Data Boar para localizar e destruir dados pessoais em resposta a investigação regulatória ou ordem de preservação (*litigation hold*)
- **Revender** a edição Community como produto comercial concorrente sem cumprir a licença de código aberto
- **Deturpar achados** — apresentar resultados de varredura do Data Boar como certificação jurídica completa de conformidade

## 4. Uso comercial e níveis de licenciamento

Entregar resultados de varredura do Data Boar a terceiros como parte de serviço pago (consultoria,
auditoria, MSSP) exige no mínimo uma **licença Pro**. Veja [docs/SUBSCRIPTION_TIERS.md](docs/SUBSCRIPTION_TIERS.md),
[docs/LICENSING_SPEC.md](docs/LICENSING_SPEC.md) e [docs/LICENSING_OPEN_CORE_AND_COMMERCIAL.md](docs/LICENSING_OPEN_CORE_AND_COMMERCIAL.md).

Usar o Data Boar em vários ambientes de clientes exige no mínimo uma **licença Partner**.

## 5. Funcionalidades próximas a vigilância

Funcionalidades que varrem artefatos de navegador, formatos proprietários legados de escritório e outros
caminhos de mídia rica listados em [docs/SUBSCRIPTION_TIERS.md](docs/SUBSCRIPTION_TIERS.md)
(por exemplo capturas de tela ou áudio quando habilitados na sua build) estão restritas a níveis
licenciados e exigem confirmação explícita do operador em tempo de execução.

Ao habilitar esses recursos, você declara que:

1. Possui base legal válida (LGPD Art. 7, GDPR Art. 6 ou equivalente) para a varredura
2. Se estiver varrendo dados de empregados, cumpriu os requisitos de direito trabalhista aplicáveis sobre monitoramento no seu ordenamento
3. Manterá os resultados da varredura apenas pelo tempo exigido por lei e os protegerá de forma adequada

## 6. Sem garantia; sem promessa de conformidade

O Data Boar é fornecido "no estado em que se encontra", sem garantia de qualquer tipo. Os resultados são probabilísticos
e podem conter falsos positivos ou falsos negativos. **Não** constituem decisão jurídica
nem certificação de conformidade com LGPD, GDPR ou qualquer outra norma.

Sempre envolva assessoria jurídica qualificada antes de decidir com base em resultados de varredura.

## 7. Divulgação responsável

Se você descobrir vulnerabilidade de segurança no Data Boar, relate pelo processo descrito em
`SECURITY.md`. **Não** abra Issue pública no GitHub para vulnerabilidades de segurança.

## 8. Alterações a estes termos

Podemos atualizar este documento quando o produto ou o modelo de licença mudarem de forma relevante.
Confira a data **Atualizado em** e o histórico em git deste arquivo.

## 9. Contato

Abra uma [issue no GitHub](https://github.com/FabioLeitao/data-boar/issues) para
perguntas gerais. Para licenciamento comercial, contate o mantenedor pelo GitHub.

---

_Estes termos são um guia de boa-fé sobre uso adequado. Não substituem a licença do software em
`LICENSE` nem acordo comercial assinado._
