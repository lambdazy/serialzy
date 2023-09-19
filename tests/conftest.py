from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


def get_serialzy_location():
    return Path(__file__).parent.parent


@pytest.fixture(scope='session')
def serialzy_location():
    return get_serialzy_location()


@pytest.fixture(autouse=True, scope='session')
def add_tests_to_sys_modules(serialzy_location):
    old_sys_path = sys.path.copy()
    sys.path.append(str(serialzy_location))
    importlib.import_module('tests')
    sys.path = old_sys_path


def pytest_addoption(parser):
    parser.addoption("--empty-venv-tests", action='store_true', default=False)


def pytest_collection_modifyitems(config, items):
    empty_venv_tests = config.option.empty_venv_tests
    serialzy_path = get_serialzy_location()

    for item in items[:]:
        path = Path(item.fspath).relative_to(serialzy_path)

        if sys.version_info >= (3, 9):
            empty_tests = path.is_relative_to('tests/empty_env')
        else:
            empty_tests = str(path).startswith('tests/empty_env/')

        if empty_tests != empty_venv_tests:
            items.remove(item)
            continue
