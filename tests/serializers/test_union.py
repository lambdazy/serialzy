import tempfile
from dataclasses import dataclass
from typing import Optional, Union
from unittest import TestCase

from pure_protobuf.dataclasses_ import message, field
from pure_protobuf.types import int32

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

        typ = Union[str, B]
        to_remove = self.registry.find_serializer_by_type(B)
        self.registry.unregister_serializer(to_remove)

        serializer = self.registry.find_serializer_by_type(typ)
        self.assertIsNone(serializer)

    def test_deserialize_with_type(self):
        @message
        @dataclass
        class TestMessage:
            a: int32 = field(1, default=0)

        @message
        @dataclass
        class TestMessage2:
            a: int32 = field(1, default=0)
            b: int32 = field(2, default=1)

        typ = Optional[TestMessage]
        serializer = self.registry.find_serializer_by_type(typ)
        # noinspection DuplicatedCode
        with tempfile.TemporaryFile() as file:
            obj = TestMessage(5)
            serializer.serialize(obj, file)
            file.flush()
            file.seek(0)
            deserialized = serializer.deserialize(file, TestMessage2)

        self.assertTrue(isinstance(obj, TestMessage))
        self.assertTrue(isinstance(deserialized, TestMessage2))

        self.assertEqual(obj.a, deserialized.a)
        self.assertEqual(1, deserialized.b)

        # removing proto serializer
        to_remove = self.registry.find_serializer_by_type(TestMessage)
        self.registry.unregister_serializer(to_remove)
        # removing cloudpickle serializer
        to_remove = self.registry.find_serializer_by_type(TestMessage)
        self.registry.unregister_serializer(to_remove)

        with tempfile.TemporaryFile() as file:
            obj = TestMessage(5)
            with self.assertRaisesRegex(ValueError, "Cannot find serializer for type*"):
                serializer.serialize(obj, file)

            file.flush()
            file.seek(0)

            with self.assertRaisesRegex(ValueError, "Cannot find serializer for type*"):
                serializer.deserialize(file, TestMessage2)
