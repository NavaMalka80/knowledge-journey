"""Smoke tests: the package installs, imports, and exposes a valid version."""

import re

import knowledge_journey

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def test_package_exposes_version() -> None:
    assert SEMVER.match(knowledge_journey.__version__)
