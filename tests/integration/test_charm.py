# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""GitHub Actions Export charm integration tests."""

import logging
import typing

import pytest
import requests
from ops.model import ActiveStatus, Application
from pytest_operator.plugin import OpsTest

# mypy has trouble to inferred types for variables that are initialized in subclasses.
ACTIVE_STATUS_NAME = typing.cast(str, ActiveStatus.name)  # type: ignore

logger = logging.getLogger()


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_active(gh_app: Application):
    """
    arrange: none.
    act: deploy all required charms and kubernetes pods for tests.
    assert: all charms and pods are deployed successfully.
    """
    # Application actually does have units
    assert gh_app.units[0].workload_status == ACTIVE_STATUS_NAME  # type: ignore


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_githubactionsexporter_is_up(ops_test: OpsTest, gh_app: Application):
    """
    arrange: all charms and pods are deployed successfully..
    act: make HTTP request to charm
    assert: HTTP request is successfully completed.
    """
    assert ops_test.model
    status = await ops_test.model.get_status()
    unit = list(status.applications[gh_app.name].units)[0]
    address = status["applications"][gh_app.name]["units"][unit]["address"]
    response = requests.get(f"http://{address}:8065/", timeout=10)
    assert response.status_code == 200
    assert "GitHub Actions Exporter" in response.text


async def test_with_ingress(
    ops_test: OpsTest,
    gh_app: Application,
    traefik_app_name: str,
    external_hostname: str,
    get_unit_ips,
):
    """
    arrange: build and deploy the github actions charm, and deploy the ingress.
    act: relate the ingress charm with the github actions charm.
    assert: requesting the charm through traefik should return a correct response
    """
    assert ops_test.model
    traefik_ip = next(await get_unit_ips(traefik_app_name))
    response = requests.get(
        f"http://{traefik_ip}",
        headers={"Host": f"{ops_test.model_name}-{gh_app.name}.{external_hostname}"},
        timeout=5,
    )
    assert response.status_code == 200
    assert "GitHub Actions Exporter" in response.text


@pytest.mark.usefixtures("nginx_integrator_app")
async def test_with_nginx_route(
    ops_test: OpsTest,
    gh_app: Application,
    nginx_integrator_app_name: str,
):
    """
    arrange: build and deploy the Synapse charm, and deploy the nginx-integrator.
    act: relate the nginx-integrator charm with the Synapse charm.
    assert: requesting the charm through nginx-integrator should return a correct response.
    """
    assert ops_test.model
    await ops_test.model.add_relation(
        f"{gh_app.name}:nginx-route", f"{nginx_integrator_app_name}:nginx-route"
    )
    await ops_test.model.wait_for_idle(status=ACTIVE_STATUS_NAME)

    response = requests.get("http://127.0.0.1/", headers={"Host": gh_app.name}, timeout=5)
    assert response.status_code == 200
    assert "GitHub Actions Exporter" in response.text
