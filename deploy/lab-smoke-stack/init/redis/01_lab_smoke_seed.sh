#!/bin/sh
# Synthetic lab data only — obvious fakes and edge cases for detector tuning (FP/FN experiments).
# Do not use real personal data.
#
# Redis has no schema. This seed exercises #1348: redis_connector.py TYPE-dispatches
# value sampling (string GET, hash HSCAN, list LRANGE, set SSCAN, zset ZRANGE, stream XRANGE).

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

# (b) HASH + opaque key — PII in fields (#1348 hash dispatch via HSCAN).
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" HSET 'u:1002' \
  email 'hash.pii@example.invalid' \
  cpf '529.982.247-25' \
  nome 'Cliente Hash Sintetico'

# (c) LIST and SET — same multi-type sampling path as (b).
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" RPUSH 'u:1003' \
  'Lista sintetica RG 12.345.678-9' \
  'email list.case@example.invalid'
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SADD 'u:1004' \
  'set.member@example.invalid' \
  'CPF 111.444.777-35 sintetico'

# (f) ZSET + opaque key — synthetic PII in a member (dado sintético, regra #1288).
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ZADD 'u:1005' 1 \
  '529.982.247-25 zset.member@example.invalid'

# (g) STREAM + opaque key — synthetic PII in entry fields (dado sintético, regra #1288).
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" XADD 'u:1006' '*' \
  email 'stream.pii@example.invalid' \
  cpf '123.456.789-09'

# (d) STRING + talkative key name, clean value — name-based detection control.
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SET 'customer:email:1003' 'valor-limpo-sem-pii'

# (e) Audit/migration keys — negative control for anti-generic (#1327).
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SET 'created_at' '2026-01-01T00:00:00Z'
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SET 'schema_migrate_log' 'migration_v42_applied'

echo "lab redis smoke seed applied"
