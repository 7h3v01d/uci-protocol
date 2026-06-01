# UCI Reference JSON Schema
### Draft v0.1

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://uci-spec.org/schemas/uci-manifest-0.1.schema.json",
  "title": "UCI Manifest",
  "description": "Reference JSON Schema for Universal Capability Interface manifests.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "uci_manifest_version",
    "node",
    "capabilities",
    "transports",
    "governance",
    "compatibility",
    "compliance",
    "audit",
    "extensions"
  ],
  "properties": {
    "uci_manifest_version": {
      "type": "string",
      "const": "0.1"
    },

    "node": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "node_id",
        "instance_id",
        "display_name",
        "node_type",
        "version"
      ],
      "properties": {
        "node_id": {
          "$ref": "#/$defs/identifier"
        },
        "instance_id": {
          "$ref": "#/$defs/identifier"
        },
        "display_name": {
          "type": "string",
          "minLength": 1
        },
        "description": {
          "type": "string"
        },
        "node_type": {
          "type": "string",
          "enum": [
            "application",
            "service",
            "agent",
            "daemon",
            "adapter",
            "hardware_bridge",
            "orchestrator",
            "policy_engine",
            "registry"
          ]
        },
        "vendor": {
          "type": "string"
        },
        "version": {
          "type": "string",
          "minLength": 1
        }
      }
    },

    "capabilities": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "#/$defs/capability"
      }
    },

    "transports": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "#/$defs/transport"
      }
    },

    "governance": {
      "$ref": "#/$defs/governance"
    },

    "compatibility": {
      "$ref": "#/$defs/compatibility"
    },

    "compliance": {
      "$ref": "#/$defs/compliance"
    },

    "audit": {
      "$ref": "#/$defs/audit"
    },

    "extensions": {
      "type": "object",
      "additionalProperties": true
    },

    "integrity": {
      "$ref": "#/$defs/integrity"
    }
  },

  "$defs": {
    "identifier": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_]*$",
      "minLength": 1
    },

    "version_string": {
      "type": "string",
      "pattern": "^[0-9]+(\\.[0-9]+){0,2}(-[a-zA-Z0-9_.-]+)?$"
    },

    "capability": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "capability_id",
        "version",
        "category",
        "description",
        "actions"
      ],
      "properties": {
        "capability_id": {
          "$ref": "#/$defs/identifier"
        },
        "version": {
          "$ref": "#/$defs/version_string"
        },
        "category": {
          "type": "string",
          "enum": [
            "retrieval",
            "storage",
            "generation",
            "analysis",
            "transformation",
            "communication",
            "execution",
            "governance",
            "monitoring",
            "vision",
            "audio",
            "identity",
            "network",
            "security",
            "utility",
            "other"
          ]
        },
        "description": {
          "type": "string",
          "minLength": 1
        },
        "aliases": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/identifier"
          },
          "uniqueItems": true
        },
        "actions": {
          "type": "array",
          "minItems": 1,
          "items": {
            "$ref": "#/$defs/action"
          }
        }
      }
    },

    "action": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "action_id",
        "description",
        "execution",
        "input_schema",
        "output_schema",
        "risk",
        "permissions",
        "errors"
      ],
      "properties": {
        "action_id": {
          "$ref": "#/$defs/identifier"
        },
        "version": {
          "$ref": "#/$defs/version_string"
        },
        "description": {
          "type": "string",
          "minLength": 1
        },
        "execution": {
          "$ref": "#/$defs/execution"
        },
        "input_schema": {
          "type": "object"
        },
        "output_schema": {
          "type": "object"
        },
        "risk": {
          "$ref": "#/$defs/risk"
        },
        "permissions": {
          "$ref": "#/$defs/permissions"
        },
        "errors": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/error_declaration"
          }
        }
      }
    },

    "execution": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "mode",
        "timeout_ms",
        "idempotent",
        "side_effects",
        "rollback_supported",
        "requires_confirmation"
      ],
      "properties": {
        "mode": {
          "type": "string",
          "enum": [
            "sync",
            "async",
            "streaming",
            "scheduled",
            "event_driven"
          ]
        },
        "timeout_ms": {
          "type": "integer",
          "minimum": 1
        },
        "idempotent": {
          "type": "boolean"
        },
        "side_effects": {
          "type": "boolean"
        },
        "rollback_supported": {
          "type": "boolean"
        },
        "requires_confirmation": {
          "type": "boolean"
        },
        "supports_cancellation": {
          "type": "boolean"
        },
        "execution_guarantee": {
          "type": "string",
          "enum": [
            "best_effort",
            "at_most_once",
            "at_least_once",
            "exactly_once"
          ]
        }
      }
    },

    "risk": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "level",
        "categories",
        "description"
      ],
      "properties": {
        "level": {
          "type": "string",
          "enum": [
            "none",
            "low",
            "medium",
            "high",
            "critical"
          ]
        },
        "categories": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": [
              "read_only",
              "state_modifying",
              "destructive",
              "external_communication",
              "sensitive_data_access",
              "financial",
              "legal",
              "security_sensitive",
              "network_access",
              "filesystem_access",
              "code_execution",
              "operator_visible",
              "irreversible"
            ]
          },
          "uniqueItems": true
        },
        "description": {
          "type": "string",
          "minLength": 1
        }
      }
    },

    "permissions": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "required_permissions",
        "operator_confirmation",
        "minimum_trust_state"
      ],
      "properties": {
        "required_permissions": {
          "type": "array",
          "items": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)+$"
          },
          "uniqueItems": true
        },
        "operator_confirmation": {
          "type": "string",
          "enum": [
            "none",
            "recommended",
            "required",
            "required_with_reason",
            "multi_party_required"
          ]
        },
        "minimum_trust_state": {
          "type": "string",
          "enum": [
            "unknown",
            "discovered",
            "verified",
            "trusted",
            "restricted",
            "suspended",
            "revoked"
          ]
        }
      }
    },

    "error_declaration": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "code",
        "description"
      ],
      "properties": {
        "code": {
          "type": "string",
          "enum": [
            "validation_error",
            "schema_error",
            "unsupported_version",
            "invalid_invocation",
            "permission_denied",
            "policy_denied",
            "trust_failure",
            "confirmation_required",
            "node_revoked",
            "node_suspended",
            "execution_error",
            "timeout_error",
            "provider_unavailable",
            "transport_error",
            "cancellation_error",
            "rollback_error",
            "partial_failure",
            "unsupported_action",
            "unsupported_capability",
            "unsupported_transport",
            "version_mismatch",
            "incompatible_schema",
            "output_schema_error"
          ]
        },
        "description": {
          "type": "string",
          "minLength": 1
        }
      }
    },

    "transport": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "transport_id",
        "type",
        "endpoint",
        "security"
      ],
      "properties": {
        "transport_id": {
          "$ref": "#/$defs/identifier"
        },
        "type": {
          "type": "string",
          "enum": [
            "http",
            "https",
            "websocket",
            "ipc",
            "grpc",
            "message_bus",
            "local_socket",
            "custom"
          ]
        },
        "endpoint": {
          "type": "string",
          "minLength": 1
        },
        "security": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "auth_required",
            "tls_required"
          ],
          "properties": {
            "auth_required": {
              "type": "boolean"
            },
            "tls_required": {
              "type": "boolean"
            },
            "signed_invocations_required": {
              "type": "boolean"
            }
          }
        },
        "reliability": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "delivery_guarantee": {
              "type": "string",
              "enum": [
                "best_effort",
                "at_most_once",
                "at_least_once",
                "exactly_once"
              ]
            },
            "ordering_guarantee": {
              "type": "boolean"
            },
            "retry_supported": {
              "type": "boolean"
            }
          }
        }
      }
    },

    "governance": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "requires_policy_check",
        "audit_required",
        "operator_authority_required",
        "default_action_policy"
      ],
      "properties": {
        "requires_policy_check": {
          "type": "boolean"
        },
        "audit_required": {
          "type": "boolean"
        },
        "signed_invocations_required": {
          "type": "boolean"
        },
        "operator_authority_required": {
          "type": "boolean"
        },
        "default_action_policy": {
          "type": "string",
          "enum": [
            "deny",
            "defer",
            "allow"
          ]
        },
        "default_policy_profile": {
          "type": "string"
        }
      }
    },

    "compatibility": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "supported_manifest_versions"
      ],
      "properties": {
        "supported_manifest_versions": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string"
          },
          "uniqueItems": true
        },
        "supported_extensions": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "uniqueItems": true
        },
        "compatibility_status": {
          "type": "string",
          "enum": [
            "compatible",
            "compatible_with_warnings",
            "unsupported",
            "rejected"
          ]
        }
      }
    },

    "compliance": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "profile"
      ],
      "properties": {
        "profile": {
          "type": "string",
          "enum": [
            "minimal",
            "standard",
            "enhanced",
            "experimental"
          ]
        },
        "supported_features": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "uniqueItems": true
        }
      }
    },

    "audit": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "audit_enabled"
      ],
      "properties": {
        "audit_enabled": {
          "type": "boolean"
        },
        "supported_event_categories": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": [
              "discovery",
              "validation",
              "governance",
              "invocation",
              "execution",
              "transport",
              "registry",
              "identity",
              "operator",
              "security"
            ]
          },
          "uniqueItems": true
        }
      }
    },

    "integrity": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "signed": {
          "type": "boolean"
        },
        "signature_algorithm": {
          "type": "string"
        },
        "manifest_hash": {
          "type": "string"
        }
      }
    }
  }
}
```

### Notes for v0.1

This schema intentionally validates structure, not full behavioral correctness.

A manifest can pass this schema and still be rejected later by:

-	governance policy, 
-	trust evaluation, 
-	compatibility evaluation, 
-	operator decision, 
-	semantic review, 
-	extension handling, 
-	or provider-specific safety checks. 

The schema is the first gate, not the whole security model.

