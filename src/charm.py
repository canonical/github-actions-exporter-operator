#!/usr/bin/env python3

# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm for GitHub Actions Exporter on kubernetes."""

import logging
from re import findall
from typing import Dict

from charms.nginx_ingress_integrator.v0.nginx_route import require_nginx_route
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from ops.charm import CharmBase, HookEvent, WorkloadEvent
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus

from state import State
from types_ import CharmState

logger = logging.getLogger(__name__)

GH_EXPORTER_METRICS_PORT = 9101
GH_EXPORTER_WEBHOOK_PORT = 8065
SVC_HOSTNAME = "service-hostname"
SVC_NAME = "service-name"
SVC_PORT = "service-port"


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
        self._require_nginx_route()
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

    def _require_nginx_route(self):
        """Set require_nginx_route."""
        service_hostname = self.state.external_hostname or self.app.name
        service_name = self.app.name
        service_port = GH_EXPORTER_WEBHOOK_PORT

        if self._has_nginx_route_relation() and self._has_app_data():
            rel = self.model.relations["nginx-route"][0].data[self.app]
            if self._has_required_fields(rel):
                service_hostname = self.state.external_hostname or self.app.name
                service_name = rel[SVC_NAME]
                service_port = rel[SVC_PORT]

        require_nginx_route(
            charm=self,
            service_hostname=service_hostname,
            service_name=service_name,
            service_port=service_port,
        )

    def _has_required_fields(self, rel: Dict) -> bool:
        """Check for required fields in relation.

        Args:
            rel: relation to check
        Returns:
            Returns true if all fields exist
        """
        return all(key in rel for key in (SVC_HOSTNAME, SVC_NAME, SVC_PORT))

    def _has_app_data(self) -> bool:
        """Check for app in relation data.

        Returns:
            Returns true if app data exist
        """
        return self.app in self.model.relations["nginx-route"][0].data

    def _has_nginx_route_relation(self) -> bool:
        """Check for nginx-route relation.

        Returns:
            Returns true if nginx-route relation exist
        """
        return (
            "nginx-route" in self.model.relations and len(self.model.relations["nginx-route"]) > 0
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
        self.unit.set_workload_version(self._get_exporter_version())

    def _is_configuration_valid(self) -> bool:
        """Check if there is no empty configuration.

        Returns:
            True if they are all set
        """
        github_webhook_token = self.state.github_webhook_token
        github_api_token = self.state.github_api_token
        github_org = self.state.github_org
        return all([github_webhook_token, github_api_token, github_org])

    def _get_exporter_version(self) -> str:
        """Retrieve the current version of GitHub Actions Exporter.

        Returns:
            The  GitHub Actions Exporter version installed.
        """
        container = self.unit.get_container("github-actions-exporter")
        process = container.exec(
            ["/srv/gh_exporter/github-actions-exporter", "--version"], user="gh_exporter"
        )
        version_string, _ = process.wait_output()
        version = findall("[0-9a-f]{5,40}", version_string)
        return version[0][0:7] if version else ""

    def _on_config_changed(self, event: HookEvent) -> None:
        """Handle changed configuration.

        Args:
            event: Event triggering after config is changed.
        """
        if self._is_configuration_valid():
            container = self.unit.get_container("github-actions-exporter")
            if container.can_connect():
                logger.info("Configuration has changed")
                self.model.unit.status = MaintenanceStatus("Configuring pod")
                container.add_layer("github-actions-exporter", self._pebble_layer, combine=True)
                container.replan()
                self.unit.status = ActiveStatus()
            else:
                event.defer()
                self.unit.status = WaitingStatus("Waiting for pebble")
        else:
            self.model.unit.status = BlockedStatus("Configuration is not valid")
            event.defer()
            return

    @property
    def _pebble_layer(self) -> Dict:
        """Return a dictionary representing a Pebble layer."""
        logger.info("using %s", self.state.github_webhook_token)
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
