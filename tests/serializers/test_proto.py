from dataclasses import dataclass
from pickle import UnpicklingError
from unittest import TestCase

from pure_protobuf.dataclasses_ import field, message
from pure_protobuf.types import int32

from serialzy.api import StandardDataFormats, StandardSchemaFormats, Schema
from serialzy.registry import DefaultSerializerRegistry
from tests.serializers.utils import serialized_and_deserialized


# noinspection PyPackageRequirements


class ProtoSerializationTests(TestCase):
    def setUp(self):
        self.registry = DefaultSerializerRegistry()

    def test_proto_serialization(self):
        @message
        @dataclass
        class TestMessage:
            a: int32 = field(1, default=0)

        test_message = TestMessage(42)
        self.assertEqual(
            test_message.a, serialized_and_deserialized(self.registry, test_message).a
        )

        serializer = self.registry.find_serializer_by_type(type(test_message))
        self.assertTrue(serializer.stable())
        self.assertIn("pure-protobuf", serializer.meta())

    def test_schema(self):
        @message
        @dataclass
        class TestMessage:
            a: int32 = field(1, default=0)

        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.proto.name)
        schema = serializer.schema(TestMessage)

        self.assertEqual(StandardDataFormats.proto.name, schema.data_format)
        self.assertEqual(StandardSchemaFormats.pickled_type.name, schema.schema_format)
        self.assertTrue(len(schema.schema_content) > 0)
        self.assertTrue('pure-protobuf' in schema.meta)
        self.assertTrue('cloudpickle' in schema.meta)

    def test_resolve(self):
        @message
        @dataclass
        class TestMessage:
            a: int32 = field(1, default=0)

        serializer = self.registry.find_serializer_by_data_format(StandardDataFormats.proto.name)
        schema = serializer.schema(TestMessage)

        typ = serializer.resolve(schema)
        self.assertEqual(TestMessage.__module__, typ.__module__)
        self.assertEqual(TestMessage.__name__, typ.__name__)

        with self.assertRaisesRegex(ValueError, "Invalid data format*"):
            serializer.resolve(
                Schema(
                    StandardDataFormats.primitive_type.name,
                    StandardSchemaFormats.pickled_type.name,
                    schema.schema_content,
                    {'cloudpickle': '0.0.0', 'pure-protobuf': '0.0.0'}
                )
            )
        with self.assertRaisesRegex(ValueError, "Invalid schema format*"):
            serializer.resolve(
                Schema(
                    StandardDataFormats.proto.name,
                    StandardSchemaFormats.json_pickled_type.name,
                    schema.schema_content,
                    {'cloudpickle': '0.0.0', 'pure-protobuf': '0.0.0'}
                )
            )

        with self.assertRaises(UnpicklingError):
            serializer.resolve(
                Schema(StandardDataFormats.proto.name, StandardSchemaFormats.pickled_type.name, 'data',
                       {'cloudpickle': '0.0.0', 'pure-protobuf': '0.0.0'}))

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema(StandardDataFormats.proto.name, StandardSchemaFormats.pickled_type.name, schema.schema_content,
                       {'cloudpickle': '0.0.0', 'pure-protobuf': '10000.0.0'}))
            self.assertRegex(cm.output[0], 'WARNING:serialzy.serializers.proto:Installed version of pure-protobuf*')

        with self.assertLogs() as cm:
            serializer.resolve(
                Schema(StandardDataFormats.proto.name, StandardSchemaFormats.pickled_type.name, schema.schema_content,
                       {'cloudpickle': '0.0.0'}))
            self.assertRegex(cm.output[0], 'WARNING:serialzy.serializers.proto:No pure-protobuf version in meta*')
