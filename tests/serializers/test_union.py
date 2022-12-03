import tempfile
from typing import Optional, Union
from unittest import TestCase

from serialzy.api import Schema
from serialzy.registry import DefaultSerializerRegistry
from tests.serializers.utils import serialize_and_deserialize


class UnionSerializationTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_optional(self):
        typ = Optional[str]
        obj = "str"
        serializer = self.registry.find_serializer_by_type(typ)

        deserialized = serialize_and_deserialize(serializer, obj)
        self.assertEqual(obj, deserialized)

        # serialize by primitive and deserialize by union
        primitive_serializer = self.registry.find_serializer_by_type(type(obj))
        with tempfile.TemporaryFile() as file:
            primitive_serializer.serialize(obj, file)
            file.flush()
            file.seek(0)
            deserialized = serializer.deserialize(file)
        self.assertEqual(obj, deserialized)

        self.assertTrue(serializer.stable())
        self.assertEqual("serialzy_union", serializer.data_format())
        self.assertTrue("serialzy" in serializer.meta())

    def test_optional_schema(self):
        typ = Optional[str]
        serializer = self.registry.find_serializer_by_type(typ)
        schema = serializer.schema(typ)

        self.assertEqual("serialzy_union_schema", schema.schema_format)
        self.assertEqual("serialzy_union", schema.data_format)
        self.assertTrue("serialzy" in schema.meta)

    def test_optional_resolve(self):
        typ = Optional[str]
        serializer = self.registry.find_serializer_by_type(typ)

        schema = serializer.schema(typ)
        resolved = serializer.resolve(schema)
        self.assertEqual(typ, resolved)

        with self.assertRaisesRegex(ValueError, "Cannot find serializer for data format*"):
            serializer.resolve(
                Schema(
                    'invalid format',
                    'serialzy_union_schema',
                    schema.schema_content,
                    {'serialzy': '0.0.0'}
                )
            )

        with self.assertRaisesRegex(ValueError, "Invalid schema format*"):
            serializer.resolve(
                Schema(
                    'serialzy_union',
                    'invalid schema',
                    schema.schema_content,
                    {'serialzy': '0.0.0'}
                )
            )

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema('serialzy_union', 'serialzy_union_schema', schema.schema_content,
                       {'serialzy': '10000.0.0'}))
            self.assertRegex(cm.output[0], 'WARNING:serialzy.serializers.union_base:Installed version of serialzy*')

        with self.assertLogs() as cm:
            serializer.resolve(Schema('serialzy_union', 'serialzy_union_schema', schema.schema_content, {}))
            self.assertRegex(cm.output[0], 'WARNING:serialzy.serializers.union_base:No serialzy version in meta*')

    def test_stable_unstable_union(self):
        class B:
            def __init__(self, x: int):
                self.x = x

        typ = Union[str, B]
        serializer = self.registry.find_serializer_by_type(typ)
        self.assertEqual("serialzy_union", serializer.data_format())
        self.assertTrue("serialzy" in serializer.meta())
        self.assertFalse(serializer.stable())

        typ = Union[str, int, type(None)]
        serializer = self.registry.find_serializer_by_type(typ)
        self.assertEqual("serialzy_union", serializer.data_format())
        self.assertTrue("serialzy" in serializer.meta())
        self.assertTrue(serializer.stable())
