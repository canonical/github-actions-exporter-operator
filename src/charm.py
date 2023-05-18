#!/usr/bin/env python3

# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm for GitHub Actions Exporter on kubernetes."""

import logging
from typing import Dict

from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from charms.traefik_k8s.v1.ingress import IngressPerAppRequirer
from ops.charm import CharmBase, HookEvent, WorkloadEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus

import github_actions_exporter as gh_exporter
from charm_state import CharmState

logger = logging.getLogger(__name__)


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
        self.state: CharmState = CharmState(self)
        self.ingress = IngressPerAppRequirer(
            self,
            port=self.state.webhook_port,
            # We're forced to use the app's service endpoint
            # as the ingress per app interface currently always routes to the leader.
            # https://github.com/canonical/traefik-k8s-operator/issues/159
            # For juju >= 3.1.1, this could be used in combination with open-port for true load
            # balancing.
            host=f"{self.app.name}-endpoints.{self.model.name}.svc.cluster.local",
            strip_prefix=True,
        )
        self._metrics_endpoint = MetricsEndpointProvider(
            self,
            jobs=[
                {
                    "static_configs": [
                        {
                            "targets": [
                                f"*:{self.state.metrics_port}",
                            ]
                        }
                    ]
                }
            ],
        )

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
        version = gh_exporter.version(container, self.state)
        self.unit.set_workload_version(version)

    def _on_config_changed(self, event: HookEvent) -> None:
        """Handle changed configuration.

        Args:
            event: Event triggering after config is changed.
        """
        if not gh_exporter.is_configuration_valid(self.state):
            self.model.unit.status = BlockedStatus("Configuration is not valid")
            event.defer()
            return
        container = self.unit.get_container(self.state.container_name)
        if not container.can_connect():
            event.defer()
            self.unit.status = WaitingStatus("Waiting for pebble")
            return
        self.model.unit.status = MaintenanceStatus("Configuring pod")
        container.add_layer(self.state.container_name, self._pebble_layer, combine=True)
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
                    "user": self.state.user,
                    "command": gh_exporter.COMMAND_PATH,
                    "environment": gh_exporter.environment(self.state),
                }
            },
            "checks": {
                "github-actions-exporter-ready": {
                    "override": "replace",
                    "level": "ready",
                    "tcp": {"port": self.state.metrics_port},
                }
            },
        }


if __name__ == "__main__":  # pragma: nocover
    main(GithubActionsExporterOperatorCharm)
