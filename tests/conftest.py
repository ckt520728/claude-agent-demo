import pytest
from dotenv import load_dotenv

load_dotenv()  # picks up ANTHROPIC_API_KEY from .env if present


def pytest_addoption(parser):
    parser.addoption(
        "--run-live",
        action="store_true",
        help="run tests that call Claude for real (costs money)",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "live: calls Claude for real; needs --run-live")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-live"):
        return
    skip = pytest.mark.skip(reason="live test: pass --run-live to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)
