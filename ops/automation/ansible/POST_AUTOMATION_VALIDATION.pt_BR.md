## Validação pós-automação (Ansible baseline) — checklist rápido

**Objetivo:** confirmar que a rodada de automação não quebrou login/SSH, que os serviços “baseline” estão operando, e que o host está pronto para auditoria e host-report.

> Política: este checklist **não** deve exigir segredos. Tudo que for host-specific (IPs, usuários, comunidades/credenciais SNMP) fica em `docs/private/`.

---

## 1) Sanidade imediata (não travar acesso)

- **Rede + DNS**

```bash
ip -br a
ip r
getent hosts deb.debian.org
```

- **SSH (se aplicável)**

```bash
sudo systemctl status ssh --no-pager
ss -lntp | sed -n '1,160p'
```

---

## 2) Serviços de hardening (baseline)

```bash
sudo systemctl status ufw fail2ban auditd sshguard usbguard --no-pager
```

- **UFW**

```bash
sudo ufw status verbose
```

- **Fail2ban (jail sshd)**

```bash
sudo fail2ban-client status sshd
```

- **Auditd**

```bash
sudo auditctl -s
sudo augenrules --check 2>/dev/null || true
```

- **USBGuard (nota importante)**

Por padrão, o baseline mantém `usbguard` **desligado** para evitar lock-out de periféricos.

Se você optou por habilitar USBGuard, valide:

```bash
sudo systemctl status usbguard --no-pager
sudo usbguard list-devices
```

### Persistência (LMDE/USBGuard CLI variações)

Algumas builds do `usbguard` **não** têm `reload-rules`, e `usbguard list-rules` pode imprimir regras com prefixo `N:` (ex.: `8: allow ...`).

- **Não** grave `usbguard list-rules` direto em `/etc/usbguard/rules.conf` sem remover o `N:` — isso pode quebrar o daemon no restart.
- Fluxo “à prova de versão” para persistir:

```bash
sudo usbguard generate-policy | sudo tee /etc/usbguard/rules.conf >/dev/null
sudo systemctl restart usbguard
sudo usbguard list-devices --blocked
```

Se você precisa permitir dispositivos específicos de forma persistente, prefira `allow-device -p <id>` (quando suportado) e valide com `list-devices --blocked` vazio.

---

## 3) Pacotes úteis (auditoria + diagnóstico)

```bash
command -v lynis
lynis --version
command -v sysctl
command -v pydf
command -v lnav
command -v ncdu
```

---

## 4) Lynis upstream (opcional)

Se o host clonou o upstream em `/opt/lynis`, valide:

```bash
test -x /opt/lynis/lynis && /opt/lynis/lynis --version || true
```

---

## 5) Host report (mapa mental do LAB-OP)

Na raiz do repo (no host), rode:

```bash
bash scripts/homelab-host-report.sh | tee "homelab_host_report_$(date +%F).log"
```

Se você já configurou o modo privilegiado (`sudoers` restrito), rode:

```bash
bash scripts/homelab-host-report.sh --privileged --deep | tee "homelab_host_report_priv_deep_$(date +%F).log"
```

