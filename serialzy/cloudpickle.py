import logging
from typing import Any, BinaryIO, Callable, Dict, Type, Union, Optional

from serialzy.api import StandardDataFormats, Schema, VersionBoundary
from serialzy.base import DefaultSchemaSerializerByValue
from packaging import version  # type: ignore

from serialzy.utils import cached_installed_packages

_LOG = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic, PyPackageRequirements
class CloudpickleSerializer(DefaultSchemaSerializerByValue):
    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        import cloudpickle  # type: ignore
        cloudpickle.dump(obj, dest)

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        import cloudpickle  # type: ignore
        return cloudpickle.load(source)

    def available(self) -> bool:
        base_available = super().available()
        if not base_available:
            return False
        # noinspection PyBroadException
        try:
            import cloudpickle  # type: ignore
            return True
        except:
            return False

    def stable(self) -> bool:
        return False

    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        return lambda x: True

    def data_format(self) -> str:
        return StandardDataFormats.pickle.name

    def meta(self) -> Dict[str, str]:
        import cloudpickle  # type: ignore
        return {"cloudpickle": cloudpickle.__version__}

    def resolve(self, schema: Schema) -> Type:
        typ = super().resolve(schema)
        if 'cloudpickle' not in schema.meta:
            _LOG.warning('No cloudpickle version in meta')
        elif version.parse(schema.meta['cloudpickle']) > version.parse(cached_installed_packages["cloudpickle"]):
            _LOG.warning(f'Installed version of cloudpickle {cached_installed_packages["cloudpickle"]} '
                         f'is older than used for serialization {schema.meta["cloudpickle"]}')
        return typ

    def requirements(self) -> Dict[str, VersionBoundary]:
        return {"cloudpickle": VersionBoundary()}
