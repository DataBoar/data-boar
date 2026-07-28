#!/bin/sh
# Synthetic lab data only — obvious fakes and edge cases for detector tuning (FP/FN experiments).
# Do not use real personal data.
#
# Redis has no schema. This seed exercises #1348: redis_connector.py uses GET on each key;
# WRONGTYPE on hash/list/set is swallowed, so PII in non-string values is invisible today.

set -e

REDIS_HOST="${REDIS_HOST:-lab-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"

wait_for_redis() {
  attempt=0
  while [ "$attempt" -lt 60 ]; do
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null | grep -q PONG; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  echo "lab-redis seed: redis not ready at ${REDIS_HOST}:${REDIS_PORT}" >&2
  exit 1
}

wait_for_redis

# (a) STRING + opaque key name — PII in value (GET path works today).
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SET 'u:1001' \
  'Cliente Sintético Alfa; CPF 123.456.789-09; audit.synthetic@example.invalid'

# (b) HASH + opaque key — PII in fields; GET fails WRONGTYPE (#1348 exposure case).
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" HSET 'u:1002' \
  email 'hash.pii@example.invalid' \
  cpf '529.982.247-25' \
  nome 'Cliente Hash Sintetico'

# (c) LIST and SET — same WRONGTYPE class as (b).
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" RPUSH 'u:1003' \
  'Lista sintetica RG 12.345.678-9' \
  'email list.case@example.invalid'
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SADD 'u:1004' \
  'set.member@example.invalid' \
  'CPF 111.444.777-35 sintetico'

# (d) STRING + talkative key name, clean value — name-based detection control.
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SET 'customer:email:1003' 'valor-limpo-sem-pii'

# (e) Audit/migration keys — negative control for anti-generic (#1327).
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SET 'created_at' '2026-01-01T00:00:00Z'
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SET 'schema_migrate_log' 'migration_v42_applied'

echo "lab redis smoke seed applied"
