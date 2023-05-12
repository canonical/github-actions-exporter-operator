#!/usr/bin/env python3

# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Types used by the charm."""
from typing import Protocol


# There is no public method for this class.
class CharmState(Protocol):  # pylint: disable=too-few-public-methods
    """Types used by the charm."""

    github_webhook_token: str
    github_api_token: str
    github_org: str
