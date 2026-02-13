"""Pytest configuration for tiptop_ipy tests."""
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--network",
        action="store_true",
        default=False,
        help="Run tests that require network access",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "network: mark test as requiring network access")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--network"):
        skip_network = pytest.mark.skip(reason="need --network option to run")
        for item in items:
            if "network" in item.keywords:
                item.add_marker(skip_network)
