"""
Shared pytest fixtures for the UCI test rig.
Every test gets a clean engine stack — no shared state between tests.
"""

import pytest
from uci.core.audit import AuditLog
from uci.core.registry import UCIRegistry
from uci.core.governance import PolicyEngine
from uci.core.handshake import HandshakeEngine
from uci.sdk.provider import UCIOrchestrator
from test_rig.mock_providers.provider_alpha import ProviderAlpha
from test_rig.mock_providers.provider_beta import ProviderBeta
from test_rig.mock_providers.provider_gamma import (
    ProviderGammaMissingNodeId,
    ProviderGammaUnsupportedVersion,
    ProviderGammaInvalidRisk,
    ProviderGammaInvalidNodeType,
    ProviderGammaNoCaps,
)


@pytest.fixture
def audit():
    return AuditLog()


@pytest.fixture
def registry():
    return UCIRegistry()


@pytest.fixture
def policy(audit):
    return PolicyEngine(audit=audit)


@pytest.fixture
def handshake(policy, registry, audit):
    return HandshakeEngine(policy=policy, registry=registry, audit=audit)


@pytest.fixture
def orchestrator(policy, registry, audit):
    return UCIOrchestrator(policy=policy, registry=registry, audit=audit)


@pytest.fixture
def alpha():
    return ProviderAlpha()


@pytest.fixture
def beta():
    return ProviderBeta()


@pytest.fixture
def gamma_missing_id():
    return ProviderGammaMissingNodeId()


@pytest.fixture
def gamma_bad_version():
    return ProviderGammaUnsupportedVersion()


@pytest.fixture
def gamma_invalid_risk():
    return ProviderGammaInvalidRisk()


@pytest.fixture
def gamma_invalid_type():
    return ProviderGammaInvalidNodeType()


@pytest.fixture
def gamma_no_caps():
    return ProviderGammaNoCaps()
