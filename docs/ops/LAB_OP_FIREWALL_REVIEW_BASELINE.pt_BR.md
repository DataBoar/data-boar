# Baseline de revisao de firewall LAB-OP (publico-safe)

**English:** [LAB_OP_FIREWALL_REVIEW_BASELINE.md](LAB_OP_FIREWALL_REVIEW_BASELINE.md)

## Objetivo

Registrar uma baseline revisavel e util para estudo da postura de firewall sem expor detalhes privados de inventario (hostnames, topologia LAN, endpoints de gestao ou segredos).

## Escopo

- Revisao em modo leitura de configuracoes de firewall e console.
- Nenhuma acao destrutiva (`apply`, `reset`, `root`) durante a revisao.
- Achados mapeados para fases de remediacao priorizadas.

## Retrato publico-safe dos achados

### Forcas atuais

- Perimetro WAN em comportamento default-deny.
- Segmentacao interna ativa (isolamento + excecoes de allow explicitas).
- Camadas de seguranca/filtro de conteudo habilitadas em baseline.

### Riscos prioritarios (generico)

- **P1:** observabilidade de regras de drop pode melhorar (logging e auditoria).
- **P1:** possiveis regras stale/orfas precisam validacao de ownership.
- **P1:** baseline de hardening de acesso administrativo pede verificacao periodica explicita.
- **P2:** controles de saida (egress) de segmentos menos confiaveis podem ser apertados.
- **P2:** nomenclatura e ownership de aliases/grupos podem ficar mais claros.

## Modelo de score

- **Score atual:** **74/100**
- **Score projetado apos remediacao:** **82-88/100**

O racional privilegia: postura deny no perimetro, qualidade da segmentacao, hardening do plano administrativo, higiene de regras e observabilidade operacional.

## Rollout recomendado (ordem segura)

### Fase A - sem downtime

1. Habilitar e validar logging das regras de drop.
2. Auditar regras suspeitas/stale e desabilitar antes de remover.
3. Registrar ownership e finalidade de excecoes de allow.

### Fase B - hardening do plano administrativo

1. Verificar baseline de acesso de gestao (metodo, restricao de origem, exposicao minima).
2. Manter caminhos de acesso remoto desnecessarios desabilitados por padrao.

### Fase C - hardening de egress controlado

1. Migrar segmentos de menor confianca para allow-list explicita de egress.
2. Manter rollback predefinido por lote de regras.

## Acesso SSH para auditoria profunda (publico-safe)

Use quando a GUI nao expuser completamente detalhes do plano administrativo (por exemplo status/porta/restricao de origem do SSH daemon).

1. Configurar um alias SSH na estacao do operador (`~/.ssh/config`).
2. Confirmar que autenticacao por chave funciona (`ssh <alias> 'whoami'`).
3. Manter menor privilegio por padrao:
   - iniciar com comandos somente leitura;
   - preferir checagens `sudo -n` pontuais em vez de shell root amplo.
4. Guardar valores especificos de host e comandos exatos apenas em `docs/private/homelab/` (gitignored).
5. Pedir para o assistente executar a auditoria profunda no terminal integrado usando esse alias.

Nos docs publicos deve ficar apenas o fluxo. Nunca publicar hostname, IP LAN, URL de gestao, chaves ou tokens.

### Automacao reutilizavel

- Script: `scripts/unifi-ssh-deep-audit.ps1`
- Entrada: `.env` privado (ex.: `docs/private/homelab/.env.ssh.LAB-ROUTER-01-se-cursor.local`)
- Saida: log em `docs/private/homelab/reports/`

Exemplo:

```powershell
.\scripts\unifi-ssh-deep-audit.ps1 -EnvFile "docs/private/homelab/.env.ssh.LAB-ROUTER-01-se-cursor.local"
```

## Politica de split private/public

- **Verdade privada:** `docs/private/homelab/LAB_OP_FIREWALL_REVIEW_2026-04-05.pt_BR.md`
- **Abstracao publica:** este runbook (generico, sem topologia sensivel).

Use o documento privado para operacao e incidentes, e este publico para revisao de processo, onboarding e material de estudos.

## Passo a passo concreto (habilitar + validar SSH)

> Estado validado nesta sessao: `unifi.local` resolve e a porta 22 responde, mas a autenticacao falha com `Permission denied (publickey,keyboard-interactive)`.

1. Abrir UniFi com conta admin no caminho exato: `System > Control Panel > Console > SSH`.
2. Marcar `Enable SSH`.
3. Executar `Change Password` (ou registrar chave publica na opcao equivalente).
4. Aplicar mudancas e aguardar provisioning.
5. Validar no terminal do operador:
   - `ssh -o BatchMode=yes -o ConnectTimeout=8 LAB-ROUTER-01-se-cursor "echo SSH_OK && whoami"`
6. Se falhar em autenticacao, checar usuario efetivo e auth method:
   - `ssh -G LAB-ROUTER-01-se-cursor | findstr /R "^user "`
   - confirmar `User` correto no bloco do alias em `~/.ssh/config`;
   - confirmar se o modo esperado e senha ou chave.
7. Se falhar em conectividade (timeout/refused), revisar:
   - SSH habilitado no alvo certo;
   - porta configurada (22 ou custom);
   - ACL/firewall entre estacao e gateway.

Somente depois do passo 5 funcionar vale executar auditoria profunda de hardening.
