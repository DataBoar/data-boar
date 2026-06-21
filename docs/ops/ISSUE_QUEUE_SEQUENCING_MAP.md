---
# Issue Queue Sequencing Map
<!-- auto-maintained: refresh when new issues are added or NÃO INICIAR chains change -->
**Última atualização:** 2026-06-21
**Total open issues:** 145

```mermaid
flowchart TD

subgraph WAVE_174["WAVE v1.7.4 (7 issues)"]
  i426["#426 CHANGELOG structure Unreleased"]:::p3
  i421["#421 LICENSE copyright year"]:::p2
  i422["#422 NOTICE copyright year"]:::p2
  i641["#641 man pages bump 1.7.4"]:::p2
  i425["#425 README 1.7.4 checklist"]:::p2
  i640["#640 CHANGELOG wave docs/security"]:::p2
  i406["#406 🚧 release gate checklist"]:::p2
  i426 --> i640
  i421 --> i406
  i422 --> i406
  i641 --> i406
  i425 --> i406
  i640 --> i406
end

subgraph WAVE_175["WAVE v1.8.0-beta (102 issues — 6 fases)"]

  subgraph U0["Segurança U0"]
    i560["#560 gatekeeper-audit Python puro"]:::p2
    i545["#545 tamper protection opt-in Phase 2-3"]:::p2
  end

  subgraph U1a["Plugin Chain U1"]
    i606["#606 feat(core): plugin hook infrastructure"]:::p0
    i649["#649 remediation manifest JSON export"]:::p2
    i611["#611 PLUGIN_SDK.md"]:::p1
    i606 --> i649
    i606 --> i611
  end

  subgraph U1b["Governance Lens U1→U2"]
    i539["#539 Governance Lens Phase A"]:::p2
    i540["#540 Governance Lens Phase B"]:::p2
    i541["#541 Governance Lens Phase C"]:::p2
    i542["#542 Governance Lens Phase D"]:::p2
    i543["#543 Governance Lens Phase E Enterprise"]:::p2
    i539 --> i540
    i540 --> i541
    i541 --> i542
    i540 --> i543
    i539 --> i542
  end

  subgraph U1c["Higiene CI/Sec U1"]
    i490["#490 CVE-2026-3219 pip-audit check"]:::p2
    i389["#389 remove CVE suppressor"]:::p2
    i427["#427 SECURITY.md CVE triage"]:::p2
    i387["#387 rust-ci.yml toolchain"]:::p2
    i388["#388 Zizmor enforce on push"]:::p2
    i548["#548 REST connector SSRF token_url"]:::p2
    i490 --> i389
  end

  subgraph U2["Enterprise/Commercial U1→U2"]
    i643["#643 ENT subscription roadmap"]:::p1
    i650["#650 value-brief Enterprise hook"]:::p2
    i644["#644 norm_tags plugin_schema"]:::p2
    i623["#623 Python 3.14 CI matrix"]:::p1
    i546["#546 Python version matrix fix"]:::p2
  end

  subgraph U3["Phase E adapters U3"]
    i531["#531 Nagios/Cacti adapter"]:::p2
    i533["#533 XLSX adapter"]:::p2
    i534["#534 ServiceNow CMDB adapter"]:::p2
    i535["#535 iTop/Movidesk adapter"]:::p2
    i536["#536 ODS adapter"]:::p2
  end

  subgraph TAIL["TAIL P2 U:- (63 issues — docs/compliance-samples/man-pages)"]
    tail["63 issues (ver backlog)"]:::p3
  end

end

subgraph BACKLOG["BACKLOG (36 issues — sem sprint)"]
  i381["#381 db/ Ruff/Bandit plan"]:::p3
  i382["#382 mypy strictness roadmap"]:::p3
  i381 --> i382
  backlog_tail["+ 34 issues"]:::p3
end

i406 -->|"🚧 NÃO INICIAR ANTES DE #406 FECHADA"| i606

classDef p0 fill:#c0392b,color:#fff
classDef p1 fill:#e67e22,color:#fff
classDef p2 fill:#2980b9,color:#fff
classDef p3 fill:#7f8c8d,color:#fff
```

## Contagens

| Dimensão | Distribuição |
|---|---|
| P0/P1/P2/P3 | 2/6/99/38 |
| v1.7.4 / v1.8.0-beta / backlog | 7/102/36 |
| U0/U1/U2/U3/sem U | 2/9/18/5/111 |
| G3/G2/G1/sem G | 2/4/1/138 |
---
