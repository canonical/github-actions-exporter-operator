# Copyright 2023 Amanda
# See LICENSE file for licensing details.
#

"""GitHub Actions Exporter charm unit tests."""

import unittest

import ops.testing
from ops.testing import Harness

from charm import GithubActionsExporterOperatorCharm


class TestCharm(unittest.TestCase):
    """GitHub Actions Exporter charm unit tests."""

    def setUp(self):
        """Set up test environment."""
        ops.testing.SIMULATE_CAN_CONNECT = True
        self.addCleanup(setattr, ops.testing, "SIMULATE_CAN_CONNECT", False)

        self.harness = Harness(GithubActionsExporterOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()
