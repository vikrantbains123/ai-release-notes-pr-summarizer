"""Loads required credentials from the environment / a local .env file.

Per the project constitution (Secrets Never Committed), this is the only
module that reads GITHUB_TOKEN / ANTHROPIC_API_KEY.
"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


class CredentialError(Exception):
    """Raised when a required credential is missing or rejected by its API."""


def missing_credential_error(variable: str) -> CredentialError:
    return CredentialError(f"{variable} is not set")


def rejected_credential_error(variable: str, service: str) -> CredentialError:
    return CredentialError(f"{variable} was rejected by {service}")


@dataclass
class Config:
    github_token: str
    anthropic_api_key: str


def load_config() -> Config:
    load_dotenv()

    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise missing_credential_error("GITHUB_TOKEN")

    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise missing_credential_error("ANTHROPIC_API_KEY")

    return Config(github_token=github_token, anthropic_api_key=anthropic_api_key)
