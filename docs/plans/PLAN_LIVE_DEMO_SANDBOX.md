# Plan: Live Demo Sandbox (`dashboard.net.br`)

Status: in progress  
Scope: public, synthetic-data demonstration environment

## Objective

Publish a safe, resettable Data Boar demonstration at `dashboard.net.br` without
turning the demo into a production data-processing endpoint. The first deployment
targets one OCI region and one availability domain; the application must remain
portable to a customer-owned cloud or an air-gapped runner.

## v0 architecture

- OCI Home Region: Brazil East (São Paulo), using Always Free resources while the
  environment has no paying customers.
- One dedicated VCN for the demo, with non-overlapping private address space.
- Public exposure limited to the edge/reverse-proxy path. Application and data
  services have no public IP addresses.
- Private application and data subnets; database ingress is permitted only from
  the application security group.
- Network Security Groups (NSGs) and security lists use deny-by-default ingress.
- No Internet SSH. Administrative access uses a private operator path (Bastion,
  VPN, or an equivalent controlled channel).
- Cloudflare Proxy or Tunnel terminates the public path; the origin is never
  exposed as an unrestricted backend.
- Egress is restricted. OCI Service Gateway is preferred for OCI services; NAT is
  used only where an explicit connector requires it.
- Synthetic data only. No customer credentials, production data, or paid
  third-party secrets are embedded in the demo.

## Safety controls

- Read-only/curated connector targets in v0.
- Application SSRF protection and explicit target allowlists.
- Resource, request, and scan-size caps.
- Periodic reset to a known-good synthetic state.
- No user-controlled arbitrary network destination in the public demo.
- Budget and quota alerts before any paid-resource upgrade.
- Logs and telemetry must not contain credentials or raw sensitive payloads.

## Delivery sequence

1. Define and review the VCN, subnet, route, NSG, and egress manifest.
2. Create a dedicated compartment and budget guardrail.
3. Provision the smallest suitable Always Free compute shape, without public
   application/data addresses.
4. Deploy the edge and synthetic demo stack; validate reset and failure modes.
5. Configure `dashboard.net.br` only after the origin passes the private smoke
   tests.
6. Add the demo link to `databoar.com.br` only after the endpoint is stable.
7. Record operational limits and the migration path to BYO-cloud and air-gapped
   deployments.

## Acceptance criteria

- `dashboard.net.br` serves the curated demo over HTTPS through the protected edge.
- No application or data service is directly reachable from the public Internet.
- Reset restores the documented synthetic baseline.
- SSRF, rate, size, and connector allowlist tests pass.
- OCI budget/quota guardrails are active before enabling paid capacity.
- The deployment can be reproduced from a versioned manifest without private
  credentials.

## Explicit non-goals for v0

- Production customer tenancy or durable customer data.
- Arbitrary third-party credentials.
- Multi-region high availability.
- Public SSH, unrestricted outbound Internet, or a general-purpose sandbox.
- Claiming SaaS isolation guarantees beyond the documented single-demo scope.

