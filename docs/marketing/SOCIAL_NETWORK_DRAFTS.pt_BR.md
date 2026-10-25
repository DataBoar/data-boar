# Rascunhos para redes (banco de copy do operador)

**Público:** Mantenedor ou parceiro postando no LinkedIn, X ou similar. **Não** é conteúdo agendado no CI.

**Aviso:** O Data Boar expõe **sinais e metadados de governança**; **não** substitui assessoria jurídica. Quando o post falar em lei ou compliance, use linguagem de **inventário e alertas** (“sinaliza tensão”, “postura de retenção”, “política do operador”) e aponte para docs de produto, não para planos internos.

**Versão em inglês:** [SOCIAL_NETWORK_DRAFTS.md](SOCIAL_NETWORK_DRAFTS.md)

**Temas de origem (docs públicos):** [MAP.md](../MAP.md), [THE_WHY.md](../philosophy/THE_WHY.pt_BR.md), [JURISDICTION_COLLISION_HANDLING.md](../JURISDICTION_COLLISION_HANDLING.pt_BR.md), ADRs [0038](../adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md) / [0039](../adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md), [PORT_LOGISTICS_MULTINATIONAL_CREW.md](../use-cases/PORT_LOGISTICS_MULTINATIONAL_CREW.pt_BR.md).

---

## Posts curtos (uma tela)

1. **MAP + vault**
   Publicamos um **MAP** do Data Boar: o que existe hoje, o que é experimental e onde os ADRs fixam intenção. Se você avalia descoberta de dados sensíveis, comece por ali—depois o **Cofre do Arquiteto** no README para filosofia e colisão de jurisdição. #GovernancaDeDados #DadosSensiveis

2. **Evidência vs teatro**
   Ferramenta boa de compliance não é **deck bonito**. É **evidência repetível**: o que foi escaneado, o que bateu, o que você manteve ou descartou e quem é dono da retenção. A página pública **THE_WHY** diz isso direto—sem história de herói. #LGPD #ProtecaoDeDados

3. **Jurisdição é pista, não sentença**
   Dado multinacional costuma carregar **mais de um enquadramento plausível**. O papel do produto é **mostrar tensão e inventariar sinais**, não “escolher o país” sozinho. Veja o ADR 0038 e o guia de colisão de jurisdição. #Compliance #Fronteira

4. **Menores de idade no centro**
   Se o seu corpus pode incluir menores de 18 anos, **detecção de menores é de primeira classe** no roadmap—não um regex colado depois. Isso é escolha de produto e ética, não slogan. #SegurancaInfantil #IAresponsavel

5. **Contexto alfandegado / adjacente**
   Em ambientes lacrados ou adjacentes à alfândega, **retenção e artefatos são do operador**. A ferramenta **não** etiqueta “base legal” sozinha. O ADR 0039 documenta essa postura para integradores. #CadeiaDeSuprimentos #Auditoria

6. **Porto + dados de tripulação**
   **Storyboard de caso de uso** genérico: tripulação multinacional, escala, idiomas mistos, alta sensibilidade. Útil para conversas de **escopo estilo DPIA**—sem nome de cliente, sem drama. #Maritimo #DadosDeRH

7. **Logs e segredos**
   Log operacional não pode virar **segundo vazamento**. Documentamos **padrões de redação** (ADR 0036) para o operador saber o que o daemon pode guardar. #Seguranca #DevOps

8. **Governança do auditor**
   Compradores perguntam **quem rodou o scanner** e se mudanças de comportamento são **defensáveis**. O ADR 0037 documenta a linha de base 2026: atribuição de sessão, sinais orientados a integridade, trilha de auditoria em export—sem vender “imutável em cada clique”. #SOC2 #GRC

---

## Fio (LinkedIn / X — ajuste ao limite da plataforma)

**A. Fio do POC honesto**
(1) Entregamos um **MAP**: claro sobre o que é “formato produção” vs laboratório.
(2) Descoberta de dados sensíveis precisa de **tratamento de colisão** quando pistas de jurisdição discordam.
(3) Leia o **THE_WHY**: evidência vence teatro.
(4) Integradores: ADRs 0038–0039 para alertas de ambiguidade e retenção em contexto alfandegado.
(5) CTA: clone o repositório, leia USAGE, rode o seu corpus em sandbox.

**B. RH / logística multinacional**
(1) Arquivos de tripulação e terceiros são **alto risco** e **multijurisdição por padrão**.
(2) Scanner que “decide Brasil só pelo telefone” está **prometendo demais**.
(3) Prefira produtos que **inventariam conflito** e deixam o **dono da política** decidir.
(4) Ponteiros: doc de colisão de jurisdição + caso de uso portuário.

---

## Entrada opcional no journal de QA (uma linha interna)

Quando fechar uma fatia só de documentação (MAP, ADR, caso de uso), cole nas **notas de release ou QA**:
*“Somente docs: adicionado/atualizado [arquivo]; tier externo sem links para planos (ADR 0004); locale/pt-BR conferido nos pares.”*

Assim o que vai para rede **bate** com o que de fato foi entregue.
