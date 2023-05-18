# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""GitHub Actions Export charm integration tests."""

import logging

import pytest
import requests
from ops.model import ActiveStatus, Application
from pytest_operator.plugin import OpsTest

logger = logging.getLogger()


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_active(app: Application):
    """
    arrange: none.
    act: deploy all required charms and kubernetes pods for tests.
    assert: all charms and pods are deployed successfully.
    """
    # Application actually does have units
    assert app.units[0].workload_status == ActiveStatus.name  # type: ignore


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_githubactionsexporter_is_up(ops_test: OpsTest, app: Application):
    """
    arrange: all charms and pods are deployed successfully..
    act: make HTTP request to charm
    assert: HTTP request is successfully completed.
    """
    assert ops_test.model
    status = await ops_test.model.get_status()
    unit = list(status.applications[app.name].units)[0]
    address = status["applications"][app.name]["units"][unit]["address"]
    response = requests.get(f"http://{address}:8065/", timeout=10)
    assert response.status_code == 200
    assert "GitHub Actions Exporter" in response.text


async def test_with_ingress(
    ops_test: OpsTest,
    app: Application,
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
        headers={"Host": f"{ops_test.model_name}-{app.name}.{external_hostname}"},
        timeout=5,
    )
    assert response.status_code == 200
    assert "GitHub Actions Exporter" in response.text
