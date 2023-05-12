#!/usr/bin/env python3

# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""State of the Charm."""
from ops.charm import CharmBase


class State:
    """State of the Charm."""

    def __init__(self, charm: CharmBase) -> None:
        """Construct."""
        self._charm = charm

    @property
    def external_hostname(self) -> str:
        """Return external_hostname config.

        Returns:
            str: external_hostname config.
        """
        return self._charm.config["external_hostname"]

    @property
    def github_webhook_token(self) -> str:
        """Return github_webhook_token config.

        Returns:
            str: github_webhook_token config.
        """
        return self._charm.config["github_webhook_token"]

    @property
    def github_api_token(self) -> str:
        """Return github_api_token config.

        Returns:
            str: github_api_token config.
        """
        return self._charm.config["github_api_token"]

    @property
    def github_org(self) -> str:
        """Return github_org config.

        Returns:
            str: github_org config.
        """
        return self._charm.config["github_org"]
