import json
import tempfile
from json import JSONDecodeError
from typing import Any
from unittest import TestCase

from serialzy.serializers.base_model import ModelBaseSerializer

from serialzy.api import Schema, Serializer

from serialzy.registry import DefaultSerializerRegistry
from tests.rich_env.serializers.utils import serialize_and_deserialize, serialize_and_deserialize_with_meta


class ModelBaseSerializerTests(TestCase):
    def initialize(self, module: str):
        self.module = module
        self.registry = DefaultSerializerRegistry()

    def _assert_serializer(self, serializer, expected_serializer):
        self.assertIsInstance(serializer, expected_serializer)
        self.assertTrue(serializer.stable())
        self.assertTrue(serializer.available())
        self.assertIn(self.module, serializer.meta())
        self.assertIn(self.module, serializer.requirements())

    def base_unpack_test(self, model: Any, expected_serializer) -> tempfile.TemporaryDirectory:
        serializer = self.registry.find_serializer_by_type(type(model))

        assert isinstance(serializer, ModelBaseSerializer)
        self._assert_serializer(serializer, expected_serializer)

        with tempfile.TemporaryFile() as file:
            serializer.serialize(model, file)
            file.flush()
            file.seek(0)

            self.assertEqual(serializer.data_format(), Serializer.deserialize_data_format(file))

            temp_dir = tempfile.TemporaryDirectory()
            serializer.unpack_model(file, temp_dir.name)
            return temp_dir

    def base_test(self, model: Any, expected_serializer):
        serializer = self.registry.find_serializer_by_type(type(model))

        assert isinstance(serializer, ModelBaseSerializer)
        self._assert_serializer(serializer, expected_serializer)

        return serialize_and_deserialize(serializer, model)

    def base_test_with_meta(self, model: Any, expected_serializer):
        serializer = self.registry.find_serializer_by_type(type(model))

        assert isinstance(serializer, ModelBaseSerializer)
        self._assert_serializer(serializer, expected_serializer)

        return serialize_and_deserialize_with_meta(serializer, model)

    def base_invalid_types(self, model, class_type):
        serializer = self.registry.find_serializer_by_type(class_type)
        assert serializer

        with self.assertRaisesRegex(TypeError, 'Invalid object type*'):
            with tempfile.TemporaryFile() as file:
                serializer.serialize(1, file)

        with tempfile.TemporaryFile() as file:
            serializer.serialize(model, file)
            file.flush()
            file.seek(0)

            with self.assertRaisesRegex(TypeError, 'Cannot deserialize data with schema type*'):
                serializer.deserialize(file, int)

    def base_schema(self, data_format: str, class_type):
        serializer = self.registry.find_serializer_by_data_format(data_format)
        assert serializer

        schema = serializer.schema(class_type)

        self.assertEqual(data_format, schema.data_format)
        self.assertEqual('serialzy_python_type_reference', schema.schema_format)
        self.assertTrue(len(schema.schema_content) > 0)
        self.assertTrue(self.module in schema.meta)

    def base_resolve(self, data_format: str, class_type):
        serializer = self.registry.find_serializer_by_data_format(data_format)
        assert serializer

        typ = serializer.resolve(
            Schema(data_format, 'serialzy_python_type_reference', json.dumps({
                "module": class_type.__module__,
                "name": class_type.__name__
            }), {self.module: '0.0.0'}))
        self.assertEqual(class_type, typ)

        with self.assertRaisesRegex(TypeError, 'Invalid data format*'):
            serializer.resolve(
                Schema('invalid format', 'serialzy_python_type_reference', 'content', {self.module: '1.0.0'}))

        with self.assertRaisesRegex(ValueError, 'Invalid schema format*'):
            serializer.resolve(
                Schema(data_format, 'invalid format', json.dumps({
                    "module": class_type.__module__,
                    "name": class_type.__name__
                }), {self.module: '0.0.0'}))

        with self.assertRaisesRegex(JSONDecodeError, 'Expecting value*'):
            serializer.resolve(
                Schema(data_format, 'serialzy_python_type_reference', 'invalid json',
                       {self.module: '1.0.0'}))

        with self.assertRaisesRegex(ValueError, 'Invalid schema content*'):
            serializer.resolve(
                Schema(data_format, 'serialzy_python_type_reference', json.dumps({
                    "module": class_type.__module__
                }), {self.module: '0.0.0'}))

        with self.assertRaisesRegex(ValueError, 'Invalid schema content*'):
            serializer.resolve(
                Schema(data_format, 'serialzy_python_type_reference', json.dumps({
                    "name": class_type.__name__
                }), {self.module: '0.0.0'}))

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema(data_format, 'serialzy_python_type_reference', json.dumps({
                    "module": class_type.__module__,
                    "name": class_type.__name__
                }), {}))
            self.assertRegex(cm.output[0], f'No {self.module} version in meta')

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema(data_format, 'serialzy_python_type_reference', json.dumps({
                    "module": class_type.__module__,
                    "name": class_type.__name__
                }), {self.module: '1000.0.0'}))
            self.assertRegex(cm.output[0], f'Installed version of {self.module}*')
