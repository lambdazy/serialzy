import base64
import importlib
import json
import logging
from abc import ABC
from typing import Type, cast
from packaging import version  # type: ignore
from serialzy.utils import cached_installed_packages

from serialzy.api import Serializer, Schema, StandardSchemaFormats

_LOG = logging.getLogger(__name__)


# noinspection PyPackageRequirements
class DefaultSchemaSerializerByValue(Serializer, ABC):
    def available(self) -> bool:
        # noinspection PyBroadException
        try:
            import cloudpickle  # type: ignore
            return True
        except:
            return False

    def schema(self, typ: Type) -> Schema:
        import cloudpickle  # type: ignore
        return Schema(
            self.data_format(),
            StandardSchemaFormats.pickled_type.name,
            base64.b64encode(cloudpickle.dumps(typ)).decode("ascii"),
            {**self.meta(), **{"cloudpickle": cloudpickle.__version__}},
        )

    def resolve(self, schema: Schema) -> Type:
        import cloudpickle  # type: ignore
        self._validate_schema(schema)
        if schema.schema_format != StandardSchemaFormats.pickled_type.name:
            raise ValueError(f'Invalid schema format: {schema.schema_format}')
        if 'cloudpickle' not in schema.meta:
            _LOG.warning('No cloudpickle version in meta')
        elif version.parse(schema.meta['cloudpickle']) > version.parse(cached_installed_packages["cloudpickle"]):
            _LOG.warning(f'Installed version of cloudpickle {cached_installed_packages["cloudpickle"]} '
                         f'is older than used for serialization {schema.meta["cloudpickle"]}')
        return cast(
            Type,
            cloudpickle.loads(
                base64.b64decode(cast(str, schema.schema_content).encode("ascii"))
            ),
        )


class DefaultSchemaSerializerByReference(Serializer, ABC):
    SCHEMA_FORMAT = "serialzy_python_type_reference"

    def schema(self, typ: Type) -> Schema:
        return Schema(
            self.data_format(),
            self.SCHEMA_FORMAT,
            json.dumps({
                "module": typ.__module__,
                "name": typ.__name__
            }),
            self.meta(),
        )

    def resolve(self, schema: Schema) -> Type:
        self._validate_schema(schema)
        if schema.schema_format != self.SCHEMA_FORMAT:
            raise ValueError(f'Invalid schema format: {schema.schema_content}')
        info = json.loads(schema.schema_content)
        if 'module' not in info or 'name' not in info:
            raise ValueError(f'Invalid schema content: {schema.schema_content}')

        module = info['module']
        name = info['name']
        # NoneType cannot be imported from builtin
        if module == 'builtins' and name == 'NoneType':
            return type(None)

        typ = getattr(importlib.import_module(module), name)
        return cast(type, typ)
