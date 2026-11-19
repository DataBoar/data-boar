#!/usr/bin/env bash
# Syntax-check LAB-NODE-01 Ansible playbooks (regression for #1631 Jinja var names)
# and deploy/ansible/site-demo-prospect.yml (epic #2280).
# Usage (from repo root): ./scripts/ansible-syntax-check.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANSIBLE_DIR="$REPO_ROOT/ops/automation/ansible"
cd "$ANSIBLE_DIR"

if ! command -v ansible-playbook >/dev/null 2>&1; then
  echo "ansible-playbook not found; install ansible-core (CI job ansible-syntax does)." >&2
  exit 2
fi

# Optional collections (e.g. ansible.posix.acl for lab_node_01_toolchain_restrict).
if [[ -f collections/requirements.yml ]] && command -v ansible-galaxy >/dev/null 2>&1; then
  ansible-galaxy collection install -r collections/requirements.yml -p collections/ansible_collections
fi

export ANSIBLE_ROLES_PATH="$ANSIBLE_DIR/roles"
export ANSIBLE_COLLECTIONS_PATH="$ANSIBLE_DIR/collections/ansible_collections${ANSIBLE_COLLECTIONS_PATH:+:$ANSIBLE_COLLECTIONS_PATH}"
INV="$ANSIBLE_DIR/inventory.example.ini"

for pb in lab-node-01-baseline.yml lab-node-01-podman.yml; do
  echo "ansible-playbook --syntax-check playbooks/$pb"
  ansible-playbook --syntax-check -i "$INV" "playbooks/$pb"
done

# deploy/ansible: the per-prospect pod tooling (epic #2280, task 2280.3). The example
# inventory has the demo_prospect group; the playbook needs no collection.
DEPLOY_ANSIBLE_DIR="$REPO_ROOT/deploy/ansible"
(
  cd "$DEPLOY_ANSIBLE_DIR"
  export ANSIBLE_ROLES_PATH="$DEPLOY_ANSIBLE_DIR/roles"
  echo "ansible-playbook --syntax-check deploy/ansible/site-demo-prospect.yml"
  ansible-playbook --syntax-check -i "$DEPLOY_ANSIBLE_DIR/inventory/hosts.ini.example" \
    site-demo-prospect.yml
)

echo "ansible-syntax-check.sh: OK"
