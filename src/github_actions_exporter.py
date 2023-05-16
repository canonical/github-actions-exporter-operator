#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Helper module used to manage interactions with GitHub Actions Exporter."""

from re import findall

from ops.model import Container


def get_exporter_version(container: Container) -> str:
    """Retrieve the current version of GitHub Actions Exporter.

    Returns:
        The  GitHub Actions Exporter version installed.
    """
    process = container.exec(
        ["/srv/gh_exporter/github-actions-exporter", "--version"], user="gh_exporter"
    )
    version_string, _ = process.wait_output()
    version = findall("[0-9a-f]{5,40}", version_string)
    return version[0][0:7] if version else ""
