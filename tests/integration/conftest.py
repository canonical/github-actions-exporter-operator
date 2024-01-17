# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for GitHub Actions Export charm integration tests."""

import asyncio
import json
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


@fixture(scope="module", name="external_hostname")
def external_hostname_fixture() -> str:
    """Return the external hostname for ingress-related tests."""
    return "juju.test"


@fixture(scope="module", name="traefik_app_name")
def traefik_app_name_fixture() -> str:
    """Return the name of the traefik application deployed for tests."""
    return "traefik-k8s"


@pytest_asyncio.fixture(scope="module", name="get_unit_ips")
async def get_unit_ips_fixture(ops_test: OpsTest):
    """Return an async function to retrieve unit ip addresses of a certain application."""

    async def get_unit_ips(application_name: str):
        """Retrieve unit ip addresses of a certain application.

        Returns:
            a list containing unit ip addresses.
        """
        _, status, _ = await ops_test.juju("status", "--format", "json")
        status = json.loads(status)
        units = status["applications"][application_name]["units"]
        return (
            unit_status["address"]
            for _, unit_status in sorted(units.items(), key=lambda kv: int(kv[0].split("/")[-1]))
        )

    return get_unit_ips


@pytest_asyncio.fixture(scope="module", name="gh_app")
async def gh_app_fixture(
    ops_test: OpsTest,
    app_name: str,
    pytestconfig: Config,
    external_hostname: str,
    traefik_app_name: str,
):
    """GitHub Actions Export charm used for integration testing.

    Builds the charm and deploys it and the relations it depends on.
    """
    assert ops_test.model
    # Deploy relations to speed up overall execution
    dependencies = asyncio.gather(
        ops_test.model.deploy(
            traefik_app_name,
            trust=True,
            config={
                "external_hostname": external_hostname,
                "routing_mode": "subdomain",
            },
        ),
    )

    resources = {
        "github-actions-exporter-image": pytestconfig.getoption("--github-actions-exporter-image"),
    }
    charm = pytestconfig.getoption("--charm-file")
    async with ops_test.fast_forward():
        application = await ops_test.model.deploy(
            f"./{charm}", resources=resources, application_name=app_name, series="focal"
        )
        await dependencies
    # Add required relations, mypy has difficulty with WaitingStatus
    expected_name = WaitingStatus.name  # type: ignore
    assert ops_test.model.applications[app_name].units[0].workload_status == expected_name
    await asyncio.gather(
        ops_test.model.add_relation(app_name, traefik_app_name),
    )
    await ops_test.model.wait_for_idle(status="active", raise_on_error=False)

    yield application


@fixture(scope="module", name="nginx_integrator_app_name")
def nginx_integrator_app_name_fixture() -> str:
    """Return the name of the nginx integrator application deployed for tests."""
    return "nginx-ingress-integrator"


@pytest_asyncio.fixture(scope="module", name="nginx_integrator_app")
async def nginx_integrator_app_fixture(
    ops_test: OpsTest,
    gh_app,  # pylint: disable=unused-argument
    nginx_integrator_app_name: str,
):
    """Deploy nginx-ingress-integrator."""
    assert ops_test.model
    nginx_integrator_app = await ops_test.model.deploy(
        "nginx-ingress-integrator",
        application_name=nginx_integrator_app_name,
        trust=True,
    )
    async with ops_test.fast_forward():
        await ops_test.model.wait_for_idle(raise_on_blocked=True)
    return nginx_integrator_app
