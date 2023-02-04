import importlib
import logging
import os
import shutil
import tempfile
from abc import ABC
from typing import Dict, Type, BinaryIO, Any, Union, Callable

from packaging import version  # type: ignore

from serialzy.api import Schema, VersionBoundary
from serialzy.base import DefaultSchemaSerializerByReference
from serialzy.utils import cached_installed_packages, module_name


# noinspection PyPackageRequirements
def serialize_to_file(dest: BinaryIO, save_to_file) -> None:
    with tempfile.NamedTemporaryFile() as handle:
        save_to_file(handle.name)
        while True:
            data = handle.read(8096)
            if not data:
                break
            dest.write(data)


def deserialize_from_file(source: BinaryIO, read_from_file) -> Any:
    with tempfile.NamedTemporaryFile() as handle:
        while True:
            data = source.read(8096)
            if not data:
                break
            handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
        return read_from_file(handle.name)


def serialize_to_dir(dest: BinaryIO, save_to_dir):
    tmpdir = tempfile.mkdtemp()
    save_to_dir(tmpdir)
    tar_save_path = os.path.join(tmpdir, "model")
    saved_archive = shutil.make_archive(tar_save_path, "tar", tmpdir)
    with open(saved_archive, "rb") as handle:
        while True:
            data = handle.read(8096)
            if not data:
                break
            dest.write(data)
    shutil.rmtree(tmpdir)


def deserialize_from_dir(source: BinaryIO, read_from_dir) -> Any:
    with tempfile.NamedTemporaryFile(suffix=".tar") as handle:
        while True:
            data = source.read(8096)
            if not data:
                break
            handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())

        tmpdir = tempfile.mkdtemp()
        shutil.unpack_archive(handle.name, tmpdir, "tar")
        model = read_from_dir(tmpdir)
        shutil.rmtree(tmpdir)
        return model


class ModelBaseSerializer(DefaultSchemaSerializerByReference, ABC):
    def __init__(self, module: str, serializer_name: str):
        self.module = module
        self.logger = logging.getLogger(serializer_name)

    def available(self) -> bool:
        # noinspection PyBroadException
        try:
            importlib.import_module(self.module)

            return True
        except:
            return False

    def stable(self) -> bool:
        return True

    def meta(self) -> Dict[str, str]:
        m = importlib.import_module(self.module)

        return {self.module: m.__version__}

    def resolve(self, schema: Schema) -> Type:
        typ = super().resolve(schema)
        if self.module not in schema.meta:
            self.logger.warning(f'No {self.module} version in meta')
        elif version.parse(schema.meta[self.module]) > version.parse(cached_installed_packages[self.module]):
            self.logger.warning(f'Installed version of {self.module} {cached_installed_packages[self.module]} '
                                f'is older than used for serialization {schema.meta[self.module]}')
        return typ

    def requirements(self) -> Dict[str, VersionBoundary]:
        return {self.module: VersionBoundary()}

    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        return lambda t: self.__check_module_fits_serializer(t) and self._types_filter(t)

    def _types_filter(self, typ: Type) -> bool:
        return False

    def __check_module_fits_serializer(self, typ: Type) -> bool:
        name = module_name(typ)
        if name == self.module:
            return True

        if hasattr(typ, '__bases__'):
            for base in typ.__bases__:
                base_name = module_name(base)
                if base_name == self.module:
                    return True
        return False
