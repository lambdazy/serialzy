import logging
import os
import tempfile
from abc import ABC
from typing import BinaryIO, Callable, Dict, Type, Union, Any, Optional

from packaging import version  # type: ignore

from serialzy.api import Schema, VersionBoundary
from serialzy.base import DefaultSchemaSerializerByReference
from serialzy.errors import SerialzyError
from serialzy.utils import cached_installed_packages

_LOG = logging.getLogger(__name__)


# noinspection PyPackageRequirements
class CatboostBaseSerializer(DefaultSchemaSerializerByReference, ABC):
    def available(self) -> bool:
        # noinspection PyBroadException
        try:
            import catboost  # type: ignore

            return True
        except:
            return False

    def stable(self) -> bool:
        return True

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

    def requirements(self) -> Dict[str, VersionBoundary]:
        return {'catboost': VersionBoundary()}


# noinspection PyPackageRequirements
class CatboostPoolSerializer(CatboostBaseSerializer):
    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        with tempfile.NamedTemporaryFile() as handle:
            if not obj.is_quantized():  # type: ignore
                raise SerialzyError('Only quantized pools can be serialized')
            obj.save(handle.name)  # type: ignore
            while True:
                data = handle.read(8096)
                if not data:
                    break
                dest.write(data)

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
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

    def data_format(self) -> str:
        return "catboost_quantized_pool"


# noinspection PyPackageRequirements
class CatboostModelSerializer(CatboostBaseSerializer):
    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        with tempfile.NamedTemporaryFile() as handle:
            obj.save_model(handle.name, format=self.data_format())  # type: ignore
            while True:
                data = handle.read(8096)
                if not data:
                    break
                dest.write(data)

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        with tempfile.NamedTemporaryFile() as handle:
            while True:
                data = source.read(8096)
                if not data:
                    break
                handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())

            model = schema_type()
            model.load_model(handle.name, format=self.data_format())  # type: ignore
            return model

    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        import catboost as cb
        return lambda t: t in [cb.CatBoostClassifier, cb.CatBoostRegressor, cb.CatBoostRanker]  # type: ignore

    def data_format(self) -> str:
        return "cbm"  # CatBoost binary format https://catboost.ai/en/docs/concepts/python-reference_catboost_save_model
