# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""GitHub Actions Exporter charm unit tests."""

import typing
import unittest
from secrets import token_hex
from unittest.mock import MagicMock, patch

from ops.model import ActiveStatus, BlockedStatus, Container, WaitingStatus
from ops.testing import Harness

from charm import GH_EXPORTER_WEBHOOK_PORT, GithubActionsExporterOperatorCharm

TEST_MODEL_NAME = "test-github-actions-exporter"


class TestCharm(unittest.TestCase):
    """GitHub Actions Exporter charm unit tests."""

    def setUp(self):
        """Set up test environment."""
        self.harness = Harness(GithubActionsExporterOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.set_model_name(TEST_MODEL_NAME)
        self.harness.begin()

    @patch.object(Container, "exec")
    def test_config_changed(self, mock_container_exec):
        """
        arrange: charm created
        act: trigger a valid configuration change for the charm
        assert: the container and the service are running and properly configured
        """
        mock_container_exec.return_value = MagicMock(
            wait_output=MagicMock(return_value=("", None))
        )
        self.harness.update_config({"github_webhook_token": "foo"})
        self.harness.container_pebble_ready("github-actions-exporter")
        updated_plan = self.harness.get_container_pebble_plan("github-actions-exporter").to_dict()
        updated_plan_env = updated_plan["services"]["github-actions-exporter"]["environment"]
        self.assertEqual("foo", updated_plan_env["GITHUB_WEBHOOK_TOKEN"])
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())
        mock_container_exec.assert_any_call(
            ["/srv/gh_exporter/github-actions-exporter", "--version"],
            user="gh_exporter",
        )

    @patch.object(Container, "exec")
    def test_config_changed_when_config_invalid(self, mock_container_exec):
        """
        arrange: charm created and relations established
        act: trigger an invalid site URL configuration change for the charm
        assert: the unit reaches blocked status
        """
        mock_container_exec.return_value = MagicMock(
            wait_output=MagicMock(return_value=("", None))
        )
        self.harness.update_config({"github_webhook_token": ""})
        self.assertEqual(
            self.harness.model.unit.status,
            BlockedStatus("Configuration is not valid"),
        )

    def test_config_changed_when_pebble_not_ready(self):
        """
        arrange: charm created and relations established but pebble is not ready yet
        act: trigger a configuration change for the charm
        assert: the charm is still in waiting status
        """
        self.harness.update_config({"github_webhook_token": "foo"})
        self.assertEqual(self.harness.model.unit.status, WaitingStatus("Waiting for pebble"))

    @patch.object(Container, "exec")
    def test_default_config(self, mock_container_exec):
        """
        arrange: charm created
        act: set container as ready
        assert: the charm is configured with default variables
        """
        mock_container_exec.return_value = MagicMock(
            wait_output=MagicMock(return_value=("", None))
        )
        self.harness.container_pebble_ready("github-actions-exporter")
        updated_plan = self.harness.get_container_pebble_plan("github-actions-exporter").to_dict()
        updated_plan_env = updated_plan["services"]["github-actions-exporter"]["environment"]
        self.assertEqual("default", updated_plan_env["GITHUB_WEBHOOK_TOKEN"])
        self.assertEqual("default", updated_plan_env["GITHUB_API_TOKEN"])
        self.assertEqual("default", updated_plan_env["GITHUB_ORG"])

    @patch.object(Container, "exec")
    def test_valid_webhook_token(self, mock_container_exec):
        """
        arrange: charm created
        act: set container as ready and change the configuration
        assert: webhook token will be equal to the one that was set
        """
        mock_container_exec.return_value = MagicMock(
            wait_output=MagicMock(return_value=("", None))
        )
        self.harness.container_pebble_ready("github-actions-exporter")
        new_webhook_token = token_hex(16)
        self.harness.update_config({"github_webhook_token": new_webhook_token})
        updated_plan = self.harness.get_container_pebble_plan("github-actions-exporter").to_dict()
        updated_plan_env = updated_plan["services"]["github-actions-exporter"]["environment"]
        self.assertEqual(new_webhook_token, updated_plan_env["GITHUB_WEBHOOK_TOKEN"])

    @patch.object(Container, "exec")
    def test_empty_webhook_token(self, mock_container_exec):
        """
        arrange: charm created
        act: set container as ready and change the configuration
        assert: webhook token will be equal to the one that was set
        """
        mock_container_exec.return_value = MagicMock(
            wait_output=MagicMock(return_value=("", None))
        )
        self.harness.container_pebble_ready("github-actions-exporter")
        self.harness.update_config({"github_webhook_token": ""})
        updated_plan = self.harness.get_container_pebble_plan("github-actions-exporter").to_dict()
        updated_plan_env = updated_plan["services"]["github-actions-exporter"]["environment"]
        self.assertEqual("default", updated_plan_env["GITHUB_WEBHOOK_TOKEN"])

    @patch.object(Container, "exec")
    def test_github_actions_exporter_pebble_ready(self, mock_container_exec):
        """
        arrange: charm created
        act: trigger container pebble ready event for github-actions-exporter container
        assert: the container and the service are running
        """
        mock_container_exec.return_value = MagicMock(
            wait_output=MagicMock(return_value=("", None))
        )
        self.harness.container_pebble_ready("github-actions-exporter")
        service = self.harness.model.unit.get_container("github-actions-exporter").get_service(
            "github-actions-exporter"
        )
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

    def test_ingress(self):
        """
        arrange: charm created
        act: create a relation between github-actions-exporter-k8s and nginx ingress integrator,
            and update the external-hostname configuration
        assert: ingress relation data should be set up according to the configuration
            and application name
        """
        harness = self.harness
        nginx_route_relation_id = harness.add_relation("nginx-route", "ingress")
        harness.add_relation_unit(nginx_route_relation_id, "ingress/0")
        charm: GithubActionsExporterOperatorCharm = typing.cast(
            GithubActionsExporterOperatorCharm, self.harness.charm
        )
        harness.set_leader(True)
        # Disabled to keep require nginx route as protected
        charm._require_nginx_route()  # pylint:disable=protected-access

        assert harness.get_relation_data(nginx_route_relation_id, charm.app) == {
            "service-namespace": TEST_MODEL_NAME,
            "service-hostname": charm.app.name,
            "service-name": charm.app.name,
            "service-port": str(GH_EXPORTER_WEBHOOK_PORT),
        }

        new_hostname = token_hex(16)
        harness.update_config({"external_hostname": new_hostname})
        # Disabled to keep require nginx route as protected
        charm._require_nginx_route()  # pylint:disable=protected-access

        assert harness.get_relation_data(nginx_route_relation_id, charm.app) == {
            "service-namespace": TEST_MODEL_NAME,
            "service-hostname": new_hostname,
            "service-name": charm.app.name,
            "service-port": str(GH_EXPORTER_WEBHOOK_PORT),
        }
