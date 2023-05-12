#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Helper class used to manage interactions with GitHub Actions Exporter."""

from re import findall


# There is only one method for this class.
class GitHubActionsExporter:  # pylint: disable=too-few-public-methods
    """This class handles interactions with GitHub Actions Exporter."""

    def __init__(
        self,
        charm,
    ):
        """Construct."""
        self._charm = charm

    def get_exporter_version(self) -> str:
        """Retrieve the current version of GitHub Actions Exporter.

        Returns:
            The  GitHub Actions Exporter version installed.
        """
        container = self._charm.unit.get_container("github-actions-exporter")
        process = container.exec(
            ["/srv/gh_exporter/github-actions-exporter", "--version"], user="gh_exporter"
        )
        version_string, _ = process.wait_output()
        version = findall("[0-9a-f]{5,40}", version_string)
        return version[0][0:7] if version else ""
