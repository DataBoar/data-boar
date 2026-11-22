# Prova OneDrive pessoal via Graph delegado — Fase 0 (#2260)

**Data:** 2026-11-18 (início da varredura UTC `2026-11-18T12:37:26`).

**Issue:** [#2260](https://github.com/DataBoar/data-boar/issues/2260) — prova real no **OneDrive pessoal** pelo leitor `sharepoint_online` do Data Boar (não só sonda fora do produto).

Evidência do que foi executado — **não** conclusão jurídica.

| Campo | Valor |
| ----- | ----- |
| Instância | Demo **apresentação** (`apresentacao.dashboard.net.br`), sem reset de 30 min |
| Versão no export | `1.8.1` (pacote demo, ambiente `lab` no relatório) |
| `session_id` | `c001d83a80c8_20261118_123726` |
| Conector | `sharepoint_online`, delegado, `tenant: consumers`, `drive: me`, escopos `Files.Read` + `offline_access` |

Dois alvos: pasta `/Documents` (72 achados em planilha) e `/Attachments` (1 achado); **73** linhas com prefixo `onedrive:` na aba **Filesystem findings**. Conteúdo de arquivos e nomes reais **não** entram no Git.

Confirmação: `GET https://apresentacao.dashboard.net.br/findings` (mesmo `session_id`, achados filesystem OneDrive) + Excel do operador no disco local.

**Provado:** OneDrive pessoal via conector Boar em Graph de produção (2026-11-18). **Não provado:** SharePoint Online (sites), tenant corporativo, modo app-only, consentimento multitenant verificado.

Detalhes em inglês: [m365_graph_onedrive_delegated_2260_2026-11-18.md](m365_graph_onedrive_delegated_2260_2026-11-18.md).