# UCI Reference Manifest Pack
### Draft v0.1

Below are the first canonical examples.
________________________________________
### 1. minimal_provider_manifest.json
   
```json
{
  "uci_manifest_version": "0.1",
  "node": {
    "node_id": "minimal_search_provider",
    "instance_id": "minimal_search_local_001",
    "display_name": "Minimal Search Provider",
    "node_type": "service",
    "version": "1.0.0"
  },
  "capabilities": [
    {
      "capability_id": "document_search",
      "version": "1.0",
      "category": "retrieval",
      "description": "Search indexed documents.",
      "actions": [
        {
          "action_id": "search_index",
          "description": "Search the document index.",
          "execution": {
            "mode": "sync",
            "timeout_ms": 10000,
            "idempotent": true,
            "side_effects": false,
            "rollback_supported": false,
            "requires_confirmation": false
          },
          "input_schema": {
            "type": "object",
            "required": ["query"],
            "properties": {
              "query": { "type": "string" }
            }
          },
          "output_schema": {
            "type": "object",
            "required": ["results"],
            "properties": {
              "results": { "type": "array" }
            }
          },
          "risk": {
            "level": "low",
            "categories": ["read_only"],
            "description": "Read-only search operation."
          },
          "permissions": {
            "required_permissions": ["documents.read"],
            "operator_confirmation": "none",
            "minimum_trust_state": "verified"
          },
          "errors": [
            {
              "code": "validation_error",
              "description": "Input failed validation."
            },
            {
              "code": "execution_error",
              "description": "Search failed."
            }
          ]
        }
      ]
    }
  ],
  "transports": [
    {
      "transport_id": "local_http",
      "type": "http",
      "endpoint": "http://127.0.0.1:8080",
      "security": {
        "auth_required": false,
        "tls_required": false
      }
    }
  ],
  "governance": {
    "requires_policy_check": true,
    "audit_required": true,
    "operator_authority_required": true,
    "default_action_policy": "deny"
  },
  "compatibility": {
    "supported_manifest_versions": ["0.1"]
  },
  "compliance": {
    "profile": "minimal"
  },
  "audit": {
    "audit_enabled": true
  },
  "extensions": {}
}
```
________________________________________

### 2. standard_provider_manifest.json

```json
{
  "uci_manifest_version": "0.1",
  "node": {
    "node_id": "librarian_pro",
    "instance_id": "librarian_pro_local_001",
    "display_name": "Librarian Pro",
    "description": "Offline document retrieval and analysis provider.",
    "node_type": "application",
    "vendor": "Example Vendor",
    "version": "2.4.0"
  },
  "capabilities": [
    {
      "capability_id": "document_search",
      "version": "1.0",
      "category": "retrieval",
      "description": "Search indexed documents.",
      "aliases": ["search_documents"],
      "actions": [
        {
          "action_id": "search_index",
          "version": "1.0",
          "description": "Search indexed document content.",
          "execution": {
            "mode": "sync",
            "timeout_ms": 15000,
            "idempotent": true,
            "side_effects": false,
            "rollback_supported": false,
            "requires_confirmation": false,
            "supports_cancellation": false,
            "execution_guarantee": "at_most_once"
          },
          "input_schema": {
            "type": "object",
            "required": ["query"],
            "properties": {
              "query": { "type": "string" },
              "top_k": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 10
              }
            }
          },
          "output_schema": {
            "type": "object",
            "required": ["results", "count"],
            "properties": {
              "results": { "type": "array" },
              "count": { "type": "integer" }
            }
          },
          "risk": {
            "level": "low",
            "categories": ["read_only"],
            "description": "Reads indexed content without modifying state."
          },
          "permissions": {
            "required_permissions": ["documents.read"],
            "operator_confirmation": "none",
            "minimum_trust_state": "verified"
          },
          "errors": [
            {
              "code": "validation_error",
              "description": "Invalid search input."
            },
            {
              "code": "provider_unavailable",
              "description": "Search provider unavailable."
            },
            {
              "code": "execution_error",
              "description": "Search execution failed."
            }
          ]
        }
      ]
    }
  ],
  "transports": [
    {
      "transport_id": "local_http",
      "type": "http",
      "endpoint": "http://127.0.0.1:8080",
      "security": {
        "auth_required": true,
        "tls_required": false,
        "signed_invocations_required": false
      },
      "reliability": {
        "delivery_guarantee": "at_most_once",
        "ordering_guarantee": true,
        "retry_supported": true
      }
    }
  ],
  "governance": {
    "requires_policy_check": true,
    "audit_required": true,
    "signed_invocations_required": false,
    "operator_authority_required": true,
    "default_action_policy": "deny",
    "default_policy_profile": "strict_local"
  },
  "compatibility": {
    "supported_manifest_versions": ["0.1"],
    "supported_extensions": [],
    "compatibility_status": "compatible"
  },
  "compliance": {
    "profile": "standard",
    "supported_features": [
      "manifest_validation",
      "governance",
      "audit",
      "canonical_errors"
    ]
  },
  "audit": {
    "audit_enabled": true,
    "supported_event_categories": [
      "validation",
      "governance",
      "invocation",
      "execution",
      "transport"
    ]
  },
  "extensions": {}
}
```
________________________________________
### 3. orchestrator_manifest.json

```json
{
  "uci_manifest_version": "0.1",
  "node": {
    "node_id": "uci_orchestrator",
    "instance_id": "uci_orchestrator_local_001",
    "display_name": "UCI Orchestrator",
    "description": "Coordinates UCI-compatible providers under governance control.",
    "node_type": "orchestrator",
    "version": "1.0.0"
  },
  "capabilities": [
    {
      "capability_id": "capability_orchestration",
      "version": "1.0",
      "category": "governance",
      "description": "Discover, validate, and invoke UCI capabilities.",
      "actions": [
        {
          "action_id": "validate_manifest",
          "description": "Validate a UCI manifest.",
          "execution": {
            "mode": "sync",
            "timeout_ms": 5000,
            "idempotent": true,
            "side_effects": false,
            "rollback_supported": false,
            "requires_confirmation": false
          },
          "input_schema": {
            "type": "object",
            "required": ["manifest"],
            "properties": {
              "manifest": { "type": "object" }
            }
          },
          "output_schema": {
            "type": "object",
            "required": ["valid"],
            "properties": {
              "valid": { "type": "boolean" },
              "errors": { "type": "array" }
            }
          },
          "risk": {
            "level": "low",
            "categories": ["read_only"],
            "description": "Validates metadata only."
          },
          "permissions": {
            "required_permissions": ["uci.validate"],
            "operator_confirmation": "none",
            "minimum_trust_state": "verified"
          },
          "errors": [
            {
              "code": "validation_error",
              "description": "Manifest failed validation."
            }
          ]
        }
      ]
    }
  ],
  "transports": [
    {
      "transport_id": "local_http",
      "type": "http",
      "endpoint": "http://127.0.0.1:8090",
      "security": {
        "auth_required": true,
        "tls_required": false
      }
    }
  ],
  "governance": {
    "requires_policy_check": true,
    "audit_required": true,
    "operator_authority_required": true,
    "default_action_policy": "deny"
  },
  "compatibility": {
    "supported_manifest_versions": ["0.1"]
  },
  "compliance": {
    "profile": "standard",
    "supported_features": [
      "manifest_validation",
      "capability_mounting",
      "policy_evaluation",
      "canonical_responses"
    ]
  },
  "audit": {
    "audit_enabled": true,
    "supported_event_categories": [
      "discovery",
      "validation",
      "governance",
      "invocation",
      "execution"
    ]
  },
  "extensions": {}
}
```
________________________________________
### 4. registry_manifest.json

```json
{
  "uci_manifest_version": "0.1",
  "node": {
    "node_id": "uci_registry",
    "instance_id": "uci_registry_local_001",
    "display_name": "UCI Registry",
    "description": "Indexes known UCI nodes and manifests.",
    "node_type": "registry",
    "version": "1.0.0"
  },
  "capabilities": [
    {
      "capability_id": "node_registry",
      "version": "1.0",
      "category": "identity",
      "description": "Register and query UCI node metadata.",
      "actions": [
        {
          "action_id": "query_nodes",
          "description": "Query known registry entries.",
          "execution": {
            "mode": "sync",
            "timeout_ms": 5000,
            "idempotent": true,
            "side_effects": false,
            "rollback_supported": false,
            "requires_confirmation": false
          },
          "input_schema": {
            "type": "object",
            "properties": {
              "capability_id": { "type": "string" },
              "trust_state": { "type": "string" }
            }
          },
          "output_schema": {
            "type": "object",
            "required": ["nodes"],
            "properties": {
              "nodes": { "type": "array" }
            }
          },
          "risk": {
            "level": "low",
            "categories": ["read_only"],
            "description": "Reads registry metadata only."
          },
          "permissions": {
            "required_permissions": ["registry.read"],
            "operator_confirmation": "none",
            "minimum_trust_state": "verified"
          },
          "errors": [
            {
              "code": "validation_error",
              "description": "Invalid registry query."
            },
            {
              "code": "execution_error",
              "description": "Registry query failed."
            }
          ]
        }
      ]
    }
  ],
  "transports": [
    {
      "transport_id": "local_http",
      "type": "http",
      "endpoint": "http://127.0.0.1:8091",
      "security": {
        "auth_required": true,
        "tls_required": false
      }
    }
  ],
  "governance": {
    "requires_policy_check": true,
    "audit_required": true,
    "operator_authority_required": true,
    "default_action_policy": "deny"
  },
  "compatibility": {
    "supported_manifest_versions": ["0.1"]
  },
  "compliance": {
    "profile": "standard",
    "supported_features": [
      "registry",
      "trust_visibility",
      "capability_indexing"
    ]
  },
  "audit": {
    "audit_enabled": true,
    "supported_event_categories": [
      "registry",
      "identity",
      "validation"
    ]
  },
  "extensions": {}
}
```

________________________________________
### 5. policy_engine_manifest.json

```json
{
  "uci_manifest_version": "0.1",
  "node": {
    "node_id": "uci_policy_engine",
    "instance_id": "uci_policy_engine_local_001",
    "display_name": "UCI Policy Engine",
    "description": "Evaluates policy decisions for UCI invocations.",
    "node_type": "policy_engine",
    "version": "1.0.0"
  },
  "capabilities": [
    {
      "capability_id": "policy_validate",
      "version": "1.0",
      "category": "governance",
      "description": "Evaluate policy decisions for invocation requests.",
      "actions": [
        {
          "action_id": "evaluate_invocation",
          "description": "Evaluate whether an invocation should be allowed, restricted, deferred, or denied.",
          "execution": {
            "mode": "sync",
            "timeout_ms": 5000,
            "idempotent": true,
            "side_effects": false,
            "rollback_supported": false,
            "requires_confirmation": false
          },
          "input_schema": {
            "type": "object",
            "required": ["invocation", "context"],
            "properties": {
              "invocation": { "type": "object" },
              "context": { "type": "object" }
            }
          },
          "output_schema": {
            "type": "object",
            "required": ["decision"],
            "properties": {
              "decision": {
                "type": "string",
                "enum": ["allow", "allow_with_restrictions", "defer", "deny"]
              },
              "reason": { "type": "string" }
            }
          },
          "risk": {
            "level": "medium",
            "categories": ["security_sensitive"],
            "description": "Produces governance decisions but does not execute actions."
          },
          "permissions": {
            "required_permissions": ["policy.evaluate"],
            "operator_confirmation": "none",
            "minimum_trust_state": "trusted"
          },
          "errors": [
            {
              "code": "policy_denied",
              "description": "Policy denied the request."
            },
            {
              "code": "execution_error",
              "description": "Policy evaluation failed."
            }
          ]
        }
      ]
    }
  ],
  "transports": [
    {
      "transport_id": "local_http",
      "type": "http",
      "endpoint": "http://127.0.0.1:8092",
      "security": {
        "auth_required": true,
        "tls_required": false,
        "signed_invocations_required": false
      }
    }
  ],
  "governance": {
    "requires_policy_check": true,
    "audit_required": true,
    "operator_authority_required": true,
    "default_action_policy": "deny"
  },
  "compatibility": {
    "supported_manifest_versions": ["0.1"]
  },
  "compliance": {
    "profile": "standard",
    "supported_features": [
      "policy_evaluation",
      "trust_evaluation",
      "permission_evaluation",
      "audit"
    ]
  },
  "audit": {
    "audit_enabled": true,
    "supported_event_categories": [
      "governance",
      "operator",
      "security"
    ]
  },
  "extensions": {}
}
```
________________________________________
### 6. adapter_manifest.json

```json
{
  "uci_manifest_version": "0.1",
  "node": {
    "node_id": "legacy_api_adapter",
    "instance_id": "legacy_api_adapter_local_001",
    "display_name": "Legacy API Adapter",
    "description": "Wraps a legacy API with UCI-compatible capability declarations.",
    "node_type": "adapter",
    "version": "1.0.0"
  },
  "capabilities": [
    {
      "capability_id": "external_service_bridge",
      "version": "1.0",
      "category": "communication",
      "description": "Bridge requests to a legacy external service.",
      "actions": [
        {
          "action_id": "send_request",
          "description": "Send a governed request to the wrapped service.",
          "execution": {
            "mode": "sync",
            "timeout_ms": 20000,
            "idempotent": false,
            "side_effects": true,
            "rollback_supported": false,
            "requires_confirmation": true
          },
          "input_schema": {
            "type": "object",
            "required": ["request"],
            "properties": {
              "request": { "type": "object" }
            }
          },
          "output_schema": {
            "type": "object",
            "properties": {
              "response": { "type": "object" }
            }
          },
          "risk": {
            "level": "high",
            "categories": [
              "external_communication",
              "network_access",
              "state_modifying"
            ],
            "description": "May communicate with and modify external service state."
          },
          "permissions": {
            "required_permissions": ["network.external"],
            "operator_confirmation": "required",
            "minimum_trust_state": "trusted"
          },
          "errors": [
            {
              "code": "transport_error",
              "description": "External service transport failed."
            },
            {
              "code": "execution_error",
              "description": "External service request failed."
            },
            {
              "code": "confirmation_required",
              "description": "Operator approval required."
            }
          ]
        }
      ]
    }
  ],
  "transports": [
    {
      "transport_id": "local_http",
      "type": "http",
      "endpoint": "http://127.0.0.1:8093",
      "security": {
        "auth_required": true,
        "tls_required": false
      }
    }
  ],
  "governance": {
    "requires_policy_check": true,
    "audit_required": true,
    "operator_authority_required": true,
    "default_action_policy": "deny"
  },
  "compatibility": {
    "supported_manifest_versions": ["0.1"]
  },
  "compliance": {
    "profile": "standard",
    "supported_features": [
      "adapter",
      "governance",
      "audit"
    ]
  },
  "audit": {
    "audit_enabled": true,
    "supported_event_categories": [
      "governance",
      "execution",
      "transport",
      "security"
    ]
  },
  "extensions": {}
}
```
________________________________________
### 7. non_ai_service_manifest.json

```json
{
  "uci_manifest_version": "0.1",
  "node": {
    "node_id": "file_cleanup_service",
    "instance_id": "file_cleanup_local_001",
    "display_name": "File Cleanup Service",
    "description": "Non-AI local file cleanup utility.",
    "node_type": "service",
    "version": "1.0.0"
  },
  "capabilities": [
    {
      "capability_id": "file_management",
      "version": "1.0",
      "category": "storage",
      "description": "Manage local files under governed conditions.",
      "actions": [
        {
          "action_id": "delete_file",
          "description": "Delete a specified local file.",
          "execution": {
            "mode": "sync",
            "timeout_ms": 10000,
            "idempotent": false,
            "side_effects": true,
            "rollback_supported": false,
            "requires_confirmation": true
          },
          "input_schema": {
            "type": "object",
            "required": ["path"],
            "properties": {
              "path": { "type": "string" }
            }
          },
          "output_schema": {
            "type": "object",
            "required": ["deleted"],
            "properties": {
              "deleted": { "type": "boolean" }
            }
          },
          "risk": {
            "level": "critical",
            "categories": [
              "filesystem_access",
              "destructive",
              "irreversible"
            ],
            "description": "Deletes filesystem data and may be irreversible."
          },
          "permissions": {
            "required_permissions": ["files.delete"],
            "operator_confirmation": "required_with_reason",
            "minimum_trust_state": "trusted"
          },
          "errors": [
            {
              "code": "permission_denied",
              "description": "Caller lacks permission to delete files."
            },
            {
              "code": "confirmation_required",
              "description": "Operator confirmation required."
            },
            {
              "code": "execution_error",
              "description": "File deletion failed."
            }
          ]
        }
      ]
    }
  ],
  "transports": [
    {
      "transport_id": "local_ipc",
      "type": "ipc",
      "endpoint": "uci://local/file_cleanup",
      "security": {
        "auth_required": true,
        "tls_required": false,
        "signed_invocations_required": true
      }
    }
  ],
  "governance": {
    "requires_policy_check": true,
    "audit_required": true,
    "signed_invocations_required": true,
    "operator_authority_required": true,
    "default_action_policy": "deny"
  },
  "compatibility": {
    "supported_manifest_versions": ["0.1"]
  },
  "compliance": {
    "profile": "standard",
    "supported_features": [
      "governance",
      "audit",
      "signed_invocations"
    ]
  },
  "audit": {
    "audit_enabled": true,
    "supported_event_categories": [
      "governance",
      "execution",
      "security",
      "operator"
    ]
  },
  "extensions": {}
}
```

