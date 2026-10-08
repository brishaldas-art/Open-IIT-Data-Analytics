"""Version strings. Every response is attributable to these (contract §12, invariant 9)."""

SCHEMA_VERSION = "sutra-1.0"                 # §12 — any field added/removed bumps this
RULE_VERSION = "candidate-rules-v2"          # resolver + candidate + ranking rules
EVIDENCE_POLICY_VERSION = "evidence-policy-v3"
RADIUS_MAP_VERSION = "radius-map-v1"
GATE_RULE_VERSION = "gate-v2"                # eligibility gate
PURPOSE_RULE_VERSION = "purpose_rules-v1"
DIRECTIONS_RULE_VERSION = "directions-v1"
PROTOCOL_VERSION = "protocol-v1-immutable"   # §2 train/eval protocol
STORE_SCHEMA_VERSION = "store-2"   # belief rows are scoped by rule set
WATCHTOWER = "sutra-1.0"

ALL = {
    "schema_version": SCHEMA_VERSION,
    "rule_version": RULE_VERSION,
    "evidence_policy_version": EVIDENCE_POLICY_VERSION,
    "radius_map_version": RADIUS_MAP_VERSION,
    "gate_rule_version": GATE_RULE_VERSION,
    "purpose_rule_version": PURPOSE_RULE_VERSION,
    "directions_rule_version": DIRECTIONS_RULE_VERSION,
    "protocol_version": PROTOCOL_VERSION,
    "store_schema_version": STORE_SCHEMA_VERSION,
}
