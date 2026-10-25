# Operator governance checklist for compliance samples

**Português (Brasil):** [OPERATOR_GOVERNANCE_CHECKLIST.pt_BR.md](OPERATOR_GOVERNANCE_CHECKLIST.pt_BR.md)

Use this checklist when enabling or updating a regional compliance sample.

## 1) Scope and purpose

- Define the systems and data domains included in this scan cycle.
- Record explicit exclusions and why they are excluded.
- Confirm the operational purpose (inventory, triage, remediation prep, audit prep).
- Confirm legal/compliance reviewer for this cycle.

## 2) Data minimization and limits

- Set sampling limits appropriate to the environment.
- Confirm scanning strategy does not duplicate raw PII into ad-hoc files.
- Validate report destination and access controls.
- Confirm retention and deletion policy for outputs and local databases.

## 3) Profile and norm-tag quality

- Confirm selected sample profile matches the intended jurisdiction.
- Review `norm_tag` and recommendation wording before production scans.
- Add organization-specific overrides where required.
- Keep a changelog note when profile semantics are adjusted.

## 4) Credentials and least privilege

- Use dedicated read-only credentials where possible.
- Restrict network access to only approved targets.
- Avoid broad shared credentials across unrelated connectors.
- Confirm secret storage follows operator policy (no secrets in tracked docs).

## 5) Evidence and traceability

- Keep scan session identifiers and execution timestamps.
- Export and archive audit trail artifacts when required.
- Record app version and config profile used for each relevant run.
- Capture who approved scope and who reviewed findings.

## 6) Decision and escalation

- Define what triggers immediate remediation.
- Define what requires legal/compliance escalation.
- Define what is accepted temporarily with owner and review date.
- Keep unresolved high-risk findings out of silent backlog.

## 7) Review cadence

- Revalidate critical profiles at least quarterly.
- Revalidate before high-stakes audits or regulator-facing milestones.
- Revalidate when law text or regulator guidance materially changes.
- Revalidate after major connector or detection-profile changes.

## Related docs

- [README.md](README.md) ([pt-BR](README.pt_BR.md))
- [../COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) ([pt-BR](../COMPLIANCE_FRAMEWORKS.pt_BR.md))
- [../COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) ([pt-BR](../COMPLIANCE_AND_LEGAL.pt_BR.md))
- [../USAGE.md](../USAGE.md) ([pt-BR](../USAGE.pt_BR.md))
