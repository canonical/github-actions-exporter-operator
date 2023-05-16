#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Helper module used to manage interactions with GitHub Actions Exporter."""

from re import findall

from ops.model import Container

from charm_state import CharmState


def exporter_environment(state: CharmState) -> dict[str, str]:
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


def exporter_version(container: Container, state: CharmState) -> str:
    """Retrieve the current version of GitHub Actions Exporter.

    Args:
        container: The container of the charm.
        state: The state of the charm.

    Returns:
        The  GitHub Actions Exporter version installed.
    """
    process = container.exec([state.github_exporter_command, "--version"], user="gh_exporter")
    version_string, _ = process.wait_output()
    version = findall("[0-9a-f]{5,40}", version_string)
    return version[0][0:7] if version else ""


def is_configuration_valid(state: CharmState) -> bool:
    """Check if there is no empty configuration.

    Args:
        state: The state of the charm.

    Returns:
        True if they are all set
    """
    github_webhook_token = state.github_webhook_token
    github_api_token = state.github_api_token
    github_org = state.github_org
    return all([github_webhook_token, github_api_token, github_org])
