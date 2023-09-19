import tempfile
from json import JSONDecodeError
from typing import List
from unittest import TestCase

from serialzy.api import Schema, StandardDataFormats, StandardSchemaFormats
from serialzy.registry import DefaultSerializerRegistry
from tests.rich_env.serializers.utils import serialize_and_deserialize


class PrimitiveSerializationTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_serialization(self):
        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.primitive_type.name)
        assert serializer

        var1 = 10
        self.assertEqual(var1, serialize_and_deserialize(serializer, var1))

        var2 = 0.0001
        self.assertEqual(var2, serialize_and_deserialize(serializer, var2))

        var3 = "str"
        self.assertEqual(var3, serialize_and_deserialize(serializer, var3))

        var4 = True
        self.assertEqual(var4, serialize_and_deserialize(serializer, var4))

        var5 = False
        self.assertEqual(var5, serialize_and_deserialize(serializer, var5))

        var6 = None
        self.assertEqual(var6, serialize_and_deserialize(serializer, var6))

    def test_schema(self):
        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.primitive_type.name)
        assert serializer
        self.assertTrue(serializer.stable())
        self.assertTrue(serializer.available())
        self.assertTrue('serialzy' in serializer.meta())
        self.assertTrue(len(serializer.requirements()) == 0)

        schema = serializer.schema(int)
        self.assertEqual(StandardDataFormats.primitive_type.name, schema.data_format)
        self.assertEqual('serialzy_python_type_reference', schema.schema_format)
        self.assertEqual('{"module": "builtins", "name": "int"}', schema.schema_content)
        self.assertTrue('serialzy' in schema.meta)

        schema = serializer.schema(type(None))
        self.assertEqual('{"module": "builtins", "name": "NoneType"}', schema.schema_content)

    def test_resolve(self):
        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.primitive_type.name)
        assert serializer
        typ = serializer.resolve(Schema(
            StandardDataFormats.primitive_type.name, 'serialzy_python_type_reference',
            '{"module": "builtins", "name": "str"}'
        ))
        self.assertEqual(str, typ)

        typ = serializer.resolve(Schema(
            StandardDataFormats.primitive_type.name, 'serialzy_python_type_reference',
            '{"module": "builtins", "name": "NoneType"}'
        ))
        self.assertEqual(type(None), typ)

        with self.assertRaisesRegex(TypeError, "Invalid data format*"):
            serializer.resolve(
                Schema(
                    StandardDataFormats.proto.name,
                    'serialzy_python_type_reference',
                    "content"
                )
            )
        with self.assertRaisesRegex(ValueError, "Invalid schema format*"):
            serializer.resolve(
                Schema(
                    StandardDataFormats.primitive_type.name,
                    StandardSchemaFormats.pickled_type.name,
                    "content"
                )
            )

        with self.assertRaises(JSONDecodeError):
            serializer.resolve(
                Schema(
                    StandardDataFormats.primitive_type.name,
                    'serialzy_python_type_reference',
                    "invalid content"
                )
            )

    def test_invalid_types(self):
        serializer = self.registry.find_serializer_by_type(int)
        assert serializer

        with self.assertRaisesRegex(TypeError, 'Invalid object type*'):
            with tempfile.TemporaryFile() as file:
                serializer.serialize([1, 1, 1], file)

        with tempfile.TemporaryFile() as file:
            serializer.serialize(1, file)
            file.flush()
            file.seek(0)

            with self.assertRaisesRegex(TypeError, 'Cannot deserialize data with schema type*'):
                serializer.deserialize(file, List[int])
