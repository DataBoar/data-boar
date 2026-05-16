# SonarQube in a home lab (Docker) — CI, IDE, and MCP

**Português (Brasil):** [SONARQUBE_HOME_LAB.pt_BR.md](SONARQUBE_HOME_LAB.pt_BR.md)

This guide helps you run **SonarQube Server** on a second machine (Linux VM or container host) so you can:

- Point **GitHub Actions** at it (same job as in `.github/workflows/ci.yml` when `SONAR_TOKEN` and `SONAR_HOST_URL` are set).
- Connect **Cursor / VS Code** (SonarQube extension and/or **SonarQube MCP**) to the same server.

It complements [`.cursor/rules/sonarqube_mcp_instructions.mdc`](../../.cursor/rules/sonarqube_mcp_instructions.mdc) (how the **agent** should use MCP tools) and [`sonar-project.properties`](../../sonar-project.properties) (what we scan). For day-to-day test and lint behaviour, see [TESTING.md](../TESTING.md).

---

## 1. What you need on the lab server

| Resource    | Practical minimum           | Notes                                                                                                                                              |
| --------    | -----------------           | -----                                                                                                                                              |
| **RAM**     | **4 GB** for SonarQube + DB | 8 GB+ is more comfortable; Elasticsearch embedded in Sonar is memory-hungry.                                                                       |
| **Disk**    | **20 GB+** free             | Grows with analysis history; SSD recommended.                                                                                                      |
| **CPU**     | 2 vCPU                      | More helps parallel analysis.                                                                                                                      |
| **OS**      | Linux x86_64                | Docker Engine or Podman; VM or bare metal.                                                                                                         |
| **Network** | Reachable from your PC      | For IDE/MCP. For **GitHub-hosted runners**, see §6 — they must reach the URL from the **public internet** unless you use a **self-hosted runner**. |

---

## 2. Host kernel settings (Linux)

SonarQube’s embedded search layer needs higher `vm.max_map_count` on the **Docker host** (not only inside the container):

```bash
# Apply now
sudo sysctl -w vm.max_map_count=524288

# Persist after root (example: Debian/Ubuntu)
echo 'vm.max_map_count=524288' | sudo tee /etc/sysctl.d/99-sonarqube.conf
sudo sysctl --system
```

If SonarQube exits with errors about `max virtual memory areas`, recheck this value.

---

## 3. Docker Compose (SonarQube + PostgreSQL)

Create a directory (e.g. `/opt/sonarqube`) and a `docker-compose.yml` like below. **Do not expose SonarQube to the open internet** without TLS and strong auth (see §7).

```yaml
services:
  sonarqube:
    image: sonarqube:community
    depends_on:
      db:
        condition: service_healthy
    environment:
      SONAR_JDBC_URL: jdbc:postgresql://db:5432/sonar
      SONAR_JDBC_USERNAME: sonar
      SONAR_JDBC_PASSWORD: ${SONAR_DB_PASSWORD:?set SONAR_DB_PASSWORD in .env}
      # Optional: cap heap on small VMs (tune to your RAM)
      SONAR_ES_JAVA_OPTS: "-Xms512m -Xmx512m"
      SONAR_WEB_JAVA_OPTS: "-Xms256m -Xmx512m"
    volumes:

      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_extensions:/opt/sonarqube/extensions
      - sonarqube_logs:/opt/sonarqube/logs

    ports:

      - "9000:9000"

    ulimits:
      nofile:
        soft: 65535
        hard: 65535

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: sonar
      POSTGRES_PASSWORD: ${SONAR_DB_PASSWORD:?set SONAR_DB_PASSWORD in .env}
      POSTGRES_DB: sonar
    volumes:

      - postgresql_data:/var/lib/postgresql/data

    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sonar -d sonar"]
      interval: 5s
      timeout: 5s
      retries: 10

volumes:
  sonarqube_data:
  sonarqube_extensions:
  sonarqube_logs:
  postgresql_data:
```

Create `.env` in the same directory (chmod `600`):

```bash
SONAR_DB_PASSWORD=your-long-random-secret-here
```

Start:

```bash
docker compose up -d
docker compose logs -f sonarqube   # wait until “SonarQube is operational”
```

Open `http://<server-ip>:9000`. Default login is **admin / admin** — you **must** change the password on first login.

**Image tag:** `sonarqube:community` tracks current Community Build releases. For stricter reproducibility, pin a digest or an explicit version tag from [Docker Hub](https://hub.docker.com/_/sonarqube).

---

## 4. Create project and token (for CI, IDE, MCP)

1. **Create a project** in SonarQube with a **Project key** that matches `sonar.projectKey` in this repo (`data-boar` unless you change it).
1. **User token (not project token):** **My Account → Security → Generate Tokens.**
   - The MCP rule file [`.cursor/rules/sonarqube_mcp_instructions.mdc`](../../.cursor/rules/sonarqube_mcp_instructions.mdc) states SonarQube expects **user** tokens for API/MCP-style use.
1. **GitHub repository secrets** (for `ci.yml` sonar job):
   - `SONAR_TOKEN` — the user token.
   - `SONAR_HOST_URL` — base URL of your server, e.g. `<https://sonarqube.home.exampl>e` (no trailing slash).
   - Do **not** set `sonar.organization` in `sonar-project.properties` for SonarQube Server (that is for SonarCloud).

Local scripts (e.g. `scripts/sonar_issues.py`) use the same variables:

```bash
export SONAR_HOST_URL=http://<your-sonar-host>:9000   # LAN hostname or IP; do not commit real values to the public repo
export SONAR_TOKEN=squ_xxxxxxxx
uv run python scripts/sonar_issues.py
```

---

## 5. Cursor / VS Code — SonarQube extension

1. Install the **SonarQube** extension (SonarSource) in Cursor/VS Code.
1. Add a **connected mode** server: your `SONAR_HOST_URL` + **user token**.
1. Bind the workspace to the project key matching `sonar-project.properties`.

The extension uses the same analysis configuration as CI (`sonar-project.properties`).

---

## 6. GitHub Actions vs home lab networking (important)

GitHub’s **hosted** runners run on GitHub’s cloud. They can only call `SONAR_HOST_URL` if it is **reachable from the public internet** (or from GitHub’s network), e.g.:

- **HTTPS reverse proxy** (Caddy, nginx, Traefik) with a real or internal DNS name.
- **Tailscale** **subnet router** or **public exit** so a stable hostname resolves to the service (still prefer TLS).
- **Cloudflare Tunnel** (or similar) to expose `9000` without opening router ports.

**Alternative (often simpler for a lab):** run a **[self-hosted GitHub Actions runner](https://docs.github.com/en/actions/hosting-your-own-runners)** on the same LAN as SonarQube. The runner reaches SonarQube at an **internal URL** (e.g. `http://sonarqube:9000`). No public exposure of SonarQube required.

Choose one approach; mixing “private IP only” with **only** GitHub-hosted runners will **not** work.

---

## 7. Security checklist (home lab)

- Change default **admin** password immediately.
- Prefer **HTTPS** in front of SonarQube (reverse proxy with Let’s Encrypt or internal CA).
- **Firewall:** allow `9000` (or `443` via proxy) only from trusted IPs or your **Tailscale** interface.
- Treat `SONAR_TOKEN` like a password; rotate if leaked.
- SonarQube holds **source-derived** metadata; back up volumes (`sonarqube_data`, DB volume) if you care about history.

---

## 8. SonarQube MCP in Cursor

MCP servers vary by implementation; typical requirements are:

- **Server base URL** — same as `SONAR_HOST_URL`.
- **User token** — same as for the scanner.
- The agent-side behaviour (e.g. `analyze_file_list`, `toggle_automatic_analysis`) is described in [`.cursor/rules/sonarqube_mcp_instructions.mdc`](../../.cursor/rules/sonarqube_mcp_instructions.mdc).

Add the MCP server in **Cursor Settings → MCP** per the MCP provider’s README (env var names may differ). After the SonarQube container is healthy and the token works in the browser/extension, point MCP at the same URL and token.

---

## 9. Troubleshooting

| Symptom                    | What to check                                                                                 |
| -------                    | -------------                                                                                 |
| Container exits on start   | `vm.max_map_count`, `docker compose logs sonarqube`, RAM (OOM).                               |
| `Not authorized` (API/MCP) | User token vs project token; token type and expiry.                                           |
| CI cannot connect          | Hosted runner vs private IP — use tunnel or self-hosted runner (§6).                          |
| IDE connects, CI fails     | Different URLs or missing `SONAR_HOST_URL` secret; trailing slash on URL.                     |
| Quality gate always red    | Narrow rules in SonarQube UI or first analysis baseline; fix or adjust gate for new projects. |

---

## See also

- [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) — deployment smoke tests and synthetic/real **data targets** (filesystem, SQL, archives) on a second machine; complements SonarQube (code quality).
- [TESTING.md](../TESTING.md) — SonarQube/SonarCloud section and `scripts/sonar_issues.py`.
- [sonar-project.properties](../../sonar-project.properties) — project key, sources, exclusions.
- `.github/workflows/ci.yml` — `sonar` job conditions and `SonarSource/sonarqube-scan-action`.
