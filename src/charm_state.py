#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""State of the Charm."""
import itertools
import typing

# pydantic is causing this no-name-in-module problem
from pydantic import (  # pylint: disable=no-name-in-module,import-error
    BaseModel,
    Extra,
    Field,
    ValidationError,
)

from exceptions import CharmConfigInvalidError

if typing.TYPE_CHECKING:
    from charm import GithubActionsExporterCharm


KNOWN_CHARM_CONFIG = (
    "github_api_token",
    "github_org",
    "github_webhook_token",
)


class GithubActionsExporterConfig(BaseModel):  # pylint: disable=too-few-public-methods
    """Represent GithubActionsExporter builtin configuration values.

    Attrs:
        github_api_token: github_api_token config.
        github_org: github_org config.
        github_webhook_token: github_webhook_token config.
    """

    github_api_token: str = Field(None)
    github_org: str = Field(None)
    github_webhook_token: str = Field(..., min_length=1)

    class Config:  # pylint: disable=too-few-public-methods
        """Config class.

        Attrs:
            extra: extra configuration.
        """

        extra = Extra.allow


class CharmState:
    """State of the Charm.

    Attrs:
        github_api_token: github_api_token config.
        github_org: github_org config.
        github_webhook_token: github_webhook_token config.
    """

    def __init__(
        self,
        *,
        github_config: GithubActionsExporterConfig,
    ) -> None:
        """Construct.

        Args:
            github_config: The value of the github_config charm configuration.
        """
        self._github_config = github_config

    @property
    def github_api_token(self) -> str:
        """Return github_api_token config.

        Returns:
            str: github_api_token config.
        """
        return self._github_config.github_api_token

    @property
    def github_org(self) -> str:
        """Return github_org config.

        Returns:
            str: github_org config.
        """
        return self._github_config.github_org

    @property
    def github_webhook_token(self) -> str:
        """Return github_webhook_token config.

        Returns:
            str: github_webhook_token config.
        """
        return self._github_config.github_webhook_token

    @classmethod
    def from_charm(cls, charm: "GithubActionsExporterCharm") -> "CharmState":
        """Initialize a new instance of the CharmState class from the associated charm.

        Args:
            charm: The charm instance associated with this state.

        Return:
            The CharmState instance created by the provided charm.

        Raises:
            CharmConfigInvalidError: if the charm configuration is invalid.
        """
        github_config = {k: v for k, v in charm.config.items() if k in KNOWN_CHARM_CONFIG}
        try:
            valid_github_config = GithubActionsExporterConfig(**github_config)  # type: ignore
        except ValidationError as exc:
            error_fields = set(
                itertools.chain.from_iterable(error["loc"] for error in exc.errors())
            )
            error_field_str = " ".join(f"{f}" for f in error_fields)
            raise CharmConfigInvalidError(f"invalid configuration: {error_field_str}") from exc
        return cls(github_config=valid_github_config)
