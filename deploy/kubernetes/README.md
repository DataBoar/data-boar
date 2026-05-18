# Kubernetes: Web API and frontend (default)

These manifests run the **image default**: web API and frontend on port 8088. No `command`/`args` override.

## Prerequisites

- **Image:** Edit `deployment.yaml` and set `containers[0].image` to your image (e.g. `fabioleitao/data_boar:latest` or `ghcr.io/fabioleitao/data_boar:latest`).
- **Config:** The provided ConfigMap supplies a minimal `config.yaml`. Replace or extend it for production (e.g. Secret or external config). Config is mounted at `/data/config.yaml`.

## Security (Corporate-Entity-C-aligned)

The default ConfigMap is **minimal** (empty targets). When you expose the Service via **NodePort**, **LoadBalancer**, or **Ingress** so the API is reachable from untrusted networks:

1. Set **`api.require_api_key: true`** in `config.yaml` (see `configmap.yaml` comments).
1. Provide the key via **`api.api_key`** (not committed) or **`api.api_key_from_env`** pointing at a Kubernetes **Secret** (env var injected into the pod). Same pattern as [docs/deploy/DEPLOY.md](../../docs/deploy/DEPLOY.md) § hardening and [SECURITY.md](../../SECURITY.md).

NetworkPolicy and `network-policy.example.yaml` are optional extra layers; they do not replace API key when the dashboard is reachable from a WAN.

- **Persistence:** The deployment uses `emptyDir` for `/data`, so SQLite and reports do not survive pod restart. For production, use a PersistentVolumeClaim and replace the `data` volume in `deployment.yaml`.
- **Resources:** The deployment sets memory request/limit and a small CPU request; CPU limit is unset so I/O-bound workload and report-generation bursts are not throttled. See [docs/deploy/DEPLOY.md](../../docs/deploy/DEPLOY.md) ([pt-BR](../../docs/deploy/DEPLOY.pt_BR.md)) (§ Resource and I/O tuning) for production guidance.

## Apply

From the **repository root**:

```bash
# Set your image (e.g. Docker Hub or ghcr.io)
export IMAGE=fabioleitao/data_boar:latest
# Or: export IMAGE=ghcr.io/fabioleitao/data_boar:latest

# Optional: use image from env in deployment (or edit deploy/kubernetes/deployment.yaml image field)
kubectl apply -f deploy/kubernetes/
```

## What runs

- **Deployment:** 1 replica, no command override → container runs web API + frontend (dashboard, reports, config UI).
- **Service:** ClusterIP on port 8088; use NodePort or Ingress to expose externally.
- **ConfigMap:** Minimal `config.yaml` for `/data/config.yaml`; replace or extend as needed.

## Access

- Expose via NodePort, LoadBalancer, or Ingress to port 8088.
- Dashboard: `http://<external>:8088/`, API docs: `http://<external>:8088/docs`, health: `http://<external>:8088/health`.

## CLI one-shot (Job)

To run a single audit from the CLI in the cluster, create a **Job** that overrides the command:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-boar-cli-once
spec:
  template:
    spec:
      containers:

        - name: audit

          image: YOUR_IMAGE
          command: ["python"]
          args: ["main.py", "--config", "/data/config.yaml", "--tenant", "Acme", "--technician", "Ops"]
          volumeMounts:

            - name: data

              mountPath: /data
      volumes:

        - name: data

          configMap:
            name: data-boar-config
      restartPolicy: Never
  backoffLimit: 0
```

Mount the same ConfigMap (or a volume with config) and ensure `report.output_dir` in config is `/data` so reports persist in the volume if needed.
