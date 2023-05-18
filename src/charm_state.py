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
    def github_exporter_command(self) -> str:
        """Return the github exporter command.

        Returns:
            str: github exporter command path.
        """
        return "/srv/gh_exporter/github-actions-exporter"

    @property
    def github_exporter_user(self) -> str:
        """Return the github exporter user that will run the exporter.

        Returns:
            str: user name.
        """
        return "gh_exporter"
