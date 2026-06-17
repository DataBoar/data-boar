# AI evolution primer (no hype)

**Português (Brasil):** [AI_EVOLUTION_PRIMER.pt_BR.md](AI_EVOLUTION_PRIMER.pt_BR.md)

This note is for **integrators, compliance readers, and maintainers** who hear “AI” used interchangeably for **regex**, **random forests**, **chatbots**, and **billion-parameter models**. It is **not** a full history of the field; decades and labels are **approximate** on purpose. For textbook depth, use a general AI/ML reference (e.g. Russell & Norvig, *Artificial Intelligence: A Modern Approach*)—here we only **anchor vocabulary** so Data Boar’s **deterministic + supervised** posture makes sense.

**Related product docs:** [TECH_GUIDE.md](TECH_GUIDE.md#detection-stack-vs-generative-llms) · [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) · [GLOSSARY.md](GLOSSARY.md) (§8 and **§8b**).

---

## 1. Why this exists (and what it is not)

- **Why:** Vendors blur **retrieval**, **classification**, **rules**, and **generative text** under one brand, “AI”. Data Boar needs a **shared timeline** so “we use ML” does **not** mean “we ship an LLM inside the scanner.”
- **What it is not:** A promise that any one technique is “safe”; every layer has **false positives/negatives** or **misuse paths**. Not legal advice.

---

## 2. Chronology at a glance (high level)

| Era (approx.) | Dominant idea | What worked | What broke confidence |
| ------------- | ------------- | ----------- | --------------------- |
| **1950s–1960s** | Symbolic reasoning, early **cybernetics**, first **neural** models (e.g. perceptron) | Proofs-of-concept, games, optimism | Hard problems stayed hard; **limited compute** |
| **Late 1960s–1970s** | Same symbolic push; first **funding contraction** often called an **“AI winter”** | Specialized demos | **Cost vs results**; famous limits on early linear classifiers for non-linear tasks |
| **1980s** | **Expert systems**, **knowledge bases**, **Lisp machines** (workstations optimized for AI languages) | Narrow domains (config, diagnostics **if** rules stable) | **Brittleness**, **knowledge acquisition bottleneck**, high **maintenance** → **second bust** / funding dip (**late 1980s–1990s** in many accounts) |
| **1990s–2000s** | **ML as statistics**: trees, SVMs, kernels, **random forests**; more **data** and **disk** | Tabular and text **classification** with **labeled** datasets | Poor choices still yield **garbage**; **bias** in data echoes in models |
| **2010s onward** | **Deep learning**: **GPU** throughput, **ImageNet** moment (~2012) for vision; **RNN/LSTM** then **Transformers** (~2017) for sequences | **Representation learning** at scale when **labels** or **self-supervision** align | **Data hunger**, **opaque errors**, **environment shift**; ops cost |
| **2020s** | **Very large** **transformer** models; **LLMs** as product category | Drafting, search assistants, code **suggestions** | **Hallucination**, **non-determinism**, **privacy** when sending **customer** text out of band |

---

## 3. Method families—where they fit, limits, caution

| Family | Typical use | Strength | Limit / caution |
| ------ | ----------- | -------- | ----------------- |
| **Symbolic / rules** | Logic, tax codes as **if-then**, parsers | **Auditable**, repeatable | **Coverage** gaps; experts must maintain rules |
| **Expert systems (1980s style)** | Encoded domain heuristics | Transparent **if** rules honest | **Stale** knowledge; conflict rules hard |
| **Classical ML** (trees, SVMs, linear models, **TF-IDF** + forest) | Labeled **tabular/text** slices | **Reproducible** with fixed seeds and versioned features | Needs **quality labels**; **domain shift** |
| **Deep learning** (CNNs, transformers **as encoders**) | Vision, speech **features**, embeddings | Rich representations | **Compute**, tuning, **black-box** behaviour in places |
| **Reinforcement learning (RL)** | Games, robotics **policies**, recommender **simulation** | Strong when **environment** is cheap to sample | **Sample inefficiency**; **safety** and **verification** in production are hard |
| **Deep RL (DRL)** | **RL** with **deep neural** policies or value networks (e.g. DQN, PPO on pixels) | Handles **high-dimensional** state; same reward-driven loop as tabular RL | **Not** “RDL” as a standard acronym—use **DRL** (**deep reinforcement learning**). Inherits **RL + DL** risks (reward hacking, opaque failures) |
| **Language models (LM)—classical to “large”** | Ranking, completion, **ASR** rescoring, assistants | **Fluency**, broad priors when **weights** fit in **RAM/GPU** | **Confabulation** risk grows with open-ended prompts; **PII** in prompts |
| **LLM (generative, chat-oriented)** | Drafts, brainstorming, **IDE** assist | Fast iteration on **language** | **Not** a substitute for **git/CI** on regulated artefacts |

**Voice assistants (e.g. Siri-class products):** Historically a **pipeline**—**speech recognition**, **intent detection**, **slot filling**, **dialog policy**, **text-to-speech**—mixing **classical NLP**, **smaller** statistical or neural **language models**, and **rules**. That is **not identical** to dropping a single **frontier-scale LLM** into the same slot; marketing language often **compresses** the stack.

---

## 4. Hardware and software co-evolution (why “large” now)

- **CPUs → GPUs → TPUs / big clusters:** Throughput and **memory bandwidth** set practical **model size** and **batch size**.
- **Frameworks** (automatic differentiation, **CUDA**, high-level DL libs): Lowered the **engineering** cost to train and deploy nets.
- **Data + corpora + web text:** **Self-supervised** pre-training made **general** LMs feasible before task-specific fine-tuning.
- **Implication:** “**Large**” is partly an **engineering** statement (what fits on **your** budget of **VRAM** and **latency**), not a moral claim about quality.

---

## 5. How this aligns with Data Boar (evidence-first)

- **In-product detection:** **Regex** + **named patterns** + **supervised ML/DL** on **your** terms and **your** samples, with **reproducible** scoring—see [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md). That sits in the **classical ML / controlled DL** column, not the **open-ended LLM** column.
- **Compliance outputs:** **Metadata-first findings**, **norm tags**, **quasi-identifier** aggregation, **minor** signals, **jurisdiction hints**—structured artefacts for **human** review, not generative prose that invents **sources**.
- **Around the repo:** **LLMs** (IDE agents, vendor chat) can help **draft** docs or **explore** ideas—treat outputs as **unverified** until **tests** and **diff** say otherwise; see [docs/ops/LLM_AGENT_EDITING_CAUTION.md](ops/LLM_AGENT_EDITING_CAUTION.md).

---

## 6. Further reading (independent of this repo)

- Russell, S. & Norvig, P., *Artificial Intelligence: A Modern Approach* — broad, vendor-neutral **survey**.
- Goodfellow, Bengio, Courville, *Deep Learning* — **DL** foundations.
- Official histories from **DARPA**, **ACM**, university courses—prefer **primary** timelines when citing **dates** in external material.

---

**See also:** [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md#deterministic-detection-vs-generative-llm-hype) · [docs/ops/LLM_AGENT_EDITING_CAUTION.md](ops/LLM_AGENT_EDITING_CAUTION.md)
