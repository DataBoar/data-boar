package databoar.tier

import rego.v1

# Illustrative ladder — mirrors FEATURE_TIER_MAP intent (#854 connector boundary).
tier_rank := {
	"community": 1,
	"pro": 2,
	"enterprise": 3,
	"open": 99,
}

default min_tier := "community"

min_tier := "pro" if {
	input.feature == "connector_smb"
}

min_tier := "pro" if {
	input.feature == "connector_powerbi"
}

min_tier := "community" if {
	input.feature == "connector_filesystem"
}

min_tier := "community" if {
	input.feature == "connector_postgresql"
}

# Symptom #887: custom/partner tiers must not bypass documented ladder without explicit rule.
deny[msg] if {
	input.claimed_tier == "partner_custom"
	not input.operator_override_documented
	msg := "partner_custom tier requires documented operator override (#887)"
}

# Symptom #854: connector without explicit mapping should fail closed in enforced mode.
deny[msg] if {
	input.kind == "connector"
	not input.feature_tier_map_has[input.feature]
	input.enforcement_mode == "enforced"
	msg := sprintf("connector '%s' missing FEATURE_TIER_MAP entry (#854)", [input.feature])
}
