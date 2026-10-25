package databoar.tier_test

import rego.v1

import data.databoar.tier

test_smb_requires_pro if {
	tier.min_tier with input as {"feature": "connector_smb"} == "pro"
}

test_filesystem_community if {
	tier.min_tier with input as {"feature": "connector_filesystem"} == "community"
}

test_enforced_missing_connector_denied if {
	count(tier.deny) > 0 with input as {
		"kind": "connector",
		"feature": "connector_unknown",
		"feature_tier_map_has": {"connector_filesystem": true},
		"enforcement_mode": "enforced",
	}
}
