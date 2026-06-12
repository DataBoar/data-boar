# Planejamento de energia e elétrica do homelab

**Objetivo:** Calcular **consumo total**, **capacidade do UPS** e requisitos de **disjuntor** para as máquinas do homelab documentadas em [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) §9.

**Documento completo (EN, fórmulas e tabelas):** [HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md](HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md)

### Energia solar (PV)

Conta de luz **mais barata ou compensada** **não** elimina a necessidade de planejar **disjuntores, cabos, tomadas e UPS**: a capacidade de cada **circuito** continua a mesma; em muitas instalações **grid-tied**, em uma **falta de rede** as tomadas **não** ficam alimentadas pelo solar sem **bateria e arquitetura de backup** adequados. Ver a seção **Solar / PV** no documento em inglês.

### UniFi “power bank” / SmartPower vs segundo nobreak

Para **tirar o LAB-ROUTER-01-SE** (e talvez o switch) do **Attiv** e **liberar watts**: a Ubiquiti documenta **SmartPower** com **USP-RPS** + cabo **USP** para gateways compatíveis — o **LAB-ROUTER-01-SE** aparece na tabela oficial com até **220 W em 52 V CC** na porta SmartPower (ver [Power Redundancy](https://help.ui.com/hc/en-us/articles/360042834933-Power-Redundancy)). Alternativa simples: **segundo nobreak** só para **stack de rede** (modem + LAB-ROUTER-01 + switch). O RPS/UPS UniFi continua precisando de **tomada AC**; confirme firmware/recursos antes de comprar **UPS 2U**. Detalhes em **§5.2** do documento em inglês.

### Nobreak Intelbras **Attiv 1500 VA** (120 V)

Se **tudo** está ligado nele hoje, o limite relevante costuma ser **potência em watts (W)**, não só **1500 VA**. Na linha Attiv 1500 VA, a ficha técnica Intelbras indica frequentemente **~750 W** de potência ativa máxima (ver **etiqueta** e datasheet do seu SKU). **Planeje ≤ ~600 W** em uso contínuo para margem; **8 tomadas** não aumentam esse teto. **Ar-condicionado** (condensadora) em geral **não** deve ir num nobreak pequeno tipo mesa. Estratégias: separar cargas críticas, segundo nobreak, ou UPS **online** maior para servidor. Ver **§5.1** no documento em inglês.

### Refrigeração / ar-condicionado (split LG)

Em climas **quentes e úmidos** (ex. **Niterói**), o **ar-condicionado** entra no plano: conforto, **carga elétrica** (especialmente a **unidade externa**) e **confiabilidade** do lab (calor excessivo acelera desgaste de HDD e bateria de UPS). Inclua o **modelo LG** (evaporadora + condensadora) e dados da **placa** (A ou W) na tabela §3 do EN; ver **§8** e **§8.2.1** no documento em inglês.

**Relatado pelo operador:** split LG em **circuito dedicado ~220 V** com **disjuntor próprio**, **separado** do **resto da sala** (tomadas gerais / lab). Isso é **bom**: o **compressor** não compete no **mesmo disjuntor** que o **nobreak 120 V** + PCs — mas a **condensadora** continua **fora** do Attiv. Para **conta de luz / solar**, some as **duas** frentes; para **“vai disparar o disjuntor do lab?”**, use só o **circuito das tomadas do lab**. Amperagem do disjuntor do AC: anotar em **`docs/private/homelab/`** se quiser painel completo — ver [PRIVATE_OPERATOR_NOTES.pt_BR.md](../PRIVATE_OPERATOR_NOTES.pt_BR.md) (sem fotos do quadro no Git público).

---

## Resumo

**5º host registrado (Alpine Linux / musl — eMachines E527):** Celeron 900, 3.8 GB RAM, consumo estimado ~15 W idle / ~25 W leve / ~45 W pesado. Adicionado ao inventário do lab via [#821](https://github.com/FabioLeitao/data-boar/issues/821); tabela §3 do EN já atualizada. Incluir este host no cálculo de UPS e disjuntor da sala.

**Portátil primary:** o EN usa uma **classe** ilustrativa (notebook **14"** ~2012, **≤8 GB** DDR3, Ubuntu/Zorin); **marca/modelo/hostname** só em **`docs/private/homelab/`** — ver [PRIVATE_OPERATOR_NOTES.pt_BR.md](../PRIVATE_OPERATOR_NOTES.pt_BR.md). Adaptador **65/90 W** de teto; **§10.1** no EN.

1. **Preencha a tabela** (§3 do EN) com modelos, CPU, RAM, PSU e consumo (idle/leve/pesado) de cada máquina.
1. **Envie:** tabela preenchida + tensão (120 V ou 230 V) + disjuntor do **circuito do lab** (ex. 15 A, 20 A) + UPS atual (se houver) + **modelo do split LG**; se o AC tem **disjuntor 220 V dedicado** (como no seu caso), isso **já** está anotado no doc — só confirme **amperagem** do AC em privado se quiser cálculo de quadro.
1. **Cálculos:** total W (cenários A/B/C), UPS VA recomendado, verificação de disjuntor, contagem de tomadas.

## Fórmulas rápidas:
- **UPS VA ≥ (Total W × 1.25) / 0.85** (margem 25%, fator de potência 0.85)
- **Corrente (A) = Total W / Tensão (V)**
- **Máx. contínuo = Disjuntor (A) × 0.8** (código elétrico)
