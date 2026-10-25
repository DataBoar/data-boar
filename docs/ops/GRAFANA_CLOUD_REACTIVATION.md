# Grafana Cloud — reactivation + first safe steps (operator runbook)

**Português (Brasil):** [GRAFANA_CLOUD_REACTIVATION.pt_BR.md](GRAFANA_CLOUD_REACTIVATION.pt_BR.md)

**Purpose:** Keep a short, repeatable path for (a) **reactivating** a Grafana Cloud stack that was suspended for inactivity and (b) doing the first **safe** post-reactivation steps without leaking secrets into Git.

**Scope:** Operator-only. This repo does **not** provision Grafana Cloud automatically and does **not** store Grafana tokens in tracked files.

## 1. What “reactivation” means (and the common failure mode)

Grafana Cloud free tiers may suspend stacks after long inactivity. A common portal error is that the instance **cannot be reactivated automatically** and requires **support**.

**What to record (no secrets):**

- Stack name (human label).
- Region (if shown).
- The public stack URL shape (use placeholders in docs, e.g. `https://<org>.grafana.net/`).
- Screenshot of the portal message (keep private if it contains identifiers).

## 2. Reactivation steps (portal)

1. Log in to the Grafana Cloud portal.
1. Open your stack and try **Launch**.
1. If the portal says it cannot be reactivated automatically:
   - Use the portal’s **support** path (or email the address shown) and request reactivation.
   - Provide only what support needs (stack name + message + timeframe). Avoid sending extra personal data.
1. Wait for confirmation and retry **Launch**.

## 3. Post-reactivation: “first safe configuration”

### 3.1 Create an Access Policy token (least privilege)

1. In the portal, go to **Access policies**.
1. Create a policy + token with the minimum scope you need:
   - **Read-only** if you only want dashboards and queries.
   - **Write** only for the pipelines you actually use (metrics/logs/traces).
1. Store the token in one (or both):
   - GitHub repo secrets (for CI/workflows), and/or
   - a password manager (Bitwarden) for operator recovery.

**Never store** the token in tracked Markdown, `config.yaml`, screenshots committed to git, or chat logs that may be exported.

### 3.2 Decide what you want first (metrics vs logs vs traces)

This repo’s recommended sequence lives in the plan:

- `docs/plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md` ([pt-BR](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md))

**Operator-friendly default:** start with **metrics** (Prometheus path) and only then add logs/traces when the lab has RAM.

## 4. Integration shapes (high-level, no secrets)

Pick one or two, not everything at once:

- **Metrics**: Prometheus remote_write → Grafana Cloud metrics endpoint.
- **Logs**: Loki/Promtail → Grafana Cloud logs endpoint.
- **Traces**: OpenTelemetry collector (OTLP) → Grafana Cloud traces endpoint.

**Where to put the real endpoints and tokens:** `docs/private/` (gitignored) or environment variables on the operator host / CI secrets.

## 5. Where this connects in repo docs

- Operator index: `docs/ops/README.md` ([pt-BR](README.pt_BR.md))
- Lab map: `docs/ops/OPERATOR_LAB_DOCUMENT_MAP.md` ([pt-BR](OPERATOR_LAB_DOCUMENT_MAP.pt_BR.md))
- Learning links: `docs/ops/inspirations/LAB_OP_OBSERVABILITY_LEARNING_LINKS.md` ([pt-BR](inspirations/LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md))

