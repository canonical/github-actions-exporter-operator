#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Helper module used to manage interactions with GitHub Actions Exporter."""

from re import findall
from typing import Dict

from ops.model import Container

from charm_state import CharmState

COMMAND_PATH = "/srv/gh_exporter/github-actions-exporter"
WEBHOOK_PORT = 8065


def environment(state: CharmState) -> Dict[str, str]:
    """Generate a environment dictionary from the charm configurations.

    Args:
        state: The state of the charm.

    Returns:
        A dictionary representing the GitHub Actions Exporter environment variables.
    """
    return {
        "GITHUB_WEBHOOK_TOKEN": f"{state.github_webhook_token}",
        "GITHUB_API_TOKEN": f"{state.github_api_token}",
        "GITHUB_ORG": f"{state.github_org}",
    }


def version(container: Container, state: CharmState) -> str:
    """Retrieve the current version of GitHub Actions Exporter.

    Args:
        container: The container of the charm.
        state: The state of the charm.

    Returns:
        The  GitHub Actions Exporter version installed.
    """
    process = container.exec([COMMAND_PATH, "--version"], user=state.user)
    version_string, _ = process.wait_output()
    version_found = findall("[0-9a-f]{5,40}", version_string)
    return version_found[0][0:7] if version_found else ""


def is_configuration_valid(state: CharmState) -> bool:
    """Check if there is no empty configuration.

    Args:
        state: The state of the charm.

    Returns:
        True if they are all set
    """
    return all([state.github_webhook_token, state.github_api_token, state.github_org])
