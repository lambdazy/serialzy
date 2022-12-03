from json import JSONDecodeError
from unittest import TestCase

from serialzy.api import Schema, StandardDataFormats, StandardSchemaFormats
from serialzy.registry import DefaultSerializerRegistry
from tests.rich_env.serializers.utils import serialize_and_deserialize


class PrimitiveSerializationTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_serialization(self):
        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.primitive_type.name)

        var = 10
        self.assertEqual(var, serialize_and_deserialize(serializer, var))

        var = 0.0001
        self.assertEqual(var, serialize_and_deserialize(serializer, var))

        var = "str"
        self.assertEqual(var, serialize_and_deserialize(serializer, var))

        var = True
        self.assertEqual(var, serialize_and_deserialize(serializer, var))

        var = None
        self.assertEqual(var, serialize_and_deserialize(serializer, var))

    def test_schema(self):
        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.primitive_type.name)
        self.assertTrue(serializer.stable())
        self.assertTrue(serializer.available())

        schema = serializer.schema(int)
        self.assertEqual(StandardDataFormats.primitive_type.name, schema.data_format)
        self.assertEqual(StandardSchemaFormats.json_pickled_type.name, schema.schema_format)
        self.assertEqual('{"py/type": "builtins.int"}', schema.schema_content)
        self.assertTrue('jsonpickle' in schema.meta)

        schema = serializer.schema(type(None))
        self.assertEqual('{"py/type": "builtins.NoneType"}', schema.schema_content)

    def test_resolve(self):
        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.primitive_type.name)
        typ = serializer.resolve(Schema(
            StandardDataFormats.primitive_type.name, StandardSchemaFormats.json_pickled_type.name,
            '{"py/type": "builtins.str"}', {'jsonpickle': '0.0.0'}
        ))
        self.assertEqual(str, typ)

        typ = serializer.resolve(Schema(
            StandardDataFormats.primitive_type.name, StandardSchemaFormats.json_pickled_type.name,
            '{"py/type": "builtins.NoneType"}', {'jsonpickle': '0.0.0'}
        ))
        self.assertEqual(type(None), typ)

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
            self.assertRegex(cm.output[0], 'WARNING:serialzy.serializers.stable.primitive:Installed version of jsonpickle*')

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema(
                    StandardDataFormats.primitive_type.name,
                    StandardSchemaFormats.json_pickled_type.name,
                    '{"py/type": "builtins.str"}',
                    {}
                )
            )
            self.assertRegex(cm.output[0], 'WARNING:serialzy.serializers.stable.primitive:No jsonpickle version in meta*')
