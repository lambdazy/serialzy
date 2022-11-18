import logging
import os
import tempfile
from typing import BinaryIO, Callable, Dict, Type, TypeVar, Union

from serialzy.api import Schema
from serialzy.base import DefaultSchemaSerializerByReference
from serialzy.utils import cached_installed_packages

from packaging import version  # type: ignore

T = TypeVar("T")  # pylint: disable=invalid-name

_LOG = logging.getLogger(__name__)


# noinspection PyPackageRequirements
class CatboostPoolSerializer(DefaultSchemaSerializerByReference):
    def available(self) -> bool:
        # noinspection PyBroadException
        try:
            import catboost  # type: ignore

            return True
        except:
            return False

    def serialize(self, obj: T, dest: BinaryIO) -> None:
        with tempfile.NamedTemporaryFile() as handle:
            if not obj.is_quantized():  # type: ignore
                obj.quantize()  # type: ignore
            obj.save(handle.name)  # type: ignore
            while True:
                data = handle.read(8096)
                if not data:
                    break
                dest.write(data)

    def deserialize(self, source: BinaryIO, typ: Type[T]) -> T:
        with tempfile.NamedTemporaryFile() as handle:
            while True:
                data = source.read(8096)
                if not data:
                    break
                handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
            import catboost

            return catboost.Pool("quantized://" + handle.name)  # type: ignore

    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        import catboost

        return catboost.Pool  # type: ignore

    def stable(self) -> bool:
        return True

    def data_format(self) -> str:
        import catboost

        return str(catboost.Pool.__module__) + "." + str(catboost.Pool.__name__)

    def meta(self) -> Dict[str, str]:
        import catboost

        return {"catboost": catboost.__version__}

    def resolve(self, schema: Schema) -> Type:
        typ = super().resolve(schema)
        if 'catboost' not in schema.meta:
            _LOG.warning('No catboost version in meta')
        elif version.parse(schema.meta['catboost']) > version.parse(cached_installed_packages["catboost"]):
            _LOG.warning(f'Installed version of catboost {cached_installed_packages["catboost"]} '
                         f'is older than used for serialization {schema.meta["catboost"]}')
        return typ
