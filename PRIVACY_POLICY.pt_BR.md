# Política de privacidade — Data Boar

**English:** [PRIVACY_POLICY.md](PRIVACY_POLICY.md)

_Atualizado em: 2026-05-20_

## O que é o Data Boar

O Data Boar é um *scanner* de código aberto para descoberta de dados sensíveis e apoio à conformidade LGPD/GDPR.
Ele roda **inteiramente na sua infraestrutura**. Não há serviço em nuvem do produto, *phone-home*,
telemetria nem conta obrigatória para usar a edição Community.

## O que esta política cobre

Esta política descreve:

1. Que informações este **repositório e projeto no GitHub** coletam (se coletam).
2. Que informações a **ferramenta Data Boar** coleta quando você a executa.
3. Seus direitos em relação a dados que eventualmente guardemos.

## 1. O repositório no GitHub

Este repositório está hospedado no [GitHub](https://github.com). Ao visitá-lo, a política de privacidade
do GitHub se aplica à sua interação com a plataforma (cookies, análises etc.).
Não controlamos a coleta de dados do GitHub.

Quando você abre uma Issue, envia um Pull Request ou comenta, seu usuário do GitHub
e o conteúdo que enviou ficam visíveis para mantenedores e para o público como parte do
histórico de colaboração em código aberto.

Não mantemos banco de usuários separado, lista de newsletter nem plataforma de análise própria para
este repositório.

## 2. A ferramenta Data Boar (o que roda na sua máquina)

Política revisada em relação à linha de produto **1.7.4-rc** no repositório público (varredura local,
painel opcional, conectores por nível de licença). Se você usa outra build, compare
[docs/SUBSCRIPTION_TIERS.md](docs/SUBSCRIPTION_TIERS.md) e as notas de release.

O Data Boar varre **os seus** bancos, filesystems e documentos em busca de dados pessoais.
Ele **não**:

- Envia resultados de varredura, conteúdo de arquivos ou metadados a servidor externo
- Contata os mantenedores do Data Boar durante ou após a varredura
- Coleta estatísticas de uso ou telemetria
- Exige conexão com a internet para rodar (edição Community)
- Cria contas de usuário nem armazena credenciais além do que você configurar explicitamente

Os resultados são gravados **localmente** no caminho de saída que você definir.
Seus dados não saem da sua máquina salvo se você exportar ou compartilhar explicitamente.

### Níveis licenciados (Pro, Partner, Enterprise)

Se você usar *token* de licença assinado (JWT), a validação é feita **localmente**
com a chave pública embutida. Não há chamada a servidor de licença.
O próprio *token* contém apenas: nome do nível, data de expiração e assinatura criptográfica.
Não contém dados pessoais sobre você.

### Autenticação opcional no painel (quando você habilita)

Se você implantar o painel web com autenticação, credenciais e metadados de sessão ficam na
infraestrutura que você controla. WebAuthn e RBAC são caminhos opcionais de configuração do
operador documentados no guia técnico; não são obrigatórios para varreduras CLI da edição Community.

### Avaliação de maturidade (questionário local)

O fluxo de avaliação de maturidade grava respostas em banco SQLite local na sua máquina.
Não envia respostas aos mantenedores do Data Boar salvo se você exportar ou compartilhar.

## 3. O que coletamos (mínimo)

| O quê | Onde | Por quê |
| --- | --- | --- |
| Conteúdo de Issues / PRs | GitHub (público) | Relatos de bug e contribuições |
| E-mail se nos contatar diretamente | Somente e-mail do mantenedor | Suporte, parcerias |

Não vendemos, intermediamos nem compartilhamos essas informações com terceiros.

## 4. Data Boar e LGPD / GDPR

O Data Boar é uma ferramenta para **ajudar você a cumprir** LGPD, GDPR e normas semelhantes.
Não toma decisões de conformidade por você. Os achados de varredura são insumos
ao seu próprio processo de avaliação; **não** constituem assessoria jurídica.

Se você usar o Data Boar para tratar dados em nome de terceiros (como consultor ou integrador),
você é o controlador ou operador dessa atividade.
Consulte seu assessor jurídico sobre obrigações aplicáveis.

## 5. Funcionalidades próximas a vigilância (Pro e Enterprise)

Alguns recursos em níveis licenciados (por exemplo artefatos de navegador, formatos proprietários
legados de escritório e outros caminhos de mídia rica em [docs/SUBSCRIPTION_TIERS.md](docs/SUBSCRIPTION_TIERS.md))
podem detectar dados pessoais em artefatos de terceiros além do operador.

Você precisa de **base legal** nos termos do art. 7 da LGPD (ou art. 6 do GDPR) antes de varrer dados
de terceiros. O contrato de licença do Data Boar (EULA) exige que você declare
ter essa base como condição de uso.

## 6. Dados de menores

O Data Boar não se dirige a menores de 18 anos nem se destina a uso por crianças.
Não coletamos dados de menores de forma intencional.

## 7. Alterações a esta política

Podemos atualizar esta política quando o produto mudar de forma relevante (por exemplo, se surgir edição SaaS).
Atualizaremos a data **Atualizado em** acima e registraremos a mudança no changelog do repositório.

## 8. Contato

Para questões de privacidade sobre este projeto:

- Abra uma [issue no GitHub](https://github.com/FabioLeitao/data-boar/issues) (preferível para perguntas gerais)
- Para assuntos sensíveis, contate o mantenedor diretamente pelo e-mail indicado no perfil do GitHub

---

_O Data Boar é um projeto de código aberto. Esta política de privacidade é oferecida de boa-fé
como transparência. Não é um contrato jurídico._
