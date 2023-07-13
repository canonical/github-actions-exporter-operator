# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for GitHub Actions Export charm tests."""


def pytest_addoption(parser):
    """Parse additional pytest options."""
    parser.addoption("--github-actions-exporter-image", action="store")
