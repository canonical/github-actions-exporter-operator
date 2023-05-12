#!/usr/bin/env python3

# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm for GitHub Actions Exporter on kubernetes."""

import logging
from typing import Dict

from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from ops.charm import CharmBase, HookEvent, WorkloadEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus

from github_actions_exporter import GitHubActionsExporter
from ingress import set_nginx_route
from state import State
from types_ import CharmState

logger = logging.getLogger(__name__)

GH_EXPORTER_METRICS_PORT = 9101


class GithubActionsExporterOperatorCharm(CharmBase):
    """Charm the service."""

    def __init__(self, *args) -> None:
        """Construct."""
        super().__init__(*args)
        self.framework.observe(
            self.on.github_actions_exporter_pebble_ready,
            self._on_github_actions_exporter_pebble_ready,
        )
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.state: CharmState = State(self)
        set_nginx_route(self, self.state)
        self._metrics_endpoint = MetricsEndpointProvider(
            self,
            jobs=[
                {
                    "static_configs": [
                        {
                            "targets": [
                                f"*:{GH_EXPORTER_METRICS_PORT}",
                            ]
                        }
                    ]
                }
            ],
        )

    @property
    def _github_actions_exporter(self) -> GitHubActionsExporter:
        """Returns an instance of the GitHub Actions Exporter object.

        Returns:
            Instance of GitHub Actions Exporter
        """
        return GitHubActionsExporter(self)

    def _on_github_actions_exporter_pebble_ready(self, event: WorkloadEvent):
        """Define and start a workload using the Pebble API.

        Args:
            event: Event triggering after pebble is ready.
        """
        container = event.workload
        self.unit.status = MaintenanceStatus(f"Adding {container.name} layer to pebble")
        container.add_layer(container.name, self._pebble_layer, combine=True)
        container.replan()
        self.unit.status = ActiveStatus()
        self.unit.set_workload_version(self._github_actions_exporter.get_exporter_version())

    def _is_configuration_valid(self) -> bool:
        """Check if there is no empty configuration.

        Returns:
            True if they are all set
        """
        github_webhook_token = self.state.github_webhook_token
        github_api_token = self.state.github_api_token
        github_org = self.state.github_org
        return all([github_webhook_token, github_api_token, github_org])

    def _on_config_changed(self, event: HookEvent) -> None:
        """Handle changed configuration.

        Args:
            event: Event triggering after config is changed.
        """
        if not self._is_configuration_valid():
            self.model.unit.status = BlockedStatus("Configuration is not valid")
            event.defer()
            return
        container = self.unit.get_container("github-actions-exporter")
        if not container.can_connect():
            event.defer()
            self.unit.status = WaitingStatus("Waiting for pebble")
            return
        self.model.unit.status = MaintenanceStatus("Configuring pod")
        container.add_layer("github-actions-exporter", self._pebble_layer, combine=True)
        container.replan()
        self.unit.status = ActiveStatus()

    @property
    def _pebble_layer(self) -> Dict:
        """Return a dictionary representing a Pebble layer."""
        return {
            "summary": "GitHub Actions Exporter layer",
            "description": "pebble config layer for GitHub Actions Exporter",
            "services": {
                "github-actions-exporter": {
                    "override": "replace",
                    "summary": "github-actions-exporter",
                    "startup": "enabled",
                    "user": "gh_exporter",
                    "command": "/srv/gh_exporter/github-actions-exporter",
                    "environment": {
                        "GITHUB_WEBHOOK_TOKEN": f"{self.state.github_webhook_token}",
                        "GITHUB_API_TOKEN": f"{self.state.github_api_token}",
                        "GITHUB_ORG": f"{self.state.github_org}",
                    },
                }
            },
            "checks": {
                "github-actions-exporter-ready": {
                    "override": "replace",
                    "level": "ready",
                    "tcp": {"port": self.state.github_webhook_token},
                }
            },
        }


if __name__ == "__main__":  # pragma: nocover
    main(GithubActionsExporterOperatorCharm)
