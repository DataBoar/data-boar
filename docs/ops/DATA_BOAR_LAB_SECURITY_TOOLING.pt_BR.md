# Data Boar: testes de lab vs ferramentas de segurança no host

**English:** [DATA_BOAR_LAB_SECURITY_TOOLING.md](DATA_BOAR_LAB_SECURITY_TOOLING.md)

## Objetivo

Ambientes **Linux**, **Windows** e **rede** endurecidos costumam usar **firewall**, **controle de acesso obrigatório**, **daemons** de resposta a intrusão e **monitores de integridade**. Isso e correto em producao; ainda pode **bloquear ou confundir** a validacao de **lab** do Data Boar (dashboard/API na LAN, bind mounts do Docker, SSH repetido por automacao, portas de BD em [LAB_SMOKE_MULTI_HOST.pt_BR.md](LAB_SMOKE_MULTI_HOST.pt_BR.md)).

Este runbook **cita** controles comuns, **diz o que em geral precisa mudar** para um teste delimitado, **justifica** e aponta **scripts auxiliares** em `scripts/`. E **generico** (sem hostnames reais, IPs de LAN ou credenciais). Registre desfechos por maquina em **`docs/private/homelab/`** (gitignored).

**Relacionado:** [HOMELAB_VALIDATION.pt_BR.md](HOMELAB_VALIDATION.pt_BR.md) secao 0.1 (acesso LAN) · [LAB_OP_FIREWALL_REVIEW_BASELINE.pt_BR.md](LAB_OP_FIREWALL_REVIEW_BASELINE.pt_BR.md) · [CURSOR_UBUNTU_APPARMOR.pt_BR.md](CURSOR_UBUNTU_APPARMOR.pt_BR.md) · [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md) · [SECURITY.pt_BR.md](../SECURITY.pt_BR.md)

## Principios (lab vs producao)

1. **Preferir regras de liberacao estreitas** (sub-rede de origem + porta de destino + ticket de mudanca com prazo) em vez de **desligar produtos inteiros**.
2. **Bind e escopo:** o Data Boar deve escutar em **`0.0.0.0`** so quando voce **quer** acesso na LAN; combine com **firewall no host** liberando **so clientes do lab**, nao `0.0.0.0/0`.
3. **Reverter:** apos a janela de teste, remover liberacoes temporarias ou voltar perfis/jails ao modo de exigencia, conforme a politica.
4. **Valor para cliente:** a mesma tabela ajuda **suporte** quando o IT do prospecto diz “nao conecta” — da para fazer perguntas objetivas em vez de adivinhar.

## Portas padrao (recap)

| Superficie | Padrao | Notas |
| ---------- | ------ | ----- |
| HTTP API + dashboard | **TCP 8088** | [USAGE.pt_BR.md](../USAGE.pt_BR.md), `api.port` |
| TLS opcional na app | mesma porta | flags de certificado no [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md) |
| Proxy reverso | **443** (tipico) | Se o TLS termina no nginx/Caddy, abra **443** ate o proxy, nao **8088** cru na borda |
| BD de lab / compose | **5432**, **3306**, etc. | [HOMELAB_VALIDATION.pt_BR.md](HOMELAB_VALIDATION.pt_BR.md) secao 4, [LAB_SMOKE_MULTI_HOST.pt_BR.md](LAB_SMOKE_MULTI_HOST.pt_BR.md) |

Scripts auxiliares (opcionais, executados pelo operador):

- **Windows:** `scripts/lab-allow-data-boar-inbound.ps1` — entrada **8088/tcp** no perfil **Private** (ajuste perfil/porta conforme precisar).
- **Linux:** `scripts/lab-allow-data-boar-inbound.sh` — **ufw** ou **firewalld** liberando origem `LAB_LAN_CIDR` (padrao `10.0.0.0/16` — **ajuste** para a sua LAN).

## Matriz: controle, interferencia, ajuste de lab, nota de producao

| Controle | Interferencia tipica com lab do Data Boar | O que mudar (lab) | Por que | Producao / cliente |
| -------- | ------------------------------------------ | ----------------- | ------- | ------------------- |
| **Firewall do Windows Defender** | Bloqueia **entrada** **8088** de outros hosts na LAN | Incluir regra para **TCP 8088** no perfil **rede privada** ou IPs remotos escopados; use `lab-allow-data-boar-inbound.ps1` ou o MMC **Firewall do Windows** | Dashboard/API precisa ser alcancavel na sub-rede do lab | Preferir **escopo por sub-rede**, nao “qualquer”; documentar dono da regra |
| **Firewall no Linux (ufw / firewalld / nftables)** | Igual ao Windows para **8088** e portas de BD | **Permitir** do CIDR da LAN para **8088/tcp**; no smoke de BD, permitir host cliente ate a porta no host do BD | Negacao padrao e normal; liberacao explicita e o menor ajuste | Manter regras **stateful**; nao abrir **8088** para WAN |
| **Roteador / UniFi / ACL de VLAN** | VLAN cliente nao alcanca **8088** do servidor | **Permissao L3** + **DNS** correto se usar nomes; veja [HOMELAB_VALIDATION.pt_BR.md](HOMELAB_VALIDATION.pt_BR.md) secao 0.1 | Segmentacao e intencional; testes precisam de excecao explicita | Mesmo padrao para **clientes** com DMZ ou rede convidada isolada |
| **AppArmor** | **DENIED** em `docker` / `containerd` / caminhos da app, bind mounts, Python em snap | Ver `journalctl` / `dmesg` por **apparmor="DENIED"**; usar modo **complain** em perfil estreito durante diagnostico, ou **overrides locais** (veja [CURSOR_UBUNTU_APPARMOR.pt_BR.md](CURSOR_UBUNTU_APPARMOR.pt_BR.md)) | MAC e por caminho; mounts incomuns disparam perfis | Preferir **perfil ajustado** a desativar tudo |
| **SELinux (Enforcing)** | Rotulos de volume de container, bind de rede | **Boolean** ou **contexto de arquivo** conforme doc da distro | SELinux nega por padrao em familia RHEL | Documentar **contexto** para runbooks de suporte |
| **fail2ban / SSHGuard** | Bloqueio de **SSH** apos conexoes repetidas; jails HTTP se o proxy registra tempestade de 401/404 | **Lista branca** de IPs do lab em `jail.local` / **ignoreip** no firewall; evitar martelar **SSH** com chave errada em scripts | Testes automatizados podem parecer forca bruta | Clientes podem precisar **allowlist** para CI ou hosts de scan |
| **USBGuard** | Bloqueia dispositivos **USB** | **Sem impacto** no Data Boar por rede | So relevante se o conector usar USB para storage | — |
| **AIDE / Tripwire / FIM do Wazuh** | **Alertas** em arquivos sob clone do repo, cache do `uv`, camadas Docker | Esperar **ruido** em `git pull`, `docker build`; ajustar **exclusoes** para dirs de build ou aceitar alertas no lab | Ferramentas de integridade flagam churn | **Nao** “desligar” silenciosamente — **es copiar** exclusoes |
| **auditd / Linux Audit** | Log pesado de **syscall**; possivel **backpressure** | Em geral **sem mudanca**; se politicas negam `exec`, ajustar **regras de audit** so com time de seguranca | Conflito raro salvo negacao estrita de `exec` | Clientes em compliance podem exigir **retencao** de logs |
| **EDR / antivirus (Windows)** | Scan em caminhos **Python** / **Docker**; raro interferir em **bind** | **Exclusoes** para clone de dev e raiz de dados do Docker **so** se a politica permitir | Performance e falsos positivos | Alinhar com IT; espelha dor de **cliente** com EDR |
| **CrowdSec / similar** | Bouncer HTTP bloqueando **8088** | **Lista branca** de origens de lab ou desativar bouncer para **vhost** de teste | Mesma classe do fail2ban | Documentar **API** + dashboard como somente internos |

## SSH automatizado e sudo (expectativas)

Operadores às vezes usam **SSH** do PC de dev para hosts de lab (scripts `lab-op`, Ansible, `git pull` manual). **SSH sem senha** e **`sudo -n`** **não** são garantidos em todo ambiente; o assistente **não** pode assumir sudo **NOPASSWD** nas suas máquinas. Automação **não interativa** **não** consegue completar **`sudo ufw …`** quando a conta exige **senha** a cada chamada — use **sessão SSH interativa**, **Ansible** com vault/`become`, ou **console**.

- Se **`sudo -n ufw status`** falhar, execute os comandos **ufw**/**firewalld** **no console** como root ou com sudo normal.
- **Documente** em notas privadas: qual host recebeu qual regra, data e rollback.

## Checklist para cliente / suporte

Quando “funciona local” mas nao na rede do cliente, pergunte:

1. **Caminho de entrada:** **8088** (ou **443** via proxy) liberado do **posto do operador** ou **sub-rede do scanner** ate o **host da app**?
2. **Bind:** o processo esta em **`0.0.0.0`** (ou interface correta), nao **somente loopback**?
3. **Caminho L3:** algum **ACL de VLAN**, **NSG** ou **firewall no host** no meio?
4. **IDS/IPS:** algum **rate limit** ou **WAF** no mesmo caminho?
5. **Integridade / EDR:** o scan esta atrasando **Docker** ou **Python** na subida?

Registrar respostas no ticket — mesma estrutura do debug interno de lab.
