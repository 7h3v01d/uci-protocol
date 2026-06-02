"""
UCI — Universal Capability Interface
Python Reference Implementation · v0.1.0-alpha

The four protocol objects:
    UCIManifest     — identity and capability contract
    UCIInvocation   — canonical request object
    UCIResponse     — canonical answer envelope
    UCIAuditSession — tamper-evident session record

Quick start:
    from uci.sdk.provider import UCIProvider, UCIOrchestrator
    from uci.core.manifest import UCIManifest, UCINode, UCICapability
    from uci.core.invocation import UCIInvocation
    from uci.core.response import UCIResponse, UCIErrorCode
    from uci.core.audit import AuditLog, UCIAuditSession
"""

__version__ = "0.1.0-alpha"
__author__  = "Leon Priest"
__license__ = "Apache-2.0"
__spec_version__ = "0.1"
