#!/usr/bin/env python3

# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""State of the Charm."""
from ops.charm import CharmBase


class CharmState:
    """State of the Charm."""

    def __init__(self, charm: CharmBase) -> None:
        """Construct."""
        self._charm = charm

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

    @property
    def user(self) -> str:
        """Return the github exporter user that will run the exporter.

        Returns:
            str: user name.
        """
        return "gh_exporter"

    @property
    def container_name(self) -> str:
        """Return the github exporter container name.

        Returns:
            str: container name.
        """
        return "github-actions-exporter"

    @property
    def metrics_port(self) -> int:
        """Return the port to get metrics from the github exporter.

        Returns:
            int: port number.
        """
        return 9101

    @property
    def webhook_port(self) -> int:
        """Return the github exporter user that will run the exporter.

        Returns:
            int: port number.
        """
        return 8065
