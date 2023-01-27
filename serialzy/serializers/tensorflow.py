import inspect
import logging
import os
import shutil
import tempfile
from abc import ABC
from typing import Union, Type, Callable, Dict, Any, BinaryIO, Optional

from packaging import version

from serialzy.api import Schema, VersionBoundary
from serialzy.base import DefaultSchemaSerializerByReference
from serialzy.utils import cached_installed_packages

_LOG = logging.getLogger(__name__)


def serialize_dir(dir: str, dest: BinaryIO):
    tar_save_path = os.path.join(dir, "model")
    saved_archive = shutil.make_archive(tar_save_path, "tar", dir)
    with open(saved_archive, "rb") as handle:
        while True:
            data = handle.read(8096)
            if not data:
                break
            dest.write(data)
    shutil.rmtree(dir)


def deserialize_dir(source: BinaryIO) -> str:
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

        return tmpdir


class TensorflowBaseSerializer(DefaultSchemaSerializerByReference, ABC):
    def available(self) -> bool:
        # noinspection PyBroadException
        try:
            import tensorflow  # type: ignore
            return True
        except:
            return False

    def stable(self) -> bool:
        return True

    def meta(self) -> Dict[str, str]:
        import tensorflow

        return {"tensorflow": tensorflow.__version__}

    def resolve(self, schema: Schema) -> Type:
        typ = super().resolve(schema)
        if 'tensorflow' not in schema.meta:
            _LOG.warning('No tensorflow version in meta')
        elif version.parse(schema.meta['tensorflow']) > version.parse(cached_installed_packages["tensorflow"]):
            _LOG.warning(f'Installed version of tensorflow {cached_installed_packages["tensorflow"]} '
                         f'is older than used for serialization {schema.meta["tensorflow"]}')
        return typ

    def requirements(self) -> Dict[str, VersionBoundary]:
        return {'tensorflow': VersionBoundary()}


class TensorflowKerasSerializer(TensorflowBaseSerializer):
    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        import tensorflow as tf
        return lambda t: t in [tf.keras.Sequential] or (inspect.isclass(t) and issubclass(t, tf.keras.Model))

    def data_format(self) -> str:
        return "tf_keras"

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        tmpdir = tempfile.mkdtemp()
        obj.save(tmpdir, save_format=self.data_format())  # type: ignore
        serialize_dir(tmpdir, dest)

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        tmpdir = deserialize_dir(source)
        import tensorflow as tf
        model = tf.keras.models.load_model(tmpdir)  # type: ignore
        shutil.rmtree(tmpdir)
        return model


class TensorflowPureSerializer(TensorflowBaseSerializer):
    def supported_types(self) -> Union[Type, Callable[[Type], bool]]:
        import tensorflow as tf
        return lambda t: t in [tf.train.Checkpoint] or (inspect.isclass(t) and issubclass(t, tf.Module))

    def data_format(self) -> str:
        return "tf_pure"

    def _serialize(self, obj: Any, dest: BinaryIO) -> None:
        tmpdir = tempfile.mkdtemp()
        import tensorflow as tf
        tf.saved_model.save(obj, tmpdir)
        serialize_dir(tmpdir, dest)

    def _deserialize(self, source: BinaryIO, schema_type: Type, user_type: Optional[Type] = None) -> Any:
        self._check_types_valid(schema_type, user_type)
        tmpdir = deserialize_dir(source)
        import tensorflow as tf
        model = tf.saved_model.load(tmpdir)
        shutil.rmtree(tmpdir)
        return model
