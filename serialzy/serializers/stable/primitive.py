import json
import logging
from typing import Any, BinaryIO, Callable, Dict, Type, Union, cast, Optional

from packaging import version  # type: ignore

from serialzy.api import (
    Schema,
    Serializer,
    StandardDataFormats,
    StandardSchemaFormats,
)
from serialzy.utils import cached_installed_packages

_LOG = logging.getLogger(__name__)


# noinspection PyPackageRequirements
class PrimitiveSerializer(Serializer):
    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        import jsonpickle  # type: ignore
        dumps = jsonpickle.dumps(obj).encode("utf-8")
        dest.write(dumps)

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        import jsonpickle  # type: ignore
        read = source.read().decode("utf-8")
        return jsonpickle.loads(read)

    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        return lambda t: t in [int, float, str, bool, type(None)]

    def available(self) -> bool:
        # noinspection PyBroadException
        try:
            import jsonpickle  # type: ignore
            return True
        except:
            return False

    def stable(self) -> bool:
        return True

    def data_format(self) -> str:
        return StandardDataFormats.primitive_type.name

    def meta(self) -> Dict[str, str]:
        import jsonpickle  # type: ignore
        return {"jsonpickle": jsonpickle.__version__}

    def schema(self, typ: type) -> Schema:
        import jsonpickle  # type: ignore
        return Schema(
            self.data_format(),
            StandardSchemaFormats.json_pickled_type.name,
            jsonpickle.dumps(typ),
            self.meta(),
        )

    def resolve(self, schema: Schema) -> Type:
        import jsonpickle  # type: ignore
        self._validate_schema(schema)
        if schema.schema_format != StandardSchemaFormats.json_pickled_type.name:
            raise ValueError(f'Invalid schema format {schema.schema_format}')
        if 'jsonpickle' not in schema.meta:
            _LOG.warning('No jsonpickle version in meta')
        elif version.parse(schema.meta['jsonpickle']) > version.parse(cached_installed_packages["jsonpickle"]):
            _LOG.warning(f'Installed version of jsonpickle {cached_installed_packages["jsonpickle"]} '
                         f'is older than used for serialization {schema.meta["jsonpickle"]}')

        from jsonpickle import tags
        json_loaded = json.loads(schema.schema_content)
        if json_loaded[tags.TYPE] == 'builtins.NoneType':  # jsonpickle cannot resolve NoneType
            return type(None)

        return cast(Type, jsonpickle.loads(schema.schema_content))
