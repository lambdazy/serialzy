import logging
import sys
from inspect import isclass
from typing import Any, BinaryIO, Callable, Dict, Type, Union, Optional

from packaging import version  # type: ignore
from serialzy.api import Schema, VersionBoundary
from serialzy.base import DefaultSchemaSerializerByValue
from serialzy.utils import cached_installed_packages

_LOG = logging.getLogger(__name__)


class ExceptionSerializer(DefaultSchemaSerializerByValue):
    DATA_FORMAT = "raw_exception"

    def _serialize(self, obj: BaseException, dest: BinaryIO) -> None:
        from tblib import pickling_support  # type: ignore
        pickling_support.install()
        import pickle  # type: ignore
        pickle.dump(sys.exc_info(), dest)

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        import pickle  # type: ignore
        return pickle.load(source)

    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        def supported(x):
            return isclass(x) and issubclass(x, BaseException)
        return supported

    def available(self) -> bool:
        base_available = super().available()
        if not base_available:
            return False
        # noinspection PyBroadException
        try:
            import tblib  # type: ignore
            return True
        except Exception:
            return False

    def stable(self) -> bool:
        return False

    def data_format(self) -> str:
        return self.DATA_FORMAT

    def meta(self) -> Dict[str, str]:
        import tblib  # type: ignore
        return {"tblib": tblib.__version__}

    def resolve(self, schema: Schema) -> Type:
        if 'tblib' not in schema.meta:
            _LOG.warning('No tblib version in meta')
        elif version.parse(schema.meta['tblib']) > version.parse(cached_installed_packages["tblib"]):
            _LOG.warning(f'Installed version of tblib {cached_installed_packages["tblib"]} '
                         f'is older than used for serialization {schema.meta["tblib"]}')
        return BaseException

    def requirements(self) -> Dict[str, VersionBoundary]:
        return {'tblib': VersionBoundary()}
