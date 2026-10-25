# Dispositivos móveis como ferramentas do operador (iOS + Android)

**Objetivo:** Usar **telefone e tablet** como **console do operador** na rede de casa/lab (UniFi, GitHub, Bitwarden, SSH na LAN, smoke da UI web, fotos de placas de modelo para notas **privadas**).

**Documento completo (EN):** [HOMELAB_MOBILE_OPERATOR_TOOLS.md](HOMELAB_MOBILE_OPERATOR_TOOLS.md)

**Relacionado:** [OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md](OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md) · [OPERATOR_SECRETS_BITWARDEN.pt_BR.md](OPERATOR_SECRETS_BITWARDEN.pt_BR.md) · [HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.pt_BR.md](HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.pt_BR.md)

## Resumo rápido

| Uso                                                                               | Dispositivo                                                                                                         |
| ---                                                                               | -----------                                                                                                         |
| **UniFi** (clientes, Wi‑Fi, alertas)                                              | iPhone ou tablet Android **recente**                                                                                |
| **GitHub** (Actions falharam, Dependabot)                                         | iPhone (app)                                                                                                        |
| **Bitwarden / TOTP**                                                              | iPhone 11 + tablet Android; **não** como dispositivo principal se for iPad **muito antigo** (sem apps atuais)       |
| **App solar** (Shine / fabricante)                                                | iPhone / Android conforme suporte da app                                                                            |
| **SSH** na LAN (VM, Pi)                                                           | iPhone / Android com cliente atualizado                                                                             |
| **Smoke** do dashboard Data Boar (`:8088` na LAN)                                 | Qualquer um com browser OK; **iPad mini 2** (iOS ~12): Safari para URLs simples na LAN—UI muito moderna pode falhar |
| **Fotos** de etiquetas (UPS, HVAC) → transcrever para **`docs/private/homelab/`** | Inclui **iPad antigo**; **Live Text** não existe no iOS 12—transcrever à mão                                        |

**iPad mini 2 (iOS antigo):** útil para **fotos**, **Wi‑Fi**, **Safari** em páginas **simples** na LAN; **não** contar com apps UniFi/GitHub/Bitwarden atuais. Preferir **iPhone 11** para segredos e notificações.

**Evitar:** expor gestão UniFi ou SSH à **internet** sem VPN; guardar passwords em notas não cifradas.
