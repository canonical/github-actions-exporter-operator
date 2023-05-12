#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Helper to interact with NGINX."""

from typing import Dict

from charms.nginx_ingress_integrator.v0.nginx_route import require_nginx_route
from ops.charm import CharmBase

from state import State

GH_EXPORTER_WEBHOOK_PORT = 8065
SVC_HOSTNAME = "service-hostname"
SVC_NAME = "service-name"
SVC_PORT = "service-port"


def set_nginx_route(charm: CharmBase, state: State):
    """Set require_nginx_route."""
    service_hostname = state.external_hostname or charm.app.name
    service_name = charm.app.name
    service_port = GH_EXPORTER_WEBHOOK_PORT

    if has_nginx_route_relation(charm) and has_app_data(charm):
        rel = charm.model.relations["nginx-route"][0].data[charm.app]
        if has_required_fields(rel):
            service_hostname = state.external_hostname or charm.app.name
            service_name = rel[SVC_NAME]
            service_port = rel[SVC_PORT]

    require_nginx_route(
        charm=charm,
        service_hostname=service_hostname,
        service_name=service_name,
        service_port=service_port,
    )


def has_required_fields(rel: Dict) -> bool:
    """Check for required fields in relation.

    Args:
        rel: relation to check
    Returns:
        Returns true if all fields exist
    """
    return all(key in rel for key in (SVC_HOSTNAME, SVC_NAME, SVC_PORT))


def has_app_data(charm) -> bool:
    """Check for app in relation data.

    Returns:
        Returns true if app data exist
    """
    return charm.app in charm.model.relations["nginx-route"][0].data


def has_nginx_route_relation(charm) -> bool:
    """Check for nginx-route relation.

    Returns:
        Returns true if nginx-route relation exist
    """
    return "nginx-route" in charm.model.relations and len(charm.model.relations["nginx-route"]) > 0
