# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""GitHub Actions Exporter charm unit tests."""
# pylint: disable=protected-access

import unittest
from secrets import token_hex
from unittest.mock import MagicMock, patch

import ops
from ops.testing import Harness

from charm import GithubActionsExporterCharm

TEST_MODEL_NAME = "test-github-actions-exporter"


class TestCharm(unittest.TestCase):
    """GitHub Actions Exporter charm unit tests."""

    def setUp(self):
        """Set up test environment."""
        self.harness = Harness(GithubActionsExporterCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.set_model_name(TEST_MODEL_NAME)
        self.harness.begin()

    @patch.object(ops.Container, "exec")
    def test_config_changed(self, mock_container_exec):
        """
        arrange: charm created
        act: trigger a valid configuration change for the charm
        assert: the container and the service are running and properly configured
        """
        mock_container_exec.return_value = MagicMock(
            wait_output=MagicMock(return_value=("", None))
        )
        self.harness.disable_hooks()
        self.harness._framework = ops.framework.Framework(
            self.harness._storage, self.harness._charm_dir, self.harness._meta, self.harness._model
        )
        self.harness._charm = None
        self.harness.update_config({"github_webhook_token": "foo"})
        self.harness.enable_hooks()
        self.harness.begin_with_initial_hooks()
        self.harness.container_pebble_ready("github-actions-exporter")
        updated_plan = self.harness.get_container_pebble_plan("github-actions-exporter").to_dict()
        updated_plan_env = updated_plan["services"]["github-actions-exporter"]["environment"]
        self.assertEqual("foo", updated_plan_env["GITHUB_WEBHOOK_TOKEN"])
        self.assertEqual(self.harness.model.unit.status, ops.ActiveStatus())
        mock_container_exec.assert_any_call(
            ["/srv/gh_exporter/github-actions-exporter", "--version"],
            user="gh_exporter",
        )

    @patch.object(ops.Container, "exec")
    def test_config_changed_when_config_invalid(self, mock_container_exec):
        """
        arrange: charm created and relations established
        act: trigger an invalid site URL configuration change for the charm
        assert: the unit reaches blocked status
        """
        mock_container_exec.return_value = MagicMock(
            wait_output=MagicMock(return_value=("", None))
        )
        self.harness.disable_hooks()
        self.harness._framework = ops.framework.Framework(
            self.harness._storage, self.harness._charm_dir, self.harness._meta, self.harness._model
        )
        self.harness._charm = None
        self.harness.update_config({"github_webhook_token": ""})
        self.harness.enable_hooks()
        self.harness.begin_with_initial_hooks()
        self.assertEqual(
            self.harness.model.unit.status,
            ops.BlockedStatus("invalid configuration: github_webhook_token"),
        )

    def test_config_changed_when_pebble_not_ready(self):
        """
        arrange: charm created and relations established but pebble is not ready yet
        act: trigger a configuration change for the charm
        assert: the charm is still in waiting status
        """
        self.harness.update_config({"github_webhook_token": "foo"})
        self.assertEqual(self.harness.model.unit.status, ops.WaitingStatus("Waiting for pebble"))

    @patch.object(ops.Container, "exec")
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

    @patch.object(ops.Container, "exec")
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
        self.harness.disable_hooks()
        self.harness._framework = ops.framework.Framework(
            self.harness._storage, self.harness._charm_dir, self.harness._meta, self.harness._model
        )
        self.harness._charm = None
        new_webhook_token = token_hex(16)
        self.harness.update_config({"github_webhook_token": new_webhook_token})
        self.harness.enable_hooks()
        self.harness.begin_with_initial_hooks()
        updated_plan = self.harness.get_container_pebble_plan("github-actions-exporter").to_dict()
        updated_plan_env = updated_plan["services"]["github-actions-exporter"]["environment"]
        self.assertEqual(new_webhook_token, updated_plan_env["GITHUB_WEBHOOK_TOKEN"])

    @patch.object(ops.Container, "exec")
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

    @patch.object(ops.Container, "exec")
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
        self.assertEqual(self.harness.model.unit.status, ops.ActiveStatus())
