import tempfile
from json import JSONDecodeError
from typing import Type
from unittest import TestCase

from serialzy.api import Schema, StandardDataFormats, StandardSchemaFormats
from serialzy.registry import DefaultSerializerRegistry
from tests.serializers.utils import serialized_and_deserialized


class PrimitiveSerializationTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_serialization(self):
        var = 10
        self.assertEqual(var, serialized_and_deserialized(self.registry, var))

        var = 0.0001
        self.assertEqual(var, serialized_and_deserialized(self.registry, var))

        var = "str"
        self.assertEqual(var, serialized_and_deserialized(self.registry, var))

        var = True
        self.assertEqual(var, serialized_and_deserialized(self.registry, var))

    def test_schema(self):
        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.primitive_type.name)
        self.assertTrue(serializer.stable())
        self.assertTrue(serializer.available())

        schema = serializer.schema(int)
        self.assertEqual(StandardDataFormats.primitive_type.name, schema.data_format)
        self.assertEqual(StandardSchemaFormats.json_pickled_type.name, schema.schema_format)
        self.assertEqual('{"py/type": "builtins.int"}', schema.schema_content)
        self.assertTrue('jsonpickle' in schema.meta)

    def test_resolve(self):
        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.primitive_type.name)
        typ = serializer.resolve(Schema(
            StandardDataFormats.primitive_type.name, StandardSchemaFormats.json_pickled_type.name,
            '{"py/type": "builtins.str"}', {'jsonpickle': '0.0.0'}
        ))
        self.assertEqual(str, typ)

        with self.assertRaisesRegex(ValueError, "Invalid data format*"):
            serializer.resolve(
                Schema(
                    StandardDataFormats.proto.name,
                    StandardSchemaFormats.json_pickled_type.name,
                    "content",
                    {'jsonpickle': '0.0.0'}
                )
            )
        with self.assertRaisesRegex(ValueError, "Invalid schema format*"):
            serializer.resolve(
                Schema(
                    StandardDataFormats.primitive_type.name,
                    StandardSchemaFormats.pickled_type.name,
                    "content",
                    {'jsonpickle': '0.0.0'}
                )
            )

        with self.assertRaises(JSONDecodeError):
            serializer.resolve(
                Schema(
                    StandardDataFormats.primitive_type.name,
                    StandardSchemaFormats.json_pickled_type.name,
                    "invalid content",
                    {'jsonpickle': '0.0.0'}
                )
            )

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema(
                    StandardDataFormats.primitive_type.name,
                    StandardSchemaFormats.json_pickled_type.name,
                    '{"py/type": "builtins.str"}',
                    {'jsonpickle': '10000.0.0'}
                )
            )
            self.assertRegex(cm.output[0], 'WARNING:serialzy.serializers.primitive:Installed version of jsonpickle*')

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema(
                    StandardDataFormats.primitive_type.name,
                    StandardSchemaFormats.json_pickled_type.name,
                    '{"py/type": "builtins.str"}',
                    {}
                )
            )
            self.assertRegex(cm.output[0], 'WARNING:serialzy.serializers.primitive:No jsonpickle version in meta*')
