"""
UCI Core Error Types
All exceptions raised by the UCI stack live here.
"""


class UCIError(Exception):
    """Base for all UCI errors."""
    pass


class UCIManifestError(UCIError):
    """Manifest is missing required fields or structurally invalid."""
    pass


class UCIValidationError(UCIError):
    """Manifest passed structure checks but failed semantic validation."""
    pass


class UCICompatibilityError(UCIError):
    """Manifest version or capability schema is incompatible."""
    pass


class UCIGovernanceError(UCIError):
    """Governance evaluation denied or deferred the operation."""

    def __init__(self, message: str, outcome: str = "deny", reason: str = ""):
        super().__init__(message)
        self.outcome = outcome
        self.reason = reason


class UCITrustError(UCIError):
    """Trust state is insufficient for the requested operation."""

    def __init__(self, message: str, current_state: str = "", required_state: str = ""):
        super().__init__(message)
        self.current_state = current_state
        self.required_state = required_state


class UCIHandshakeError(UCIError):
    """Handshake failed at a specific lifecycle stage."""

    def __init__(self, message: str, stage: str = ""):
        super().__init__(message)
        self.stage = stage


class UCIInvocationError(UCIError):
    """Action invocation failed — permission, schema, or runtime."""

    def __init__(self, message: str, action_id: str = "", error_code: str = ""):
        super().__init__(message)
        self.action_id = action_id
        self.error_code = error_code


class UCITransportError(UCIError):
    """Transport layer failure — connection, timeout, serialisation."""
    pass


class UCIRegistryError(UCIError):
    """Registry operation failed — duplicate node, not found, etc."""
    pass
