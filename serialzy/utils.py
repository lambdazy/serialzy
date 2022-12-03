import importlib
import pkgutil
from types import ModuleType
from typing import Dict

import pkg_resources


def all_installed_packages() -> Dict[str, str]:
    return {
        entry.project_name: entry.version
        # working_set is actually iterable see sources
        for entry in pkg_resources.working_set  # pylint: disable=not-an-iterable
    }


cached_installed_packages = all_installed_packages()


def load_all_modules_from(module: ModuleType) -> None:
    for loader, name, is_pkg in pkgutil.walk_packages(module.__path__):
        importlib.import_module(module.__name__ + '.' + name)
