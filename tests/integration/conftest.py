# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for GitHub Actions Export charm integration tests."""

import asyncio
from pathlib import Path

import pytest_asyncio
import yaml
from ops.model import WaitingStatus
from pytest import Config, fixture
from pytest_operator.plugin import OpsTest


@fixture(scope="module", name="metadata")
def metadata_fixture():
    """Provides charm metadata."""
    yield yaml.safe_load(Path("./metadata.yaml").read_text("utf-8"))


@fixture(scope="module", name="app_name")
def app_name_fixture(metadata):
    """Provides app name from the metadata."""
    yield metadata["name"]


@pytest_asyncio.fixture(scope="module")
async def app(
    ops_test: OpsTest,
    app_name: str,
    pytestconfig: Config,
):
    """GitHub Actions Export charm used for integration testing.

    Builds the charm and deploys it and the relations it depends on.
    """
    assert ops_test.model
    # Deploy relations to speed up overall execution
    dependencies = asyncio.gather(
        ops_test.model.deploy("nginx-ingress-integrator", trust=True),
    )

    resources = {
        "github-actions-exporter-image": pytestconfig.getoption("--github-actions-exporter-image"),
    }
    charm = await ops_test.build_charm(".")
    application = await ops_test.model.deploy(
        charm,
        resources=resources,
        application_name=app_name,
        series="focal"
    )

    await dependencies
    # Add required relations, mypy has difficulty with WaitingStatus
    expected_name = WaitingStatus.name  # type: ignore
    assert ops_test.model.applications[app_name].units[0].workload_status == expected_name
    await asyncio.gather(
        ops_test.model.add_relation(app_name, "nginx-ingress-integrator"),
    )
    await ops_test.model.wait_for_idle(status="active", raise_on_error=False)

    yield application
